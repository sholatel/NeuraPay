from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import FileSizeExceededError, UnsupportedFileTypeError
from app.core.logging import get_logger
from app.schemas.common import SuccessResponse

from .providers.base import TranscriptionProvider
from .providers.whisper import OpenAIWhisperProvider

logger = get_logger(__name__)

# Formats supported by Whisper — kept in sync with OpenAI's documentation
_SUPPORTED_EXTENSIONS = frozenset(
    {"mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg", "flac"}
)


class VoiceService:
    """
    Orchestrates audio validation and transcription.

    VoiceController (route)
        → VoiceService           ← you are here
            → TranscriptionProvider (abstract)
                → OpenAIWhisperProvider (concrete)
    """

    def __init__(self, provider: TranscriptionProvider | None = None) -> None:
        self._provider: TranscriptionProvider = provider or OpenAIWhisperProvider()

    async def transcribe(self, file: UploadFile) -> SuccessResponse:
        self._validate_extension(file)

        audio_bytes = await file.read()
        self._validate_size(audio_bytes)

        logger.info(
            "voice.transcribe.start",
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=len(audio_bytes),
        )

        transcript = await self._provider.transcribe(
            audio_bytes=audio_bytes,
            filename=file.filename or "audio",
            content_type=file.content_type or "application/octet-stream",
        )

        logger.info("voice.transcribe.success", filename=file.filename)

        return SuccessResponse(
            message="Transcription successful",
            data={"transcript": transcript},
        )

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        """Transcribe pre-read audio bytes and return the raw transcript string.

        Used by endpoints that have already read and validated the file
        (e.g. process-voice-operation) so the file isn't read twice.
        """
        logger.info(
            "voice.transcribe.start",
            filename=filename,
            content_type=content_type,
            size_bytes=len(audio_bytes),
        )

        transcript = await self._provider.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            content_type=content_type,
        )

        logger.info("voice.transcribe.success", filename=filename)
        return transcript

    # ── Validation helpers ────────────────────────────────────────────────────

    def _validate_extension(self, file: UploadFile) -> None:
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if not ext or ext not in _SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                message=f"Unsupported file type: {'.' + ext if ext else '(no extension)'}",
                detail=f"Supported formats: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}",
            )

    def _validate_size(self, audio_bytes: bytes) -> None:
        settings = get_settings()
        max_bytes = settings.MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024
        if len(audio_bytes) > max_bytes:
            raise FileSizeExceededError(
                message=f"File exceeds the {settings.MAX_AUDIO_FILE_SIZE_MB} MB limit "
                        f"({len(audio_bytes) / (1024 * 1024):.1f} MB received)."
            )
