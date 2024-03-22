from typing import ClassVar

from ..exceptions import AppException
from .base_integration import BaseIntegration
from .notion import Notion


class IntegrationRegistry:
    integrations: ClassVar[dict[str, type[BaseIntegration]]] = {}

    @classmethod
    def add(
        cls: type["IntegrationRegistry"],
        integration: type[BaseIntegration],
    ) -> None:
        if integration.slug in cls.integrations:
            raise AppException.IntegrationAlreadyExists
        if not integration.validate_class_attrs():
            raise AppException.IntegrationInvalid
        cls.integrations[integration.slug] = integration

    @classmethod
    def upsert(
        cls: type["IntegrationRegistry"],
        integration: type[BaseIntegration],
    ) -> None:
        integration.validate_class_attrs()
        cls.integrations[integration.slug] = integration

    @classmethod
    def get(cls: type["IntegrationRegistry"], slug: str) -> type[BaseIntegration]:
        integration_class = cls.integrations.get(slug)
        if not integration_class:
            raise AppException.IntegrationNotFound
        return integration_class

    @classmethod
    def get_all(cls: type["IntegrationRegistry"]) -> list[type[BaseIntegration]]:
        return list(cls.integrations.values())

    @classmethod
    def get_slugs(cls: type["IntegrationRegistry"]) -> list[str]:
        return list(cls.integrations.keys())


def get_integration_registry() -> type[IntegrationRegistry]:
    IntegrationRegistry.upsert(Notion)
    return IntegrationRegistry
