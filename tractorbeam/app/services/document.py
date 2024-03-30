from typing import Annotated

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..exceptions import AppException
from ..models import Document
from ..schemas.chunk import ChunkCreateSchema
from ..schemas.document import DocumentCreateSchema, DocumentSchema
from ..schemas.query import QueryResultSchema, QuerySchema
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims
from .chunk import ChunkCRUD, get_chunk_crud


class DocumentCRUD:
    def __init__(self, db: AsyncSession, tenant_id: str, tenant_user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, item: DocumentCreateSchema) -> Document | None:
        doc = Document(
            title=item.title,
            content=item.content,
            tenant_id=self.tenant_id,
            tenant_user_id=self.tenant_user_id,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        return await self.find_one(doc.id)

    async def find_one(self, item_id: int) -> Document | None:
        stmt = (
            select(Document)
            .where(
                (Document.id == item_id)
                & (Document.tenant_id == self.tenant_id)
                & (Document.tenant_user_id == self.tenant_user_id),
            )
            .options(selectinload(Document.chunks))
        )
        return await self.db.scalar(stmt)

    async def find_all(self) -> list[Document]:
        stmt = (
            select(Document)
            .where(
                (Document.tenant_id == self.tenant_id)
                & (Document.tenant_user_id == self.tenant_user_id),
            )
            .options(selectinload(Document.chunks))
        )
        result = await self.db.scalars(stmt)
        return list(result)

    async def delete(self, item_id: int) -> bool:
        stmt = delete(Document).where(
            (Document.id == item_id)
            & (Document.tenant_id == self.tenant_id)
            & (Document.tenant_user_id == self.tenant_user_id),
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0


class DocumentService:
    def __init__(
        self,
        document_crud: DocumentCRUD,
        chunk_crud: ChunkCRUD,
    ):
        self.document_crud = document_crud
        self.chunk_crud = chunk_crud

    async def create(self, item: DocumentCreateSchema) -> DocumentSchema:
        # Create a parent document.
        doc = await self.document_crud.create(item)
        if not doc:
            raise AppException.DocumentCreationFailed

        # Segement and save individual child chunks.
        content_chunks = item.content.split("\n")
        for chunk in content_chunks:
            await self.chunk_crud.create(
                ChunkCreateSchema(
                    content=chunk,
                    document_id=doc.id,
                ),
            )

        # Retrieve the parent document.
        doc_with_chunks = await self.document_crud.find_one(doc.id)

        return DocumentSchema.model_validate(doc_with_chunks)

    async def find_one(self, item_id: int) -> DocumentSchema:
        doc = await self.document_crud.find_one(item_id)
        if not doc:
            raise AppException.DocumentNotFound
        return DocumentSchema.model_validate(doc)

    async def find_all(self) -> list[DocumentSchema]:
        docs = await self.document_crud.find_all()
        return [DocumentSchema.model_validate(doc) for doc in docs]

    async def query(self, query: QuerySchema) -> list[QueryResultSchema]:  # noqa: ARG002
        # for now, ignore q and return all documents
        docs = await self.document_crud.find_all()
        return [QueryResultSchema(content=d.content, score=0.5) for d in docs]

    async def delete(self, item_id: int) -> bool:
        doc = await self.document_crud.find_one(item_id)
        if not doc:
            raise AppException.DocumentNotFound
        return await self.document_crud.delete(item_id)


def get_document_crud(
    db: Annotated[AsyncSession, Depends(get_db)],
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
):
    return DocumentCRUD(db, claims.tenant_id, claims.tenant_user_id)


def get_document_service(
    document_crud: Annotated[DocumentCRUD, Depends(get_document_crud)],
    chunk_crud: Annotated[ChunkCRUD, Depends(get_chunk_crud)],
):
    return DocumentService(document_crud, chunk_crud)
