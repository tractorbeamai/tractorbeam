from typing import Annotated

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..exceptions import AppException
from ..models import Chunk
from ..schemas.chunk import ChunkCreateSchema, ChunkSchema
from ..schemas.query import QueryResultSchema, QuerySchema
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims


class ChunkCRUD:
    def __init__(self, db: AsyncSession, tenant_id: str, tenant_user_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, item: ChunkCreateSchema) -> Chunk | None:
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


class ChunkService:
    def __init__(self, chunk_crud: ChunkCRUD):
        self.chunk_crud = chunk_crud

    async def create(self, item: ChunkCreateSchema) -> ChunkSchema:
        chunk = await self.chunk_crud.create(item)
        if not chunk:
            raise AppException.ChunkCreationFailed
        return ChunkSchema.model_validate(chunk)

    async def find_one(self, item_id: int) -> ChunkSchema:
        chunk = await self.chunk_crud.find_one(item_id)
        if not chunk:
            raise AppException.ChunkNotFound
        return ChunkSchema.model_validate(chunk)

    async def find_all(self) -> list[ChunkSchema]:
        chunks = await self.chunk_crud.find_all()
        return [ChunkSchema.model_validate(chunk) for chunk in chunks]

    async def query(self, query: QuerySchema) -> list[QueryResultSchema]:
        # for now, ignore q and return all documents
        chunks = await self.chunk_crud.find_all()
        return [QueryResultSchema(content=d.content, score=0.5) for d in chunks]

    async def delete(self, item_id: int) -> bool:
        chunk = await self.chunk_crud.delete(item_id)
        if not chunk:
            raise AppException.ChunkNotFound
        return await self.chunk_crud.delete(item_id)


def get_chunk_crud(
    db: Annotated[AsyncSession, Depends(get_db)],
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
):
    return ChunkCRUD(db, claims.tenant_id, claims.tenant_user_id)


def get_chunk_service(
    chunk_crud: Annotated[ChunkCRUD, Depends(get_chunk_crud)],
):
    return ChunkService(chunk_crud)
