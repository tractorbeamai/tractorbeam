import tomllib
from functools import lru_cache
from typing import Any

import httpx
from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    qdrant_url: str
    qdrant_port: int
    qdrant_collection_name: str = "chunks"
    secret: str
    cloud: bool = False
    api_keys: list[str]

    # will be validated in handlers
    integrations: dict[str, Any]

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        # toml_url="https://...",  # noqa: ERA001
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(  # noqa: PLR0913
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


class RemoteTomlConfigSettingsSource(InitSettingsSource):
    def __init__(
        self,
        settings_cls: type[BaseSettings],
        toml_url: str | None = None,
    ):
        self.toml_url = toml_url or str(settings_cls.model_config.get("toml_url"))
        self.toml_data = self._load(self.toml_url)
        super().__init__(settings_cls, self.toml_data)

    def _load(self, url: str) -> dict[str, Any]:
        response = httpx.get(url)
        response.raise_for_status()
        return tomllib.loads(response.text)


@lru_cache
def get_settings():
    return Settings()
