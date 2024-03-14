from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from .exceptions import AppException
from .schemas.token import TokenClaimsSchema
from .services.token import TokenService
from .settings import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token/")


def get_api_key(
    api_key_header: Annotated[str, Security(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    if api_key_header not in settings.api_keys:
        raise AppException.APIKeyInvalid
    return api_key_header


async def get_token_claims(
    token: Annotated[str, Security(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenClaimsSchema:
    return await TokenService().verify(token, settings.secret)
