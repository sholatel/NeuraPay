"""
Integration tests for the voice API endpoints.

These tests spin up the full FastAPI app via TestClient.
The OpenAI provider is mocked so no real API calls are made.
"""
import io

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape(client: TestClient) -> None:
    data = client.get("/health").json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_health_includes_request_id_header(client: TestClient) -> None:
    response = client.get("/health")
    assert "x-request-id" in response.headers


# ── Transcription — happy path ─────────────────────────────────────────────────

WHISPER_PATCH = "app.services.voice.providers.faster_whisper_provider.FasterWhisperProvider.transcribe"


@patch(WHISPER_PATCH, new_callable=AsyncMock)
def test_transcribe_mp3_returns_transcript(mock_transcribe: AsyncMock, client: TestClient) -> None:
    mock_transcribe.return_value = "Send ₦10,000 to my brother"

    response = client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("command.mp3", io.BytesIO(b"fake_audio"), "audio/mpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["transcript"] == "Send ₦10,000 to my brother"


@patch(WHISPER_PATCH, new_callable=AsyncMock)
def test_transcribe_wav_accepted(mock_transcribe: AsyncMock, client: TestClient) -> None:
    mock_transcribe.return_value = "Check my balance"
    response = client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("audio.wav", io.BytesIO(b"fake"), "audio/wav")},
    )
    assert response.status_code == 200


@patch(WHISPER_PATCH, new_callable=AsyncMock)
def test_transcribe_webm_accepted(mock_transcribe: AsyncMock, client: TestClient) -> None:
    mock_transcribe.return_value = "Pay electricity bill"
    response = client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("clip.webm", io.BytesIO(b"fake"), "audio/webm")},
    )
    assert response.status_code == 200


# ── Transcription — error cases ───────────────────────────────────────────────

def test_transcribe_unsupported_format_returns_415(client: TestClient) -> None:
    response = client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("doc.txt", io.BytesIO(b"text"), "text/plain")},
    )
    assert response.status_code == 415
    assert response.json()["success"] is False


def test_transcribe_missing_file_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/voice/transcribe")
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_transcribe_file_too_large_returns_413(client: TestClient) -> None:
    large_audio = b"x" * (26 * 1024 * 1024)
    response = client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("huge.mp3", io.BytesIO(large_audio), "audio/mpeg")},
    )
    assert response.status_code == 413
    assert response.json()["success"] is False


# ── Request ID propagation ─────────────────────────────────────────────────────

@patch(WHISPER_PATCH, new_callable=AsyncMock)
def test_custom_request_id_echoed_in_response(
    mock_transcribe: AsyncMock, client: TestClient
) -> None:
    mock_transcribe.return_value = "hello"
    custom_id = "my-correlation-id-123"
    response = client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("x.mp3", io.BytesIO(b"data"), "audio/mpeg")},
        headers={"X-Request-ID": custom_id},
    )
    assert response.headers.get("x-request-id") == custom_id
