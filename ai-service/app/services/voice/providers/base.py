from abc import ABC, abstractmethod


class TranscriptionProvider(ABC):
    """
    Abstract contract for any speech-to-text backend.

    Swap implementations (Whisper, Google STT, AssemblyAI, …) without
    touching VoiceService or any route handler.
    """

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        """Return the transcribed text for the given audio payload."""
        ...
