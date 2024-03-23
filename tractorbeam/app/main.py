from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .exceptions import AppExceptionCase
from .routers import chunk, document, health, integration, token

app = FastAPI(root_path="/api/v1")


@app.exception_handler(AppExceptionCase)
async def custom_app_exception_handler(_request, exception):
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "exception": exception.exception_case,
            "context": exception.context,
        },
    )


app.include_router(health.router)
app.include_router(token.router)
app.include_router(document.router)
app.include_router(chunk.router)
app.include_router(integration.router)
