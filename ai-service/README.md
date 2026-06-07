# AI Orchestration Service

FastAPI-based AI layer for the wallet-ledger fintech platform. Handles voice processing, agent orchestration, and MCP tool integration. Communicates with the NestJS banking backend via HTTP — it never touches the banking database directly.

---

## System Boundaries

```
User (Voice/Chat)
       │
       ▼
┌─────────────────────────────┐
│   AI Orchestration Service  │  ← this repo (Python / FastAPI)
│                             │
│  Voice → Whisper → Intent   │
│  Agent Orchestration        │
│  MCP Tools                  │
│  Memory / Sessions          │
└────────────┬────────────────┘
             │ HTTP only
             ▼
┌─────────────────────────────┐
│   NestJS Banking Backend    │  ← source of truth
│                             │
│  Accounts / Wallets         │
│  Transactions / Transfers   │
│  Auth / KYC                 │
└─────────────────────────────┘
```

**The AI service NEVER:**
- Reads from or writes to the banking database
- Executes financial operations independently
- Holds long-term financial state

---

## Project Structure

```
ai-service/
├── app/
│   ├── api/            # FastAPI routers and endpoint handlers (controllers)
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── health.py       GET /health
│   │       │   └── voice.py        POST /api/v1/voice/transcribe
│   │       └── router.py
│   │
│   ├── core/           # Cross-cutting concerns (config, logging, exceptions)
│   │   ├── config.py           pydantic-settings Settings class
│   │   ├── logging.py          structlog setup + get_logger()
│   │   ├── exceptions.py       domain exception hierarchy
│   │   └── error_handlers.py   FastAPI exception → JSON response mapping
│   │
│   ├── config/         # Re-exports settings; future env-specific overrides
│   │
│   ├── services/       # Business logic — no FastAPI dependencies
│   │   └── voice/
│   │       ├── service.py          VoiceService (validates + orchestrates)
│   │       └── providers/
│   │           ├── base.py         TranscriptionProvider (abstract)
│   │           └── whisper.py      OpenAIWhisperProvider (concrete)
│   │
│   ├── schemas/        # Pydantic request/response models
│   │   ├── common.py           HealthResponse, ErrorResponse
│   │   └── voice.py            TranscribeResponse
│   │
│   ├── middleware/     # Starlette middleware
│   │   └── request_id.py       Correlation ID + request logging
│   │
│   ├── agents/         # [FUTURE] OpenAI Agents SDK agent definitions
│   ├── tools/          # [FUTURE] Agent tool wrappers (banking, external APIs)
│   ├── mcp/            # [FUTURE] MCP server configs and client wrappers
│   ├── models/         # [FUTURE] ORM models for local DB (audit log, sessions)
│   ├── memory/         # [FUTURE] Conversation memory / session stores
│   └── integrations/
│       └── banking/    # [FUTURE] HTTP client for NestJS backend
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   └── services/
│   │       └── test_voice_service.py
│   └── integration/
│       └── api/
│           └── test_voice_endpoint.py
│
├── main.py             # App factory + uvicorn entrypoint
├── pyproject.toml      # uv/hatchling project config
├── .env.example        # Environment variable template
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1 — Clone and enter the service directory

```bash
cd wallet-ledger-system/ai-service
```

### 2 — Install dependencies

```bash
uv sync
```

### 3 — Configure environment

```bash
cp .env.example .env
# Open .env and set OPENAI_API_KEY
```

### 4 — Run the server

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or directly:

```bash
uv run python main.py
```

The API is now available at `http://localhost:8000`.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | **Yes** | — | Your OpenAI API key |
| `ENVIRONMENT` | No | `development` | `development` / `staging` / `production` |
| `DEBUG` | No | `false` | Pretty-print logs, enable auto-reload |
| `LOG_LEVEL` | No | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `PORT` | No | `8000` | Uvicorn listen port |
| `OPENAI_WHISPER_MODEL` | No | `whisper-1` | Whisper model name |
| `MAX_AUDIO_FILE_SIZE_MB` | No | `25` | Max upload size (MB) |
| `BANKING_BACKEND_URL` | No | `http://localhost:3000` | NestJS service base URL |

---

## API Reference

### `GET /health`

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-06-02T22:00:00.000000+00:00"
}
```

### `POST /api/v1/voice/transcribe`

**Content-Type:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `file` | File | Audio file — mp3, wav, m4a, webm, ogg, flac |

**Success (200):**

```json
{
  "success": true,
  "transcript": "Send ₦10,000 to my brother"
}
```

**Error responses:**

| Status | Cause |
|---|---|
| `413` | File exceeds 25 MB |
| `415` | Unsupported file format |
| `422` | Missing `file` field |
| `502` | OpenAI API error |

---

## Call Flow

```
POST /api/v1/voice/transcribe
        │
        ▼
RequestIDMiddleware          ← attaches correlation ID, logs start/end
        │
        ▼
voice.py (endpoint)          ← calls VoiceService via Depends()
        │
        ▼
VoiceService.transcribe()    ← validates extension + size
        │
        ▼
OpenAIWhisperProvider        ← calls OpenAI API
        │
        ▼
TranscribeResponse           ← {"success": true, "transcript": "..."}
```

---

## Running Tests

```bash
# All tests
uv run pytest

# Unit tests only (no network, fast)
uv run pytest tests/unit

# Integration tests
uv run pytest tests/integration

# With coverage
uv run pytest --cov=app --cov-report=term-missing
```

---

## Local Development

```bash
# Install dev dependencies
uv sync --group dev

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type-check
uv run mypy app/

# Interactive docs
open http://localhost:8000/docs
```

---

## Adding New Features

### New voice provider (e.g. AssemblyAI)

1. Create `app/services/voice/providers/assemblyai.py` implementing `TranscriptionProvider`
2. Pass it as `provider=AssemblyAIProvider()` in the `get_voice_service` dependency in [voice.py](app/api/v1/endpoints/voice.py)

### New agent

1. Add the agent module in `app/agents/`
2. Add its tools in `app/tools/`
3. Wire a new endpoint in `app/api/v1/endpoints/`
4. Register the router in [app/api/v1/router.py](app/api/v1/router.py)

### Banking backend calls

All outbound calls to the NestJS backend must go through `app/integrations/banking/`. Never call `BANKING_BACKEND_URL` from a service or endpoint directly.
