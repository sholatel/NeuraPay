"""Unit tests for VoiceService — provider is mocked so no OpenAI calls are made."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import UploadFile

from app.core.exceptions import FileSizeExceededError, UnsupportedFileTypeError
from app.services.voice.service import VoiceService


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_upload_file(
    filename: str,
    content: bytes = b"fake_audio_data",
    content_type: str = "audio/mpeg",
) -> UploadFile:
    mock = MagicMock(spec=UploadFile)
    mock.filename = filename
    mock.content_type = content_type
    mock.read = AsyncMock(return_value=content)
    return mock


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_provider() -> AsyncMock:
    provider = AsyncMock()
    provider.transcribe = AsyncMock(return_value="Send ₦10,000 to my brother")
    return provider


@pytest.fixture
def service(mock_provider: AsyncMock) -> VoiceService:
    return VoiceService(provider=mock_provider)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_transcribe_mp3_success(service: VoiceService, mock_provider: AsyncMock) -> None:
    file = make_upload_file("command.mp3")
    result = await service.transcribe(file)

    assert result.success is True
    assert result.data == {"transcript": "Send ₦10,000 to my brother"}
    mock_provider.transcribe.assert_awaited_once()


@pytest.mark.asyncio
async def test_transcribe_wav_success(service: VoiceService) -> None:
    file = make_upload_file("command.wav", content_type="audio/wav")
    result = await service.transcribe(file)
    assert result.success is True


@pytest.mark.asyncio
async def test_transcribe_webm_success(service: VoiceService) -> None:
    file = make_upload_file("recording.webm", content_type="audio/webm")
    result = await service.transcribe(file)
    assert result.success is True


@pytest.mark.asyncio
async def test_transcribe_m4a_success(service: VoiceService) -> None:
    file = make_upload_file("voice.m4a", content_type="audio/m4a")
    result = await service.transcribe(file)
    assert result.success is True


@pytest.mark.asyncio
async def test_unsupported_extension_raises(service: VoiceService) -> None:
    file = make_upload_file("document.txt", content_type="text/plain")
    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        await service.transcribe(file)
    assert ".txt" in exc_info.value.message


@pytest.mark.asyncio
async def test_no_extension_raises(service: VoiceService) -> None:
    file = make_upload_file("audiofile", content_type="application/octet-stream")
    with pytest.raises(UnsupportedFileTypeError):
        await service.transcribe(file)


@pytest.mark.asyncio
async def test_file_too_large_raises(service: VoiceService) -> None:
    large_audio = b"x" * (26 * 1024 * 1024)  # 26 MB — exceeds 25 MB default
    file = make_upload_file("big.mp3", content=large_audio)
    with pytest.raises(FileSizeExceededError) as exc_info:
        await service.transcribe(file)
    assert "25 MB" in exc_info.value.message


@pytest.mark.asyncio
async def test_provider_is_called_with_correct_args(
    service: VoiceService, mock_provider: AsyncMock
) -> None:
    content = b"real_audio_bytes"
    file = make_upload_file("test.mp3", content=content, content_type="audio/mpeg")
    await service.transcribe(file)

    mock_provider.transcribe.assert_awaited_once_with(
        audio_bytes=content,
        filename="test.mp3",
        content_type="audio/mpeg",
    )
