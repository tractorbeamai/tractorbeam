from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

from .exceptions import AppExceptionCase
from .qdrant import ensure_collection
from .routers import chunk, connection, document, health, integration, token
from .settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # check if collection exists
    await ensure_collection(get_settings().qdrant_collection_name)

    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(AppExceptionCase)
async def custom_app_exception_handler(_request, exception):
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "exception": exception.exception_case,
            "message": exception.message,
        },
    )


api = APIRouter(prefix="/api/v1")

api.include_router(health.router)
api.include_router(token.router)
api.include_router(document.router)
api.include_router(chunk.router)
api.include_router(integration.router)
api.include_router(connection.router)

app.include_router(api)
