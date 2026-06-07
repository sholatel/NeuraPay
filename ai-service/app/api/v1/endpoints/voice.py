from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import Settings, get_settings
from app.schemas.common import SuccessResponse
from app.services.voice.providers.base import TranscriptionProvider
from app.services.voice.service import VoiceService

router = APIRouter()


def _build_provider(settings: Settings) -> TranscriptionProvider:
    if settings.TRANSCRIPTION_PROVIDER == "openai_whisper":
        from app.services.voice.providers.whisper import OpenAIWhisperProvider
        return OpenAIWhisperProvider()
    from app.services.voice.providers.faster_whisper_provider import FasterWhisperProvider
    return FasterWhisperProvider()


def get_voice_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> VoiceService:
    return VoiceService(provider=_build_provider(settings))


@router.post(
    "/transcribe",
    response_model=SuccessResponse,
    summary="Transcribe audio to text",
    description=(
        "Upload an audio file (mp3, wav, m4a, webm, ogg, flac, …) "
        "and receive the transcription in the `data.transcript` field."
    ),
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    service: VoiceService = Depends(get_voice_service),
) -> SuccessResponse:
    return await service.transcribe(file)
