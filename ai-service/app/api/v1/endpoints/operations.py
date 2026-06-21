"""
POST /api/v1/operations/process-voice-operation

Full voice-to-action pipeline:
  1. Validate the Bearer token via NestJS GET /api/auth/me (401 if invalid).
  2. Transcribe audio with faster-whisper (or OpenAI Whisper).
  3. Check DB for any active pending actions for this user; prepend context if found.
  4. Run the transcript (+ pending context) through the BankingAgent.
  5. Commit any DB changes (pending action creates/updates) made during the run.
  6. Return the agent's final natural-language response.
"""

from typing import Annotated

import litellm
from agents import MaxTurnsExceeded, ModelBehaviorError, Runner
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile

from app.agents.banking_agent import banking_agent
from app.agents.base import RequestContext, build_banking_client, extract_user_id_from_token
from app.core.config import Settings, get_settings
from app.core.exceptions import BankingBackendError, FileSizeExceededError, UnsupportedFileTypeError
from app.core.logging import get_logger
from app.db.models.pending_action import PendingAction
from app.db.session import AsyncSessionLocal
from app.repositories import pending_action as pending_action_repo
from app.schemas.common import SuccessResponse
from app.services.voice.providers.faster_whisper_provider import FasterWhisperProvider
from app.services.voice.providers.whisper import OpenAIWhisperProvider
from app.services.voice.service import VoiceService

router = APIRouter()
logger = get_logger(__name__)

_SUPPORTED_AUDIO_TYPES = frozenset({
    "audio/webm",
    "audio/webm;codecs=opus",
    "audio/ogg",
    "audio/ogg;codecs=opus",
    "audio/mp4",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
})


def _build_voice_service(settings: Settings) -> VoiceService:
    if settings.TRANSCRIPTION_PROVIDER == "openai_whisper":
        return VoiceService(provider=OpenAIWhisperProvider())
    return VoiceService(provider=FasterWhisperProvider())


def get_voice_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> VoiceService:
    return _build_voice_service(settings)


