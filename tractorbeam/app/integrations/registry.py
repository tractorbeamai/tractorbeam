from ..exceptions import AppException
from .base_integration import BaseIntegration
from .notion import Notion


class IntegrationRegistry:
    def __init__(self) -> None:
        self.integrations: dict[str, type[BaseIntegration]] = {}

    def add(
        self: "IntegrationRegistry",
        integration: type[BaseIntegration],
    ) -> None:
        if integration.slug in self.integrations:
            raise AppException.IntegrationAlreadyExists
        if not integration.validate_class_attrs():
            raise AppException.IntegrationInvalid
        self.integrations[integration.slug] = integration

    def upsert(
        self: "IntegrationRegistry",
        integration: type[BaseIntegration],
    ) -> None:
        integration.validate_class_attrs()
        self.integrations[integration.slug] = integration

    def get(self: "IntegrationRegistry", slug: str) -> type[BaseIntegration]:
        integration_class = self.integrations.get(slug)
        if not integration_class:
            raise AppException.IntegrationNotFound
        return integration_class

    def get_all(self: "IntegrationRegistry") -> list[type[BaseIntegration]]:
        return list(self.integrations.values())

    def get_slugs(self: "IntegrationRegistry") -> list[str]:
        return list(self.integrations.keys())

    def clear(self: "IntegrationRegistry") -> None:
        self.integrations.clear()


def get_integration_registry() -> IntegrationRegistry:
    registry = IntegrationRegistry()
    registry.upsert(Notion)
    return registry
