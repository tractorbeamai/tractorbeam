from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.document import DocumentSchema, DocumentSchemaCreate
from ..schemas.query import Query, QueryResult
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims
from ..services.document import DocumentService

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
) -> DocumentSchema:
    doc_service = DocumentService(db, claims.tenant_id, claims.tenant_user_id)
    return await doc_service.create(item)


@router.get("/")
async def get_documents(
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DocumentSchema]:
    doc_service = DocumentService(db, claims.tenant_id, claims.tenant_user_id)
    return await doc_service.find_all()


@router.get("/{document_id}/")
async def get_document(
    document_id: int,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentSchema:
    doc_service = DocumentService(db, claims.tenant_id, claims.tenant_user_id)
    return await doc_service.find_one(document_id)


@router.delete("/{document_id}/")
async def delete_document(
    document_id: int,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> bool:
    doc_service = DocumentService(db, claims.tenant_id, claims.tenant_user_id)
    return await doc_service.delete(document_id)


@router.post("/query/")
async def query_documents(
    query: Query,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[QueryResult]:
    doc_service = DocumentService(db, claims.tenant_id, claims.tenant_user_id)
    return await doc_service.query(query)
