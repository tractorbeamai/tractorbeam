import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Annotated

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, Security
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session, engine, get_db
from ..exceptions import AppException
from ..main import app
from ..models import Base
from ..schemas.token import TokenClaimsSchema
from ..security import api_key_header, get_api_key, get_token_claims
from ..services.token import TokenService
from ..settings import Settings, get_settings

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
async def app_with_test_overrides(
    session: AsyncSession,
):
    async def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    async with LifespanManager(app) as lifespan:
        yield lifespan.app


@pytest.fixture()
async def client(app_with_test_overrides: FastAPI) -> AsyncGenerator:
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_overrides),  # type: ignore[arg-type]
        base_url="http://testhost",
    ) as ac:
        yield ac


@pytest.fixture()
def api_key():
    key = "test-secret-key"

    def mock_get_api_key(
        api_key_header: Annotated[str, Security(api_key_header)],
    ):
        if api_key_header != key:
            raise AppException.APIKeyInvalid
        return api_key_header

    app.dependency_overrides[get_api_key] = mock_get_api_key

    yield key

    del app.dependency_overrides[get_api_key]


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


@pytest.fixture(autouse=True)
async def _settings():
    def mock_get_settings():
        return Settings(
            integrations={
                "mock_oauth2": [
                    {
                        "client_id": "abc",
                        "client_secret": "def",
                    },
                ],
            },
        )

    app.dependency_overrides[get_settings] = mock_get_settings

    yield

    del app.dependency_overrides[get_settings]
