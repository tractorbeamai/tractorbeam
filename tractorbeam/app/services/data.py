from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Chunk, Document
from ..schemas.chunk import ChunkSchemaCreate
from ..schemas.document import DocumentSchemaCreate
from ..utils.app_exceptions import AppException
from ..utils.service_result import ServiceResult


class DataService:
    def __init__(self, db: AsyncSession, tenant_id: str, tenant_user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, document: DocumentSchemaCreate) -> ServiceResult:
        # Create a parent document.
        doc_crud = DocumentCRUD(self.db, self.tenant_id, self.tenant_user_id)
        db_document = await doc_crud.create(document)
        if not db_document:
            return ServiceResult(AppException.DocumentCreateFailed())

        # Segement and save individual child chunks.
        text_chunks = document.text.split("\n")
        chunk_crud = ChunkCRUD(self.db, self.tenant_id, self.tenant_user_id)
        for chunk in text_chunks:
            await chunk_crud.create(
                Chunk(
                    text=chunk,
                    document_id=db_document.id,
                    tenant_id=self.tenant_id,
                    tenant_user_id=self.tenant_user_id,
                )
            )

        # Return the parent document.
        await self.db.refresh(db_document)

        return ServiceResult(db_document)

    async def query(self, q: str) -> ServiceResult:
        # for now, ignore q and return all documents
        chunk_crud = ChunkCRUD(self.db, self.tenant_id, self.tenant_user_id)
        db_chunks = await chunk_crud.findAll()
        if not db_chunks:
            return ServiceResult(AppException.ChunkNotFound())
        return ServiceResult([{"text": d.text, "score": 0.5} for d in db_chunks])


class DocumentCRUD:
    def __init__(self, db: AsyncSession, tenant_id: str, tenant_user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, item: DocumentSchemaCreate) -> Chunk:
        doc = Document(
            text=item.text,
            title=item.title,
            tenant_id=self.tenant_id,
            tenant_user_id=self.tenant_user_id,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc


class ChunkCRUD:
    def __init__(self, db: AsyncSession, tenant_id: str, tenant_user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, chunk: ChunkSchemaCreate) -> Optional[Chunk]:
        db_chunk = Chunk(
            text=chunk.text,
            document_id=chunk.document_id,
            tenant_id=self.tenant_id,
            tenant_user_id=self.tenant_user_id,
        )
        self.db.add(db_chunk)
        await self.db.commit()
        await self.db.refresh(db_chunk)
        return db_chunk

    async def findOne(self, chunk_id: int) -> Optional[Chunk]:
        chunk = (
            await self.db.query(Chunk)
            .filter(
                Chunk.id == chunk_id,
                Chunk.tenant_id == self.tenant_id,
                Chunk.tenant_user_id == self.tenant_user_id,
            )
            .first()
        )
        if chunk:
            return chunk
        return None

    async def findAll(self) -> list[Chunk]:
        return (
            await self.db.query(Chunk)
            .filter(
                Chunk.tenant_id == self.tenant_id,
                Chunk.tenant_user_id == self.tenant_user_id,
            )
            .all()
        )

    async def delete(self, chunk_id: int) -> bool:
        chunk = await self.findOne(chunk_id)
        if not chunk:
            return False
        await self.db.delete(chunk)
        await self.db.commit()
        return True
