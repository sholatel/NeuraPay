from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    FileSizeExceededError,
    OpenAIAPIError,
    TranscriptionError,
    UnsupportedFileTypeError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


async def unsupported_file_type_handler(
    request: Request, exc: UnsupportedFileTypeError
) -> JSONResponse:
    logger.warning("Unsupported file type", path=str(request.url.path), error=exc.message)
    return JSONResponse(
        status_code=415,
        content={"success": False, "error": exc.message, "detail": exc.detail},
    )


async def file_size_exceeded_handler(
    request: Request, exc: FileSizeExceededError
) -> JSONResponse:
    logger.warning("File size exceeded", path=str(request.url.path), error=exc.message)
    return JSONResponse(
        status_code=413,
        content={"success": False, "error": exc.message},
    )


async def transcription_error_handler(
    request: Request, exc: TranscriptionError
) -> JSONResponse:
    logger.error("Transcription failed", path=str(request.url.path), error=exc.message)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Transcription failed. Please try again."},
    )


async def openai_api_error_handler(
    request: Request, exc: OpenAIAPIError
) -> JSONResponse:
    logger.error("OpenAI API error", path=str(request.url.path), error=exc.message)
    return JSONResponse(
        status_code=502,
        content={"success": False, "error": "AI service temporarily unavailable."},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Request validation failed", path=str(request.url.path), errors=exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "detail": exc.errors(),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", path=str(request.url.path), exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "An unexpected error occurred."},
    )
