from pydantic import BaseModel, ValidationError

from ..exceptions import AppException


class BaseIntegrationConfigModel(BaseModel):
    """
    An 'IntegrationConfigModel' defines the instance-level configuration fields for an integration.
    For example, the OAuth2IntegrationConfigModel asks for a client_id and client_secret.
    """

    slug: str | None = None

    model_config = {"extra": "forbid"}


class BaseConnectionModel(BaseModel):
    """
    A `ConnectionModel` defines the individual, connection-level fields for an integration.
    For example, the OAuth2ConnectionModel saves an access_token and refresh_token.
    """

    model_config = {"extra": "forbid"}


class BaseIntegration:
    name: str = ""
    default_slug: str = ""
    logo_url: str | None = None

    config_model: type[BaseIntegrationConfigModel] = BaseIntegrationConfigModel
    connection_model: type[BaseConnectionModel] = BaseConnectionModel

    def __init__(
        self,
        connection: BaseConnectionModel,
    ):
        if not connection:
            raise AppException.IntegrationMisconfigured(
                "A connection is required to instantiate an Integration.",
            )

        self.connection = connection

    @classmethod
    def validate_connection(cls: type["BaseIntegration"], config: dict) -> bool:
        ConnectionModel = cls.connection_model  # noqa: N806
        try:
            ConnectionModel(**config)
        except ValidationError:
            return False
        return True

    def get_all_documents(self) -> list[str]:
        raise NotImplementedError(
            "BaseIntegration.get_all_documents() must be implemented by subclasses",
        )
