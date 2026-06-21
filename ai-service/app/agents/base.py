"""
Agent infrastructure: SDK configuration, shared context, prompt loading.

This module is imported by every agent file. It must not import from any
agent or specialist module to avoid circular imports.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agents import set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.integrations.banking.client import BankingClient

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


# ── Shared request context ────────────────────────────────────────────────────

@dataclass
class RequestContext:
    """
    Per-request state threaded through every agent and tool call.

    The OpenAI Agents SDK passes this object as `ctx.context` inside any
    tool decorated with @function_tool that declares RunContextWrapper[RequestContext]
    as its first parameter.
    """
    user_id: str                        # JWT `sub` claim — authenticated user
    user: dict[str, Any]                # full user object from /api/auth/me
    bearer_token: str                   # raw JWT forwarded to banking backend
    banking_client: BankingClient       # pre-built HTTP client for this request
    db_session: AsyncSession | None = field(default=None)  # per-request DB session


# ── Prompt loading ────────────────────────────────────────────────────────────

def load_prompt(*path_parts: str) -> str:
    """Load a markdown prompt file relative to app/prompts/."""
    return _PROMPTS_DIR.joinpath(*path_parts).read_text(encoding="utf-8")


def build_agent_instructions(*prompt_paths: tuple[str, ...]) -> str:
    """Load and concatenate multiple prompt files separated by a divider.

    Each argument is a tuple of path parts passed to load_prompt().
    """
    return "\n\n---\n\n".join(load_prompt(*parts) for parts in prompt_paths)


# ── LiteLLM model factory ─────────────────────────────────────────────────────

# Maps MODEL_PROVIDER value → the Settings attribute that holds its API key.
_PROVIDER_KEY_MAP: dict[str, str] = {
    "openai":    "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini":    "GEMINI_API_KEY",
    "groq":      "GROQ_API_KEY",
    "ollama":    "",  # local — no API key required
}


def get_litellm_model() -> LitellmModel:
    """
    Return a LitellmModel configured from MODEL_PROVIDER + MODEL_NAME in settings.

    All agents call this function — the active model is driven entirely by env:

        MODEL_PROVIDER=openai     MODEL_NAME=gpt-4o-mini
        MODEL_PROVIDER=anthropic  MODEL_NAME=anthropic/claude-3-5-haiku-20241022
        MODEL_PROVIDER=gemini     MODEL_NAME=gemini/gemini-2.5-flash
        MODEL_PROVIDER=groq       MODEL_NAME=groq/llama-3.1-8b-instant
        MODEL_PROVIDER=ollama     MODEL_NAME=ollama/llama3.2

    The API key is looked up via MODEL_PROVIDER → {PROVIDER}_API_KEY in settings.
    Passing it explicitly to LitellmModel ensures the correct key is always used
    even when multiple provider keys are present in the environment.
    """
    settings = get_settings()
    provider = settings.MODEL_PROVIDER.lower()

    key_attr = _PROVIDER_KEY_MAP.get(provider, "")
    api_key: str | None = getattr(settings, key_attr, None) if key_attr else None

    if api_key is None and provider != "ollama":
        logger.warning(
            "agents.model.missing_api_key",
            provider=provider,
            expected_env=f"{provider.upper()}_API_KEY",
            hint="Set the API key in .env or switch MODEL_PROVIDER to a configured provider",
        )

    return LitellmModel(model=settings.MODEL_NAME, api_key=api_key or None)


# ── SDK setup ─────────────────────────────────────────────────────────────────

def setup_agents(settings: Settings | None = None) -> None:
    """Configure the OpenAI Agents SDK. Called once from main.py lifespan."""
    if settings is None:
        settings = get_settings()

    set_tracing_disabled(not settings.AGENTS_TRACING_ENABLED)

    logger.info(
        "agents.setup.done",
        provider=settings.MODEL_PROVIDER,
        model=settings.MODEL_NAME,
        tracing=settings.AGENTS_TRACING_ENABLED,
    )


# ── JWT decoding ──────────────────────────────────────────────────────────────

def extract_user_id_from_token(token: str) -> str:
    """Decode JWT payload without signature verification and return `sub`.

    The AI service never validates JWTs — the banking backend does that on
    every downstream call. We only decode to extract user_id for API paths.
    Returns "anonymous" if the token is missing or malformed.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return "anonymous"
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return str(payload.get("sub", "anonymous"))
    except Exception:
        return "anonymous"


# ── Banking client factory ────────────────────────────────────────────────────

def build_banking_client(bearer_token: str) -> BankingClient:
    """Create a per-request BankingClient with the user's JWT embedded."""
    settings = get_settings()
    return BankingClient(
        base_url=settings.BANKING_BACKEND_URL,
        timeout=settings.BANKING_BACKEND_TIMEOUT_SECONDS,
        bearer_token=bearer_token,
    )
