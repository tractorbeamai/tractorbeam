import importlib
from typing import Annotated

from fastapi import Depends
from pydantic import ValidationError

from ..exceptions import AppException
from ..settings import Settings, get_settings
from .base_integration import BaseIntegration
from .oauth2_integration import OAuth2Integration


class IntegrationRegistry:
    def __init__(self) -> None:
        self.integrations: dict[str, type[BaseIntegration]] = {}

    def add(
        self: "IntegrationRegistry",
        integration: type[BaseIntegration],
        slug: str | None = None,
    ) -> None:
        slug = slug or integration.default_slug

        if slug in self.integrations:
            raise AppException.IntegrationAlreadyExists(
                f'An Integration with slug, "{slug}" already exists. If you are trying to add multiple configurations for one integration, a slug must be provided for subsequent configurations.',
            )

        self.integrations[slug] = integration

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

    @classmethod
    def from_settings(
        cls: type["IntegrationRegistry"],
        settings: Settings,
    ) -> "IntegrationRegistry":
        registry = cls()
        for integration_slug, configs in settings.integrations.items():
            for config in configs:
                try:
                    integration_module = importlib.import_module(
                        f"app.integrations.{integration_slug}",
                    )
                    for obj in integration_module.__dict__.values():
                        if (
                            isinstance(obj, type)
                            and issubclass(obj, BaseIntegration)
                            and obj not in (BaseIntegration, OAuth2Integration)
                        ):
                            config_model = obj.config_model(**config)
                            slug = config_model.slug or obj.default_slug
                            registry.add(obj, slug=slug)
                except ValidationError as e:
                    raise AppException.ConnectionInvalid from e
                except ModuleNotFoundError as e:
                    raise AppException.IntegrationNotFound from e
        return registry


def get_integration_registry(
    settings: Annotated[Settings, Depends(get_settings)],
) -> IntegrationRegistry:
    return IntegrationRegistry.from_settings(settings)
