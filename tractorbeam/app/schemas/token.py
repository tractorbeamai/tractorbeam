from pydantic import BaseModel


class TokenSchema(BaseModel):
    token: str


class TokenClaimsSchema(BaseModel):
    tenant_id: str
    tenant_user_id: str
