import pytest

from ..exceptions import AppException
from ..integrations.base_integration import BaseIntegration
from ..integrations.mock.mock_oauth2 import MockOAuth2Integration
from ..integrations.registry import IntegrationRegistry


@pytest.mark.asyncio()
class TestIntegrationRegistry:
    async def test_empty_on_init(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()

        assert len(registry.integrations) == 0

    async def test_add(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        assert len(registry.integrations) == 1

    async def test_add_invalid(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()

        class BadIntegration(BaseIntegration):
            name = ""

        with pytest.raises(AppException.IntegrationInvalid):
            registry.add(BadIntegration)

    async def test_add_duplicate(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        with pytest.raises(AppException.IntegrationAlreadyExists):
            registry.add(MockOAuth2Integration)

    async def test_upsert(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.upsert(MockOAuth2Integration)

        assert len(registry.integrations) == 1

    async def test_upsert_duplicate(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.upsert(MockOAuth2Integration)
        registry.upsert(MockOAuth2Integration)

        assert len(registry.integrations) == 1

    async def test_get(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        integration = registry.get(MockOAuth2Integration.slug)

        assert integration == MockOAuth2Integration

    async def test_get_missing(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()

        with pytest.raises(AppException.IntegrationNotFound):
            registry.get("missing")

    async def test_get_all(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        integrations = registry.get_all()

        assert integrations == [MockOAuth2Integration]

    async def test_get_all_empty(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()

        integrations = registry.get_all()

        assert integrations == []

    async def test_get_slugs(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        slugs = registry.get_slugs()

        assert slugs == [MockOAuth2Integration.slug]

    async def test_clear(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        registry.clear()

        assert len(registry.integrations) == 0
