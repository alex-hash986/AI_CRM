import asyncio
from typing import Annotated, Literal

from asyncpg import InterfaceError, PostgresError
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_async_db

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "unhealthy"]


async def postgres_available(db: AsyncSession) -> bool:
    try:
        async with asyncio.timeout(1.5):
            return await db.scalar(text("SELECT 1")) == 1
    except (SQLAlchemyError, PostgresError, InterfaceError, OSError, TimeoutError):
        return False


async def redis_available() -> bool:
    try:
        async with asyncio.timeout(1.5):
            async with Redis.from_url(get_settings().redis_url) as redis:
                return bool(await redis.ping())
    except (RedisError, OSError, TimeoutError):
        return False


@router.get("/health", responses={503: {"model": HealthResponse}})
async def health(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> HealthResponse:
    postgres_ok, redis_ok = await asyncio.gather(postgres_available(db), redis_available())
    if postgres_ok and redis_ok:
        return HealthResponse(status="ok")

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="degraded" if postgres_ok or redis_ok else "unhealthy")
