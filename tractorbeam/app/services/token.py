import datetime

import jwt

from ..schemas.token import TokenClaimsSchema, TokenSchema
from ..utils.app_exceptions import AppException
from ..utils.service_result import ServiceResult


class TokenService:
    async def create(self, token: TokenClaimsSchema, secret: str) -> ServiceResult:
        claims = {
            "tenant_id": token.tenant_id,
            "tenant_user_id": token.tenant_user_id,
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=1),
        }

        encoded_jwt = jwt.encode(claims, secret, algorithm="HS256")

        return ServiceResult(TokenSchema(token=encoded_jwt))

    async def verify(self, token: str, secret: str) -> ServiceResult:
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return ServiceResult(AppException.TokenExpired())
        except jwt.InvalidTokenError:
            return ServiceResult(AppException.TokenInvalid())
        return ServiceResult(TokenClaimsSchema(**payload))
