"""
POST /api/v1/operations/process-voice-operation

Full voice-to-action pipeline:
  1. Extract user identity from Bearer token (no signature verification — the
     banking backend validates the token on every downstream call).
  2. Transcribe audio with faster-whisper (or OpenAI Whisper).
  3. Run transcript through the BankingAgent (triage → handoff → specialist tool).
  4. Return the agent's final natural-language response.
"""

from typing import Annotated

from agents import MaxTurnsExceeded, ModelBehaviorError, Runner
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile

from app.agents.banking_agent import banking_agent
from app.agents.base import RequestContext, build_banking_client, extract_user_id_from_token
from app.core.config import Settings, get_settings
from app.core.exceptions import FileSizeExceededError, UnsupportedFileTypeError
from app.core.logging import get_logger
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


@router.post(
    "/process-voice-operation",
    response_model=SuccessResponse,
    summary="Process a voice command end-to-end",
    description=(
        "Accepts an audio recording, transcribes it, routes it through the BankingAgent "
        "triage system, and executes the appropriate banking operation via the NestJS backend. "
        "Requires a valid JWT in the Authorization header — the token is forwarded to all "
        "downstream banking API calls unchanged."
    ),
)
async def process_voice_operation(
    file: Annotated[UploadFile, File(description="Audio recording (webm, ogg, mp4, wav)")],
    settings: Annotated[Settings, Depends(get_settings)],
    voice_service: Annotated[VoiceService, Depends(get_voice_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> SuccessResponse:
    """
    Voice-to-banking-action pipeline.

    Authorization header: `Bearer <jwt>`
    The JWT is not validated here — it is forwarded to the NestJS banking backend
    on every API call. If the token is invalid or expired, the banking backend
    returns a 401 and the agent surfaces a human-friendly session-expired message.

    The user_id is extracted from the JWT payload (sub claim) so tools can
    construct correct API paths like /api/wallet/:userId/balance.
    """
    # ── 1. Extract identity from Bearer token ─────────────────────────────────
    bearer_token = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer_token = authorization[7:].strip()

    user_id = extract_user_id_from_token(bearer_token) if bearer_token else "anonymous"

    if user_id == "anonymous":
        logger.warning("operations.no_auth", hint="Request missing valid Authorization header")

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

    # ── 4. Build per-request context and run the agent ────────────────────────
    context = RequestContext(
        user_id=user_id,
        bearer_token=bearer_token,
        banking_client=build_banking_client(bearer_token),
    )

    try:
        result = await Runner.run(
            banking_agent,
            input=transcript,
            context=context,
            max_turns=settings.AGENTS_MAX_TURNS,
        )
    except MaxTurnsExceeded:
        logger.warning("operations.agent.max_turns_exceeded", user_id=user_id)
        raise HTTPException(
            status_code=422,
            detail="The agent could not complete the operation within the allowed number of turns. Please try a simpler command.",
        )
    except ModelBehaviorError as exc:
        logger.error("operations.agent.model_error", error=str(exc), user_id=user_id)
        raise HTTPException(status_code=502, detail="The AI model returned an unexpected response. Please try again.")

    # Collect which agents and tools were involved (for observability)
    last_agent_name = result.last_agent.name if result.last_agent else "Banking Agent"

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
