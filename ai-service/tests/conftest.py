"""
Global pytest fixtures and environment bootstrap.

IMPORTANT: os.environ must be set BEFORE any app module is imported.
With @lru_cache on get_settings(), the Settings object is created on the
first call and cached forever. Setting env vars after that first call has
no effect. So we set them here, at the very top, before any app import.

To override settings in a specific test:
    from app.core.config import get_settings
    app.dependency_overrides[get_settings] = lambda: Settings(DEBUG=True, ...)
"""
import os

# Use local faster-whisper in tests so no OpenAI key is needed
os.environ.setdefault("TRANSCRIPTION_PROVIDER", "faster_whisper")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client — suitable for most endpoint tests."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
async def async_client():
    """Async test client for tests that need to await responses."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
