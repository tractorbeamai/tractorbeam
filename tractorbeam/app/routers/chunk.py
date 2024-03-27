from typing import Annotated

from fastapi import APIRouter, Depends

from ..schemas.chunk import ChunkSchema, ChunkSchemaCreate
from ..schemas.query import QueryResultSchema, QuerySchema
from ..security import get_token_claims
from ..services.chunk import ChunkService, get_chunk_service

router = APIRouter(
    prefix="/chunks",
    tags=["chunks"],
    dependencies=[Depends(get_token_claims)],
)


@router.post("/")
async def create_chunk(
    item: ChunkSchemaCreate,
    chunk_service: Annotated[ChunkService, Depends(get_chunk_service)],
) -> ChunkSchema:
    return await chunk_service.create(item)


@router.get("/")
async def get_chunks(
    chunk_service: Annotated[ChunkService, Depends(get_chunk_service)],
) -> list[ChunkSchema]:
    return await chunk_service.find_all()


@router.get("/{chunk_id}/")
async def get_chunk(
    chunk_id: int,
    chunk_service: Annotated[ChunkService, Depends(get_chunk_service)],
) -> ChunkSchema:
    return await chunk_service.find_one(chunk_id)


@router.delete("/{chunk_id}/")
async def delete_chunk(
    chunk_id: int,
    chunk_service: Annotated[ChunkService, Depends(get_chunk_service)],
) -> bool:
    return await chunk_service.delete(chunk_id)


@router.post("/query/")
async def query_chunks(
    query: QuerySchema,
    chunk_service: Annotated[ChunkService, Depends(get_chunk_service)],
) -> list[QueryResultSchema]:
    return await chunk_service.query(query)
