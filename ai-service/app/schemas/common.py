from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str | list | None = None

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: dict | list | None = None
