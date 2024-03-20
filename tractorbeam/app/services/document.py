from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..exceptions import AppException
from ..models import Document
from ..schemas.chunk import ChunkSchemaCreate
from ..schemas.document import DocumentSchema, DocumentSchemaCreate
from ..schemas.query import QueryResult
from .chunk import ChunkCRUD


class DocumentService:
    def __init__(self, db: AsyncSession, tenant_id: str, tenant_user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, item: DocumentSchemaCreate) -> DocumentSchema:
        # Create a parent document.
        doc_crud = DocumentCRUD(self.db, self.tenant_id, self.tenant_user_id)
        doc = await doc_crud.create(item)
        if not doc:
            raise AppException.DocumentCreationFailed

        # Segement and save individual child chunks.
        content_chunks = item.content.split("\n")
        chunk_crud = ChunkCRUD(self.db, self.tenant_id, self.tenant_user_id)
        for chunk in content_chunks:
            await chunk_crud.create(
                ChunkSchemaCreate(
                    content=chunk,
                    document_id=doc.id,
                ),
            )

        # Retrieve the parent document.
        doc_with_chunks = await doc_crud.find_one(doc.id)
        if not doc_with_chunks:
            raise AppException.DocumentNotFound

        return DocumentSchema.model_validate(doc_with_chunks)

    async def query(self, q: str) -> list[QueryResult]:  # noqa: ARG002
        # for now, ignore q and return all documents
        chunk_crud = ChunkCRUD(self.db, self.tenant_id, self.tenant_user_id)
        db_chunks = await chunk_crud.find_all()
        return [QueryResult(content=d.content, score=0.5) for d in db_chunks]

    async def delete(self, item_id: int) -> bool:
        doc_crud = DocumentCRUD(self.db, self.tenant_id, self.tenant_user_id)
        return await doc_crud.delete(item_id)


class DocumentCRUD:
    def __init__(self, db: AsyncSession, tenant_id: str, tenant_user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, item: DocumentSchemaCreate) -> Document | None:
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
                Document.id == item_id
                and Document.tenant_id == self.tenant_id
                and Document.tenant_user_id == self.tenant_user_id,
            )
            .options(selectinload(Document.chunks))
        )
        return await self.db.scalar(stmt)

    async def delete(self, item_id: int) -> bool:
        stmt = delete(Document).where(
            Document.id == item_id
            and Document.tenant_id == self.tenant_id
            and Document.tenant_user_id == self.tenant_user_id,
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0
