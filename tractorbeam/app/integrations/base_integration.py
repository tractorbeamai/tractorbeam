from pydantic import BaseModel


class BaseIntegrationConfigModel(BaseModel):
    model_config = {"extra": "forbid"}


class BaseConnectionModel(BaseModel):
    model_config = {"extra": "forbid"}


class BaseIntegration:
    name: str = ""
    slug: str = ""
    logo_url: str | None = None

    @classmethod
    def validate_class_attrs(cls: type["BaseIntegration"]) -> bool:
        return cls.name != "" and cls.slug != ""

    @classmethod
    def config_model(cls: type["BaseIntegration"]) -> type[BaseIntegrationConfigModel]:
        raise NotImplementedError(
            "BaseIntegration.config_model() must be implemented by subclasses",
        )

    @classmethod
    def connection_model(cls: type["BaseIntegration"]) -> type[BaseConnectionModel]:
        raise NotImplementedError(
            "BaseIntegration.connection_model() must be implemented by subclasses",
        )

    def get_all_documents(self) -> list[str]:
        raise NotImplementedError(
            "BaseIntegration.get_all_documents() must be implemented by subclasses",
        )