def _format_pending_context(actions: list[PendingAction], transcript: str) -> str:
    """Wrap transcript with pending-action context so the agent can continue a flow."""
    lines = [
        "[PENDING ACTIONS CONTEXT]",
        "The user has the following active pending action(s) from a previous voice request.",
        "If this message is a continuation of one of these flows (e.g. a confirmation,",
        "cancellation, or missing detail), handle it accordingly and update the action status.",
        "",
    ]
    for action in actions:
        lines.append(f"Action: {action.action_name}  |  ID: {action.id}")
        if action.meta:
            for key, value in action.meta.items():
                lines.append(f"  {key}: {value}")
        if action.expired_at:
            lines.append(f"  Expires: {action.expired_at.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("")
    lines.append("[END PENDING ACTIONS CONTEXT]")
    lines.append("")
    lines.append(f"User message: {transcript}")
    return "\n".join(lines)


@router.post(
    "/process-voice-operation",
    response_model=SuccessResponse,
    summary="Process a voice command end-to-end",
    description=(
        "Accepts an audio recording, validates the caller's JWT against the banking backend, "
        "transcribes the audio, checks for any pending multi-step flows, routes through the "
        "BankingAgent triage system, and executes the appropriate banking operation. "
        "Requires a valid JWT in the Authorization header."
    ),
)
async def process_voice_operation(
    file: Annotated[UploadFile, File(description="Audio recording (webm, ogg, mp4, wav)")],
    settings: Annotated[Settings, Depends(get_settings)],
    voice_service: Annotated[VoiceService, Depends(get_voice_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> SuccessResponse:
    # ── 1. Require and validate Authorization header ───────────────────────────
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required.")

    bearer_token = authorization[7:].strip()
    banking_client = build_banking_client(bearer_token)

    try:
        auth_result = await banking_client.verify_token()
    except BankingBackendError:
        raise HTTPException(status_code=401, detail="Invalid or expired token. Please log in again.")

    user: dict = auth_result.get("user", {})
    user_id: str = user.get("id") or extract_user_id_from_token(bearer_token)

    logger.info("operations.auth.ok", user_id=user_id, account_number=user.get("accountNumber"))

    # ── 2. Validate and read audio ────────────────────────────────────────────
    full_content_type = file.content_type or ""
    base_content_type = full_content_type.split(";")[0].strip()

    if full_content_type not in _SUPPORTED_AUDIO_TYPES and base_content_type not in _SUPPORTED_AUDIO_TYPES:
        raise UnsupportedFileTypeError(
            f"Unsupported audio type: {full_content_type or '(none)'}",
            detail=f"Supported types: {', '.join(sorted(_SUPPORTED_AUDIO_TYPES))}",
        )

    audio_bytes = await file.read()
    max_bytes = settings.MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise FileSizeExceededError(
            f"File exceeds the {settings.MAX_AUDIO_FILE_SIZE_MB} MB limit.",
            detail=f"Received {len(audio_bytes):,} bytes",
        )

    logger.info(
        "operations.start",
        filename=file.filename,
        content_type=full_content_type,
        size_bytes=len(audio_bytes),
        user_id=user_id,
    )

    # ── 3. Transcribe ─────────────────────────────────────────────────────────
    transcript = await voice_service.transcribe_bytes(
        audio_bytes=audio_bytes,
        filename=file.filename or "recording.webm",
        content_type=full_content_type,
    )

    if not transcript.strip():
        return SuccessResponse(
            message="Voice operation processed",
            data={
                "transcript": "",
                "response": (
                    "I didn't catch that — the recording appears to be silent or too short. "
                    "Please speak clearly for at least 2–3 seconds and try again."
                ),
                "agent": None,
            },
        )

    logger.info("operations.transcription.done", transcript_chars=len(transcript), user_id=user_id)

    # ── 4. DB session: check pending actions, run agent, commit ───────────────
    async with AsyncSessionLocal() as session:
        try:
            pending_actions = await pending_action_repo.get_active_for_user(session, user_id)
        except Exception as exc:
            logger.warning("operations.pending_actions.fetch_failed", error=str(exc), user_id=user_id)
            pending_actions = []

        agent_input = (
            _format_pending_context(pending_actions, transcript)
            if pending_actions
            else transcript
        )

        if pending_actions:
            logger.info(
                "operations.pending_actions.found",
                count=len(pending_actions),
                names=[a.action_name for a in pending_actions],
                user_id=user_id,
            )

        context = RequestContext(
            user_id=user_id,
            user=user,
            bearer_token=bearer_token,
            banking_client=banking_client,
            db_session=session,
        )

        try:
            result = await Runner.run(
                banking_agent,
                input=agent_input,
                context=context,
                max_turns=settings.AGENTS_MAX_TURNS,
            )
            await session.commit()
        except MaxTurnsExceeded:
            await session.rollback()
            logger.warning("operations.agent.max_turns_exceeded", user_id=user_id)
            raise HTTPException(
                status_code=422,
                detail="The agent could not complete the operation within the allowed number of turns. Please try a simpler command.",
            )
        except ModelBehaviorError as exc:
            await session.rollback()
            logger.error("operations.agent.model_error", error=str(exc), user_id=user_id)
            raise HTTPException(status_code=502, detail="The AI model returned an unexpected response. Please try again.")
        except litellm.RateLimitError as exc:
            await session.rollback()
            logger.warning("operations.agent.rate_limit", error=str(exc), user_id=user_id)
            raise HTTPException(
                status_code=429,
                detail="The AI model is rate-limited. You may have exceeded your daily quota. Please wait and try again later.",
            )
        except litellm.ServiceUnavailableError as exc:
            await session.rollback()
            logger.warning("operations.agent.service_unavailable", error=str(exc), user_id=user_id)
            raise HTTPException(
                status_code=503,
                detail="The AI model is temporarily unavailable due to high demand. Please try again in a few seconds.",
            )

    last_agent_name = result.last_agent.name if result.last_agent else "Banking_Agent"

    logger.info(
        "operations.done",
        agent=last_agent_name,
        output_chars=len(result.final_output or ""),
        user_id=user_id,
    )

    return SuccessResponse(
        message="Voice operation processed",
        data={
            "transcript": transcript,
            "response": result.final_output,
            "agent": last_agent_name,
        },
    )
