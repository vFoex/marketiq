from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from marketiq.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


@lru_cache
def get_engine() -> AsyncEngine:
    # Force the async psycopg driver regardless of how DATABASE_URL is written:
    # a bare `postgresql://` defaults to sync psycopg2 and the async engine errors.
    url = make_url(get_settings().database_url).set(drivername="postgresql+psycopg")
    return create_async_engine(url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """A transactional session: commit on success, roll back on error."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
