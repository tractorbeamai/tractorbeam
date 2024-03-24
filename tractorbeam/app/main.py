from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

from .exceptions import AppExceptionCase
from .routers import chunk, document, health, integration, token

app = FastAPI(root_path="")


@app.exception_handler(AppExceptionCase)
async def custom_app_exception_handler(_request, exception):
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "exception": exception.exception_case,
            "context": exception.context,
        },
    )


api = APIRouter(prefix="/api/v1")

api.include_router(health.router)
api.include_router(token.router)
api.include_router(document.router)
api.include_router(chunk.router)
api.include_router(integration.router)

app.include_router(api)
