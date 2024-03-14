from typing import Annotated

from fastapi import APIRouter, Depends

from ..schemas.token import TokenClaimsSchema, TokenSchema
from ..security import get_api_key
from ..services.token import TokenService
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
):
    return await TokenService().create(claims, settings.secret)
