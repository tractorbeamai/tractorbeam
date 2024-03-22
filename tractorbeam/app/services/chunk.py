from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import AppException
from ..models import Chunk
from ..schemas.chunk import ChunkSchema, ChunkSchemaCreate
from ..schemas.query import Query, QueryResult


class ChunkService:
    def __init__(self, db: AsyncSession, tenant_id: str, tenant_user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, item: ChunkSchemaCreate) -> ChunkSchema:
        chunk_crud = ChunkCRUD(self.db, self.tenant_id, self.tenant_user_id)
        chunk = await chunk_crud.create(item)
        if not chunk:
            raise AppException.ChunkCreationFailed
        return ChunkSchema.model_validate(chunk)

    async def find_one(self, item_id: int) -> ChunkSchema:
        chunk_crud = ChunkCRUD(self.db, self.tenant_id, self.tenant_user_id)
        chunk = await chunk_crud.find_one(item_id)
        if not chunk:
            raise AppException.ChunkNotFound
        return ChunkSchema.model_validate(chunk)

    async def find_all(self) -> list[ChunkSchema]:
        chunk_crud = ChunkCRUD(self.db, self.tenant_id, self.tenant_user_id)
        chunks = await chunk_crud.find_all()
        return [ChunkSchema.model_validate(chunk) for chunk in chunks]

    async def query(self, query: Query) -> list[QueryResult]:  # noqa: ARG002
        # for now, ignore q and return all documents
        chunk_crud = ChunkCRUD(self.db, self.tenant_id, self.tenant_user_id)
        chunks = await chunk_crud.find_all()
        return [QueryResult(content=d.content, score=0.5) for d in chunks]

    async def delete(self, item_id: int) -> bool:
        chunk_crud = ChunkCRUD(self.db, self.tenant_id, self.tenant_user_id)
        chunk = await chunk_crud.find_one(item_id)
        if not chunk:
            raise AppException.ChunkNotFound
        return await chunk_crud.delete(item_id)


class ChunkCRUD:
    def __init__(self, db: AsyncSession, tenant_id: str, tenant_user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, item: ChunkSchemaCreate) -> Chunk | None:
        chunk = Chunk(
            content=item.content,
            document_id=item.document_id,
            tenant_id=self.tenant_id,
            tenant_user_id=self.tenant_user_id,
        )
        self.db.add(chunk)
        await self.db.commit()
        await self.db.refresh(chunk)

        return await self.find_one(chunk.id)

    async def find_one(self, item_id: int) -> Chunk | None:
        stmt = select(Chunk).where(
            (Chunk.id == item_id)
            & (Chunk.tenant_id == self.tenant_id)
            & (Chunk.tenant_user_id == self.tenant_user_id),
        )
        return await self.db.scalar(stmt)

    async def find_all(self) -> list[Chunk]:
        stmt = select(Chunk).where(
            (Chunk.tenant_id == self.tenant_id)
            & (Chunk.tenant_user_id == self.tenant_user_id),
        )
        chunks = await self.db.scalars(stmt)
        return list(chunks)

    async def delete(self, item_id) -> bool:
        stmt = delete(Chunk).where(
            (Chunk.id == item_id)
            & (Chunk.tenant_id == self.tenant_id)
            & (Chunk.tenant_user_id == self.tenant_user_id),
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
