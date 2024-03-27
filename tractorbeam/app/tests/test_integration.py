import pytest
from fastapi import status
from httpx import AsyncClient

from ..integrations.mock.mock_oauth2 import MockOAuth2Integration
from ..integrations.registry import IntegrationRegistry, get_integration_registry
from ..main import app
from ..schemas.token import TokenClaimsSchema


@pytest.fixture()
def mock_registry():
    registry = IntegrationRegistry()
    registry.upsert(MockOAuth2Integration)

    app.dependency_overrides[get_integration_registry] = lambda: registry

    yield registry

    del app.dependency_overrides[get_integration_registry]


@pytest.fixture()
def mock_empty_registry():
    registry = IntegrationRegistry()

    app.dependency_overrides[get_integration_registry] = lambda: registry

    yield registry

    del app.dependency_overrides[get_integration_registry]


@pytest.mark.asyncio()
class TestGetIntegrations:
    async def test_get_integrations(
        self: "TestGetIntegrations",
        client: AsyncClient,
        mock_registry: IntegrationRegistry,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims
        response = await client.get(
            "/api/v1/integrations/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0

    async def test_get_integrations_empty(
        self: "TestGetIntegrations",
        client: AsyncClient,
        mock_empty_registry: IntegrationRegistry,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims
        response = await client.get(
            "/api/v1/integrations/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0  # Expecting an empty list since the registry is empty

    async def test_get_integrations_missing_auth(
        self: "TestGetIntegrations",
        client: AsyncClient,
        mock_registry: IntegrationRegistry,
    ):
        response = await client.get("/api/v1/integrations/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestGetIntegration:
    """GET /api/v1/integrations/{integration_slug}/"""

    async def test_get_integration(
        self: "TestGetIntegration",
        client: AsyncClient,
        mock_registry: IntegrationRegistry,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        response = await client.get(
            "/api/v1/integrations/mock/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["slug"] == "mock"
        assert data["name"] == "Mock Integration"

    async def test_get_integration_not_found(
        self: "TestGetIntegration",
        client: AsyncClient,
        mock_registry: IntegrationRegistry,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        response = await client.get(
            "/api/v1/integrations/not-a-real-slug/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_integration_missing_auth(
        self: "TestGetIntegration",
        client: AsyncClient,
        mock_registry: IntegrationRegistry,
    ):
        response = await client.get("/api/v1/integrations/mock/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
