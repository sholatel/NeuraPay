from fastapi import APIRouter

from app.api.v1.endpoints import operations, voice

api_v1_router = APIRouter()

# Register feature routers under /api/v1
api_v1_router.include_router(voice.router, prefix="/voice", tags=["Voice"])
api_v1_router.include_router(operations.router, prefix="/operations", tags=["Operations"])
