from typing import Annotated

from fastapi import APIRouter, Depends

from ..schemas.token import TokenClaimsSchema, TokenSchema
from ..security import get_api_key
from ..services.token import TokenService, get_token_service
from ..settings import Settings, get_settings

router = APIRouter(
    prefix="/token",
    tags=["token"],
    dependencies=[Depends(get_api_key)],
)


@router.post("/", response_model=TokenSchema)
async def create_token(
    claims: TokenClaimsSchema,
    settings: Annotated[Settings, Depends(get_settings)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
):
    return await token_service.create(claims, settings.secret)
