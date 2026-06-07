import io

from openai import APIConnectionError, APIStatusError, AsyncOpenAI

from app.core.config import get_settings
from app.core.exceptions import OpenAIAPIError
from app.core.logging import get_logger

from .base import TranscriptionProvider

logger = get_logger(__name__)


class OpenAIWhisperProvider(TranscriptionProvider):
    """Calls OpenAI Whisper (whisper-1) for audio transcription."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=get_settings().OPENAI_API_KEY)

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        settings = get_settings()
        try:
            logger.debug(
                "whisper.transcribe.start",
                filename=filename,
                model=settings.OPENAI_WHISPER_MODEL,
                size_bytes=len(audio_bytes),
            )

            # The OpenAI SDK accepts a (name, file_obj, mime_type) tuple
            audio_file = (filename, io.BytesIO(audio_bytes), content_type)

            response = await self._client.audio.transcriptions.create(
                model=settings.OPENAI_WHISPER_MODEL,
                file=audio_file,  # type: ignore[arg-type]
            )

            logger.debug("whisper.transcribe.done", filename=filename)
            return response.text

        except APIStatusError as exc:
            logger.error(
                "whisper.api_error",
                filename=filename,
                status_code=exc.status_code,
                message=exc.message,
            )
            raise OpenAIAPIError(
                f"OpenAI returned HTTP {exc.status_code}: {exc.message}"
            ) from exc

        except APIConnectionError as exc:
            logger.error("whisper.connection_error", filename=filename, error=str(exc))
            raise OpenAIAPIError("Could not reach the OpenAI API.") from exc

        except Exception as exc:
            logger.exception("whisper.unexpected_error", filename=filename)
            raise OpenAIAPIError(f"Unexpected error during transcription: {exc}") from exc
