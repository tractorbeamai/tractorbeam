from typing import Iterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from ..database import async_engine
from ..main import app


@pytest_asyncio.fixture
async def async_client() -> Iterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:80",
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
