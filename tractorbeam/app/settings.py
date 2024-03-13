from functools import lru_cache
from typing import Any

import httpx
import tomllib
from pydantic import BaseModel, ConfigDict
from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)
from pydantic_settings.sources import ConfigFileSourceMixin


class IntegrationSettings(BaseModel):
    enabled: bool
    api_key: str

    model_config = ConfigDict(extra="ignore")


class Settings(BaseSettings):
    database_url: str
    secret: str
    cloud: bool = False
    api_keys: list[str]
    integrations: list[IntegrationSettings]

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        # toml_url="https://...",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        toml_settings = TomlConfigSettingsSource(settings_cls)

        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            toml_settings,
        )


class RemoteTomlConfigSettingsSource(InitSettingsSource, ConfigFileSourceMixin):
    def __init__(
        self,
        settings_cls: type[BaseSettings],
        toml_url: str | None,
    ):
        self.toml_url = toml_url or settings_cls.model_config.get("toml_url")
        self.toml_data = self._load(self.toml_url)
        super().__init__(settings_cls, self.toml_data)

    def _load(self, url: str) -> dict[str, Any]:
        response = httpx.get(url)
        response.raise_for_status()
        return tomllib.loads(response.text)


@lru_cache
def get_settings():
    return Settings()
