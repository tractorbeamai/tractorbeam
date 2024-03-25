import asyncio
from collections.abc import AsyncGenerator, Callable, Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session, engine, get_db
from ..main import app
from ..models import Base
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims
from ..services.token import TokenService
from ..settings import get_settings

DATABASE_URL = get_settings().database_url

# https://rogulski.it/blog/sqlalchemy-14-async-orm-with-fastapi/


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
        async with async_session(bind=connection) as session:
            yield session
            await session.flush()
            await session.rollback()


@pytest.fixture()
def override_get_db(session: AsyncSession) -> Callable:
    async def _override_get_db():
        yield session

    return _override_get_db


@pytest.fixture()
def app_with_db_override(override_get_db: Callable) -> FastAPI:
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture()
async def client(app_with_db_override: FastAPI) -> AsyncGenerator:
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db_override),  # type: ignore[arg-type]
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture()
def api_key():
    key = "test-secret-key"

    def mock_get_settings():
        settings = get_settings()
        settings.api_keys += [key]
        return settings

    app.dependency_overrides[get_settings] = mock_get_settings

    yield key

    del app.dependency_overrides[get_settings]


@pytest.fixture()
async def token_with_claims():
    claims = TokenClaimsSchema(
        tenant_id="abc-123",
        tenant_user_id="def-456",
    )
    token = await TokenService().create(claims, "secret")

    def mock_get_token_claims():
        return claims

    app.dependency_overrides[get_token_claims] = mock_get_token_claims

    yield token, claims

    del app.dependency_overrides[get_token_claims]
