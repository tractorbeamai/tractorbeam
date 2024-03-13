from typing import Annotated

from fastapi import APIRouter, Depends

from ..schemas.token import TokenClaimsSchema, TokenSchema
from ..security import get_api_key
from ..services.token import TokenService
from ..utils.service_result import handle_result

router = APIRouter(
    prefix="/token",
    tags=["token"],
    dependencies=[Depends(get_api_key)],
)


@router.post("/", response_model=TokenSchema)
async def create_token(
    claims: TokenClaimsSchema, api_key: Annotated[str, Depends(get_api_key)]
):
    result = await TokenService().create(claims, api_key)
    return handle_result(result)
