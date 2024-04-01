from typing import cast

import pytest
from pydantic_settings import BaseSettings

from ..exceptions import AppException
from ..integrations.mock_oauth2 import MockOAuth2Integration
from ..integrations.registry import IntegrationRegistry, get_integration_registry
from ..settings import Settings


@pytest.mark.asyncio()
class TestIntegrationRegistry:
    async def test_empty_on_init(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()

        assert len(registry.integrations) == 0

    async def test_add(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        assert len(registry.integrations) == 1

    async def test_add_default_slug(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        assert len(registry.integrations) == 1
        assert registry.integrations["mock_oauth2"] == MockOAuth2Integration
        assert MockOAuth2Integration.default_slug in registry.integrations

    async def test_add_custom_slug(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration, slug="custom")

        assert len(registry.integrations) == 1
        assert registry.integrations["custom"] == MockOAuth2Integration
        assert MockOAuth2Integration.default_slug not in registry.integrations

    async def test_add_duplicate(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        with pytest.raises(AppException.IntegrationAlreadyExists):
            registry.add(MockOAuth2Integration)

    async def test_get(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        integration = registry.get("mock_oauth2")

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

        assert slugs == [MockOAuth2Integration.default_slug]

    async def test_clear(self: "TestIntegrationRegistry"):
        registry = IntegrationRegistry()
        registry.add(MockOAuth2Integration)

        registry.clear()

        assert len(registry.integrations) == 0

    async def test_from_settings(self: "TestIntegrationRegistry"):
        class MockSettings(BaseSettings):
            integrations: dict[str, list[dict[str, str]]] = {
                "mock_oauth2": [
                    {
                        "client_id": "abc",
                        "client_secret": "def",
                    },
                ],
            }

        settings = cast(Settings, MockSettings())
        registry = get_integration_registry(settings=settings)

        assert isinstance(registry, IntegrationRegistry)
        assert registry.integrations["mock_oauth2"] == MockOAuth2Integration

    async def test_from_settings_empty(self: "TestIntegrationRegistry"):
        class MockSettings(BaseSettings):
            integrations: dict[str, list[dict[str, str]]] = {}

        settings = cast(Settings, MockSettings())
        registry = IntegrationRegistry.from_settings(settings)

        assert isinstance(registry, IntegrationRegistry)
        assert len(registry.integrations) == 0

    async def test_from_settings_multiple_configs_raises_if_no_slug(
        self: "TestIntegrationRegistry",
    ):
        class MockSettings(BaseSettings):
            integrations: dict[str, list[dict[str, str]]] = {
                "mock_oauth2": [
                    {
                        "client_id": "abc",
                        "client_secret": "def",
                    },
                    {
                        "client_id": "ghi",
                        "client_secret": "jkl",
                    },
                ],
            }

        settings = cast(Settings, MockSettings())

        with pytest.raises(
            AppException.IntegrationAlreadyExists,
        ):
            IntegrationRegistry.from_settings(settings)

    async def test_from_settings_multiple_configs(
        self: "TestIntegrationRegistry",
    ):
        class MockSettings(BaseSettings):
            integrations: dict[str, list[dict[str, str]]] = {
                "mock_oauth2": [
                    {
                        "slug": "mock1",
                        "client_id": "abc",
                        "client_secret": "def",
                    },
                    {
                        "slug": "mock2",
                        "client_id": "ghi",
                        "client_secret": "jkl",
                    },
                ],
            }

        settings = cast(Settings, MockSettings())
        registry = IntegrationRegistry.from_settings(settings)

        assert isinstance(registry, IntegrationRegistry)
        assert len(registry.integrations) == 2
        assert registry.integrations["mock1"] == MockOAuth2Integration
        assert registry.integrations["mock2"] == MockOAuth2Integration


class TestIntegrationRegistryDependency:
    async def test_get_integration_registry(self: "TestIntegrationRegistryDependency"):
        class MockSettings(BaseSettings):
            integrations: dict[str, list[dict[str, str]]] = {
                "mock_oauth2": [
                    {
                        "client_id": "abc",
                        "client_secret": "def",
                    },
                ],
            }

        settings = cast(Settings, MockSettings())
        registry = get_integration_registry(settings=settings)

        assert isinstance(registry, IntegrationRegistry)
        assert len(registry.get_all()) > 0
