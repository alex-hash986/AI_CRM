from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    analytics,
    clients,
    communications,
    deals,
    health,
    integrations,
    pipelines,
)

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(clients.router)
router.include_router(deals.router)
router.include_router(pipelines.router)
router.include_router(ai.router)
router.include_router(analytics.router)
router.include_router(communications.router)
router.include_router(integrations.router)
