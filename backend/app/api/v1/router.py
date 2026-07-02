from fastapi import APIRouter

from app.api.v1.endpoints.agent import router as agent_router
from app.api.v1.endpoints.auto_route import router as auto_route_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.split_bill import router as split_bill_router
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(agent_router, tags=["agent"])
api_router.include_router(auto_route_router, tags=["auto-route"])
api_router.include_router(split_bill_router, tags=["split-bill"])
