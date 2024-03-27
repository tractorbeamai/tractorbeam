import datetime

import jwt

from ..exceptions import AppException
from ..schemas.token import TokenClaimsSchema, TokenSchema


class TokenService:
    async def create(self, token: TokenClaimsSchema, secret: str) -> TokenSchema:
        default_claims = {
            "iat": datetime.datetime.now(datetime.UTC),
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1),
        }
        claims = {
            "tenant_id": token.tenant_id,
            "tenant_user_id": token.tenant_user_id,
            "iat": token.iat or default_claims["iat"],
            "exp": token.exp or default_claims["exp"],
        }

        encoded_jwt = jwt.encode(claims, secret, algorithm="HS256")

        return TokenSchema(token=encoded_jwt)

    async def verify(self, token: str, secret: str) -> TokenClaimsSchema:
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as e:
            raise AppException.TokenExpired from e
        except jwt.InvalidTokenError as e:
            raise AppException.TokenInvalid from e
        return TokenClaimsSchema(**payload)


def get_token_service() -> TokenService:
    return TokenService()
