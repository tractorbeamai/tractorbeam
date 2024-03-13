from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from .schemas.token import TokenClaimsSchema
from .services.token import TokenService
from .settings import Settings, get_settings
from .utils.service_result import handle_result

api_key_header = APIKeyHeader(name="X-API-Key")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token/")


def get_api_key(
    api_key_header: Annotated[str, Security(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    if api_key_header in settings.api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


def get_token_claims(
    token: Annotated[str, Security(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenClaimsSchema:
    result = TokenService().verify(token, settings.secret)
    payload = handle_result(result)
    return TokenClaimsSchema(**payload)
