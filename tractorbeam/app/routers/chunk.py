from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.chunk import ChunkSchema, ChunkSchemaCreate
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims
from ..services.document import ChunkCRUD

router = APIRouter(
    prefix="/chunks",
    tags=["chunks"],
    dependencies=[Depends(get_token_claims)],
)


@router.post("/", response_model=ChunkSchema)
async def create_chunk(
    item: ChunkSchemaCreate,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    chunk_crud = ChunkCRUD(db, claims.tenant_id, claims.tenant_user_id)
    return await chunk_crud.create(item)


@router.get("/{chunk_id}", response_model=ChunkSchema)
async def get_chunk(
    chunk_id: int,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    chunk_crud = ChunkCRUD(db, claims.tenant_id, claims.tenant_user_id)
    return await chunk_crud.find_one(chunk_id)


@router.delete("/{chunk_id}")
async def delete_chunk(
    chunk_id: int,
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # TODO(wadefletch): replace with real errors
    chunk_crud = ChunkCRUD(db, claims.tenant_id, claims.tenant_user_id)
    success = await chunk_crud.delete(chunk_id)

    if not success:
        return {"message": "Chunk deletion failed"}

    return {"message": "Chunk deleted successfully"}
