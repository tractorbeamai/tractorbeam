from typing import Annotated

from fastapi import APIRouter, Depends

from ..schemas.connection import (
    ConnectionCreateSchema,
    ConnectionSchema,
    ConnectionUpdateSchema,
)
from ..security import get_token_claims
from ..services.connection import ConnectionService, get_connection_service

router = APIRouter(
    prefix="/connections",
    tags=["connections"],
    dependencies=[Depends(get_token_claims)],
)


@router.post("/")
async def create_connection(
    connection: ConnectionCreateSchema,
    connection_service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> ConnectionSchema:
    return await connection_service.create(connection)


@router.get("/")
async def get_connections(
    connection_service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> list[ConnectionSchema]:
    return await connection_service.find_all()


@router.get("/{connection_id}/")
async def get_connection(
    connection_id: int,
    connection_service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> ConnectionSchema:
    return await connection_service.find_one(connection_id)


@router.put("/{connection_id}/")
async def update_connection(
    connection_id: int,
    connection: ConnectionUpdateSchema,
    connection_service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> ConnectionSchema:
    return await connection_service.update(connection_id, connection)


@router.delete("/{connection_id}/")
async def delete_connection(
    connection_id: int,
    connection_service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> bool:
    return await connection_service.delete(connection_id)
