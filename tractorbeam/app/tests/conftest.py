from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from ..main import app
from ..schemas.token import TokenClaimsSchema
from ..security import get_api_key, get_token_claims
from ..services.token import TokenService


@pytest.fixture(autouse=True)
async def async_client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:80",
    ) as client:
        yield client


@pytest.fixture(scope="function")
def api_key():
    key = "test-secret-key"

    def mock_get_api_key():
        return key

    app.dependency_overrides[get_api_key] = mock_get_api_key

    yield key

    del app.dependency_overrides[get_api_key]


@pytest.fixture(scope="function")
def token_with_claims():
    claims = TokenClaimsSchema(
        tenant_id="abc-123",
        tenant_user_id="def-456",
    )

    def mock_get_token_claims():
        return claims

    app.dependency_overrides[get_token_claims] = mock_get_token_claims

    yield TokenService().create(claims, "secret"), claims

    del app.dependency_overrides[get_token_claims]
