from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AI Orchestration Service"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # ── API ──────────────────────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"

    # ── Transcription ────────────────────────────────────────────────────────
    # "faster_whisper" — local, no API key needed (default)
    # "openai_whisper" — calls OpenAI API, requires OPENAI_API_KEY
    TRANSCRIPTION_PROVIDER: str = "faster_whisper"
    OPENAI_WHISPER_MODEL: str = "whisper-1"

    # ── Faster-Whisper (local transcription) ─────────────────────────────────
    # Model sizes: tiny | base | small | medium | large-v2 | large-v3
    FASTER_WHISPER_MODEL: str = "small"
    FASTER_WHISPER_DEVICE: str = "cpu"        # cpu | cuda
    FASTER_WHISPER_COMPUTE_TYPE: str = "int8" # int8 (CPU) | float16 (GPU)
    FASTER_WHISPER_LANGUAGE: str | None = "en"
    FASTER_WHISPER_INITIAL_PROMPT: str | None = (
        "Transfer, send money, naira, balance, payment, bill, airtime, "
        "account, deposit, withdraw, transaction, recipient, bank."
    )
    FASTER_WHISPER_VAD_FILTER: bool = True

    # ── Voice Processing ─────────────────────────────────────────────────────
    MAX_AUDIO_FILE_SIZE_MB: int = 25

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173"

    # ── Database ─────────────────────────────────────────────────────────────
    # Must use asyncpg driver: postgresql+asyncpg://user:pass@host:port/dbname
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wallet-ledger-db"

    # ── Banking Backend (NestJS) ─────────────────────────────────────────────
    BANKING_BACKEND_URL: str = "http://localhost:3000"
    BANKING_BACKEND_TIMEOUT_SECONDS: int = 30

    # ── Active model ─────────────────────────────────────────────────────────
    # MODEL_PROVIDER controls which provider's API key is used.
    # MODEL_NAME is the full LiteLLM model string for that provider.
    #
    # To switch providers, change both values — nothing else:
    #   openai    / gpt-4o-mini
    #   anthropic / anthropic/claude-3-5-haiku-20241022
    #   gemini    / gemini/gemini-2.5-flash
    #   groq      / groq/llama-3.1-8b-instant
    #   ollama    / ollama/llama3.2   (no API key required)
    MODEL_PROVIDER: str = "openai"
    MODEL_NAME: str = "gpt-4o-mini"

    # ── Provider API keys ─────────────────────────────────────────────────────
    # Add the key for whichever provider you are using.
    # The system automatically selects the right key based on MODEL_PROVIDER.
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    # ── Agent behaviour ───────────────────────────────────────────────────────
    # Max conversation turns before Runner raises MaxTurnsExceeded.
    AGENTS_MAX_TURNS: int = 10
    # Enable OpenAI Agents tracing dashboard (requires Agents API plan).
    AGENTS_TRACING_ENABLED: bool = False


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached Settings instance.

    @lru_cache means Settings() runs exactly once — on the first call.
    Every subsequent call returns the same object from memory, so the .env
    file is never re-read for the lifetime of the process.

    In tests override with:
        app.dependency_overrides[get_settings] = lambda: Settings(OPENAI_API_KEY="test")
    """
    return Settings()
