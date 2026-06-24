import asyncio
import sys
from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from marketiq.storage import models  # noqa: F401 — registers the rows on Base.metadata
from marketiq.storage.database import Base

# psycopg async needs a SelectorEventLoop on Windows (not the default Proactor).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def timescale_url() -> Iterator[str]:
    """Start one throwaway TimescaleDB container for the whole test session."""
    with PostgresContainer(
        "timescale/timescaledb:2.27.2-pg17", driver="psycopg"
    ) as container:
        yield container.get_connection_url()


@pytest.fixture
async def session(timescale_url: str) -> AsyncIterator[AsyncSession]:
    """A clean DB session per test: fresh schema, isolated, disposed afterwards."""
    engine = create_async_engine(timescale_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session
    await engine.dispose()
