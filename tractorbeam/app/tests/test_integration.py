import pytest
from fastapi import status
from httpx import AsyncClient

from ..integrations.mock.mock_oauth2 import MockOAuth2Integration
from ..integrations.registry import IntegrationRegistry, get_integration_registry
from ..main import app
from ..schemas.token import TokenClaimsSchema


@pytest.fixture()
def mock_registry():
    mock_registry = IntegrationRegistry()
    mock_registry.upsert(MockOAuth2Integration)

    app.dependency_overrides[get_integration_registry] = lambda: mock_registry

    yield mock_registry

    del app.dependency_overrides[get_integration_registry]


@pytest.mark.asyncio()
async def test_get_integrations(
    client: AsyncClient,
    mock_registry: IntegrationRegistry,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims
    response = await client.get(
        "/integrations/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0


@pytest.mark.asyncio()
async def test_get_integration(
    client: AsyncClient,
    mock_registry: IntegrationRegistry,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims

    response = await client.get(
        "/integrations/mock/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["slug"] == "mock"
    assert data["name"] == "Mock Integration"


@pytest.mark.asyncio()
async def test_get_integration_not_found(
    client: AsyncClient,
    mock_registry: IntegrationRegistry,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims

    response = await client.get(
        "/integrations/not-a-real-slug/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
