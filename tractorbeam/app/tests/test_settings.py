import httpx
import pytest
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from ..settings import RemoteTomlConfigSettingsSource, Settings, get_settings


@pytest.mark.asyncio()
class TestSettings:
    async def test_get_settings(self: "TestSettings"):
        settings = get_settings()
        assert settings is not None
        assert settings.cloud is not None  # example defaultable setting

    def _mock_httpx_get(self: "TestSettings", _url: str) -> httpx.Response:
        content = """
fruits=["banana", "apple"]
breakfast=true
"""
        request = httpx.Request(method="GET", url=_url)
        return httpx.Response(200, content=content, request=request)

    async def test_remote_toml_config_settings_source(
        self: "TestSettings",
        monkeypatch,
    ):
        monkeypatch.setattr("httpx.get", self._mock_httpx_get)

        settings = RemoteTomlConfigSettingsSource(
            settings_cls=Settings,
            toml_url="http://example.com/config.toml",
        )()
        assert settings is not None
        assert settings["fruits"] == ["banana", "apple"]
        assert settings["breakfast"] is True

    async def test_remote_toml_settings_source_load_settings(
        self: "TestSettings",
        monkeypatch,
    ):
        monkeypatch.setattr("httpx.get", self._mock_httpx_get)

        class FakeSettings(BaseSettings):
            fruits: list[str]
            breakfast: bool

            model_config = SettingsConfigDict(
                toml_url="https://example.com/config.toml",
                extra="ignore",
            )  # type: ignore[typeddict-unknown-key]

            @classmethod
            def settings_customise_sources(  # noqa: PLR0913
                cls,
                settings_cls: type[BaseSettings],
                init_settings: PydanticBaseSettingsSource,
                env_settings: PydanticBaseSettingsSource,
                dotenv_settings: PydanticBaseSettingsSource,
                file_secret_settings: PydanticBaseSettingsSource,
            ) -> tuple[PydanticBaseSettingsSource, ...]:
                remote_toml_settings = RemoteTomlConfigSettingsSource(
                    settings_cls,
                )

                return (
                    init_settings,
                    env_settings,
                    dotenv_settings,
                    file_secret_settings,
                    remote_toml_settings,
                )

        settings = FakeSettings()  # type: ignore[call-arg]
        assert settings.fruits == ["banana", "apple"]
        assert settings.breakfast is True
