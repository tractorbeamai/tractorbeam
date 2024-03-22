from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.chunk import ChunkSchema, ChunkSchemaCreate
from ..schemas.query import Query, QueryResult
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims
from ..services.chunk import ChunkService

router = APIRouter(
    prefix="/chunks",
    tags=["chunks"],
    dependencies=[Depends(get_token_claims)],
)


@router.post("/")
async def create_chunk(
    item: ChunkSchemaCreate,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChunkSchema:
    chunk_service = ChunkService(db, claims.tenant_id, claims.tenant_user_id)
    return await chunk_service.create(item)


@router.get("/")
async def get_chunks(
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChunkSchema]:
    chunk_service = ChunkService(db, claims.tenant_id, claims.tenant_user_id)
    return await chunk_service.find_all()


@router.get("/{chunk_id}/")
async def get_chunk(
    chunk_id: int,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChunkSchema:
    chunk_service = ChunkService(db, claims.tenant_id, claims.tenant_user_id)
    return await chunk_service.find_one(chunk_id)


@router.delete("/{chunk_id}/")
async def delete_chunk(
    chunk_id: int,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> bool:
    chunk_service = ChunkService(db, claims.tenant_id, claims.tenant_user_id)
    return await chunk_service.delete(chunk_id)


@router.post("/query/")
async def query_chunks(
    query: Query,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[QueryResult]:
    chunk_service = ChunkService(db, claims.tenant_id, claims.tenant_user_id)
    return await chunk_service.query(query)
