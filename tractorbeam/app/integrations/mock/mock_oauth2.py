from ..oauth2_integration import (
    OAuth2ConnectionModel,
    OAuth2Integration,
    OAuth2IntegrationConfigModel,
)


class MockOAuth2IntegrationConfig(OAuth2IntegrationConfigModel):
    pass


class MockOAuth2Connection(OAuth2ConnectionModel):
    pass


class MockOAuth2Integration(OAuth2Integration):
    name = "Mock Integration"
    slug = "mock"
    logo_url = "https://placekitten.com/g/400/400"

    oauth2_api_root = "https://mock-integration.com"
    oauth2_authorization_endpoint = "/authorize"
    oauth2_token_endpoint = "/token"

    @classmethod
    def config_model(cls: type[OAuth2Integration]):
        return MockOAuth2IntegrationConfig

    @classmethod
    def connection_model(cls: type[OAuth2Integration]):
        return MockOAuth2Connection

    @classmethod
    def get_access_token(
        cls: type[OAuth2Integration],
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ):
        return {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "expires_at": "mock-expires-at",
        }

    def get_all_documents(self: OAuth2Integration) -> list[str]:
        return ["Document 1", "Document 2", "Document 3"]
