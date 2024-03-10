import asyncio
from typing import Iterator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .. import settings
from ..database import async_engine
from ..main import app


@pytest.fixture(scope="session")
def event_loop(request) -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_client() -> Iterator[AsyncClient]:
    async with AsyncClient(
        app=app, base_url=f"http://{settings.api_v1_prefix}"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def async_session() -> Iterator[AsyncSession]:
    session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with session() as s:
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        yield s

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await async_engine.dispose()
