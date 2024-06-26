import socket
from typing import Annotated

from fastapi import APIRouter, Depends
from qdrant_client import AsyncQdrantClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..exceptions import AppException
from ..qdrant import get_qdrant_client

router = APIRouter()


@router.get("/health")
async def health_check():
    return "OK"


@router.get("/health/db")
async def health_check_db(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await db.execute(text("SELECT 1"))
    except DBAPIError as e:
        raise AppException.DatabaseConnectionFailed from e
    except socket.gaierror as e:
        raise AppException.DatabaseConnectionFailed from e
    else:
        return "OK"


@router.get("/health/vector-db")
async def health_check_vector_db(
    qdrant: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
):
    try:
        await qdrant.get_collections()
    except Exception as e:
        raise AppException.VectorDatabaseConnectionFailed from e
    else:
        return "OK"
