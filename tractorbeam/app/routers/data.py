from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.document import DocumentSchemaCreate
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims
from ..services.data import DataService
from ..utils.service_result import handle_result

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_token_claims)],
)


@router.post("/")
async def create_document(
    item: DocumentSchemaCreate,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc_service = DataService(db, claims.tenant_id, claims.tenant_user_id)
    result = await doc_service.create(item)
    return handle_result(result)


@router.get("/")
async def query_documents(
    q: str,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    doc_service = DataService(db, claims.tenant_id, claims.tenant_user_id)
    result = await doc_service.query(q)
    return handle_result(result)
