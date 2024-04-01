import base64
from datetime import UTC, datetime, timedelta
from typing import Annotated
from urllib.parse import urlencode

import httpx
from pydantic import Field

from ..exceptions import AppException
from .base_integration import (
    BaseConnectionModel,
    BaseIntegration,
    BaseIntegrationConfigModel,
)


class OAuth2IntegrationConfigModel(BaseIntegrationConfigModel):
    client_id: Annotated[str, Field(description="OAuth2 Client ID")]
    client_secret: Annotated[str, Field(description="OAuth2 Client Secret")]


class OAuth2ConnectionModel(BaseConnectionModel):
    access_token: str
    refresh_token: str | None = None


class OAuth2Integration(BaseIntegration):
    oauth2_api_root: str = ""
    oauth2_authorization_endpoint: str = ""
    oauth2_token_endpoint: str = ""

    config_model = OAuth2IntegrationConfigModel
    connection_model = OAuth2ConnectionModel

    @classmethod
    def get_auth_url(
        cls: type["OAuth2Integration"],
        client_id: str,
        redirect_uri: str,
        extra_query_params: dict | None = None,
    ) -> str:
        """Build a URL to authorize an OAuth2 connection."""
        extra_query_params = extra_query_params or {}
        url = cls.oauth2_api_root + cls.oauth2_authorization_endpoint
        query_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            **extra_query_params,
        }
        return f"{url}?{urlencode(query_params)}"

    @classmethod
    def get_access_token(
        cls: type["OAuth2Integration"],
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ):
        """Get an access token from an OAuth2 code."""
        url = cls.oauth2_api_root + cls.oauth2_token_endpoint
        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        response = httpx.post(url, headers=headers, json=data)
        data = response.json()

        if response.status_code != httpx.codes.OK:
            msg = f"Failed to get access token: {data.get('error_description') or data.get('error') or response.text}"
            raise AppException.IntegrationError(msg)

        token = {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "scope": data.get("scope"),
        }

        if "expires_in" in data:
            expiration = datetime.now(tz=UTC) + timedelta(
                seconds=int(data["expires_in"]),
            )
            token["expires_at"] = expiration.isoformat()

        return token

    @classmethod
    def refresh_access_token(
        cls: type["OAuth2Integration"],
        client_id: str,
        client_secret: str,
        token: dict,
    ):
        """Refresh an expired access token."""
        raise NotImplementedError
