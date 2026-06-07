class AIServiceError(Exception):
    """Base exception for all AI Orchestration Service errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class UnsupportedFileTypeError(AIServiceError):
    """Raised when the uploaded audio file has an unsupported format."""


class FileSizeExceededError(AIServiceError):
    """Raised when the uploaded file exceeds the configured size limit."""


class TranscriptionError(AIServiceError):
    """Raised when audio transcription fails for a non-OpenAI reason."""


class OpenAIAPIError(AIServiceError):
    """Raised when the OpenAI API returns an error or is unreachable."""


class BankingBackendError(AIServiceError):
    """Raised when the NestJS banking backend returns an error or is unreachable."""


class IntentParsingError(AIServiceError):
    """Raised when the LLM fails to parse intent from a transcript."""


class AgentError(AIServiceError):
    """Raised when the agent orchestrator encounters an unrecoverable error."""
