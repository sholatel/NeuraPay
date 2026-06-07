import asyncio
import os
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import get_settings
from app.core.exceptions import TranscriptionError
from app.core.logging import get_logger

from .base import TranscriptionProvider

logger = get_logger(__name__)

# Module-level singleton — model is loaded once and reused across requests.
# First call downloads weights from HuggingFace (one-time, then cached).
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        settings = get_settings()
        logger.info(
            "faster_whisper.model.loading",
            model=settings.FASTER_WHISPER_MODEL,
            device=settings.FASTER_WHISPER_DEVICE,
            compute_type=settings.FASTER_WHISPER_COMPUTE_TYPE,
        )
        _model = WhisperModel(
            settings.FASTER_WHISPER_MODEL,
            device=settings.FASTER_WHISPER_DEVICE,
            compute_type=settings.FASTER_WHISPER_COMPUTE_TYPE,
        )
        logger.info("faster_whisper.model.ready", model=settings.FASTER_WHISPER_MODEL)
    return _model


class FasterWhisperProvider(TranscriptionProvider):
    """
    Local Whisper transcription via faster-whisper (CTranslate2 backend).
    No API key or internet connection required after the first model download.
    """

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        # Run the synchronous faster-whisper call in a thread so the
        # async event loop is never blocked during inference.
        return await asyncio.to_thread(self._transcribe_sync, audio_bytes, filename)

    def _transcribe_sync(self, audio_bytes: bytes, filename: str) -> str:
        suffix = Path(filename).suffix or ".tmp"
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            settings = get_settings()
            model = _get_model()

            segments_iter, info = model.transcribe(
                tmp_path,
                beam_size=5,
                language=settings.FASTER_WHISPER_LANGUAGE,
                initial_prompt=settings.FASTER_WHISPER_INITIAL_PROMPT,
                vad_filter=settings.FASTER_WHISPER_VAD_FILTER,
                vad_parameters={
                    # Lower threshold = more sensitive to quiet/short speech.
                    # Default is 0.5 — browser mic recordings often fall below
                    # that because they're shorter and less loud than studio audio.
                    "threshold": 0.3,
                    # Keep speech bursts as short as 100 ms (default is 250 ms).
                    # Important for short commands like "Check balance."
                    "min_speech_duration_ms": 100,
                    # How long a silence must be before splitting a segment.
                    "min_silence_duration_ms": 300,
                },
                # Whisper's built-in "no speech" detector scores each segment
                # 0–1. Default cutoff is 0.6 — anything above that is dropped.
                # Browser mic audio often scores high (quiet/compressed), so we
                # raise the bar: only drop a segment if Whisper is 95%+ sure
                # there is no speech at all.
                no_speech_threshold=0.95,
                # If the model's average log-probability is below this value
                # it considers the result unreliable and retries with higher
                # temperature. Default is -1.0. Browser audio often scores
                # around -1.2, so we loosen this to avoid discarding results.
                log_prob_threshold=-2.0,
            )

            # Materialise the generator into a list immediately.
            # 'segments_iter' is lazy — if we consume it inside a join() and it
            # yields nothing, we'd silently return "". A list gives us a count
            # so we can log and warn when VAD strips everything.
            segments = list(segments_iter)
            transcript = " ".join(seg.text.strip() for seg in segments).strip()

            logger.info(
                "faster_whisper.transcribe.done",
                filename=filename,
                audio_size_bytes=len(audio_bytes),
                language=info.language,
                language_probability=round(info.language_probability, 2),
                segment_count=len(segments),
                transcript_chars=len(transcript),
            )

            if not transcript:
                logger.warning(
                    "faster_whisper.transcribe.empty",
                    filename=filename,
                    audio_size_bytes=len(audio_bytes),
                    segment_count=len(segments),
                    language_probability=round(info.language_probability, 2),
                    hint=(
                        "VAD filtered all segments. Audio may be too short, too quiet, "
                        "or the language probability is low. Try lowering "
                        "FASTER_WHISPER_VAD_FILTER=false to confirm."
                    ),
                )

            return transcript

        except Exception as exc:
            logger.exception("faster_whisper.transcribe.error", filename=filename)
            raise TranscriptionError(f"Local transcription failed: {exc}") from exc

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
