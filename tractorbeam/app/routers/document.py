from typing import Annotated

from fastapi import APIRouter, Depends

from ..schemas.document import DocumentSchema, DocumentSchemaCreate
from ..schemas.query import QueryResultSchema, QuerySchema
from ..security import get_token_claims
from ..services.document import DocumentService, get_document_service

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_token_claims)],
)


@router.post("/")
async def create_document(
    item: DocumentSchemaCreate,
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentSchema:
    return await document_service.create(item)


@router.get("/")
async def get_documents(
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[DocumentSchema]:
    return await document_service.find_all()


@router.get("/{document_id}/")
async def get_document(
    document_id: int,
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentSchema:
    return await document_service.find_one(document_id)


@router.delete("/{document_id}/")
async def delete_document(
    document_id: int,
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> bool:
    return await document_service.delete(document_id)


@router.post("/query/")
async def query_documents(
    query: QuerySchema,
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[QueryResultSchema]:
    return await document_service.query(query)
