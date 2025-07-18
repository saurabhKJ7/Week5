from fastapi import APIRouter

from app.api.endpoints import health, query, comparison

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(comparison.router, prefix="/comparison", tags=["comparison"]) 