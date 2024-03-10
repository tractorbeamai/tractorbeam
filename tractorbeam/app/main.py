from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.sql import text
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

from .database import get_db
from .routers import foo
from .utils.app_exceptions import AppExceptionCase, app_exception_handler
from .utils.request_exceptions import (
    http_exception_handler,
    request_validation_exception_handler,
)

app = FastAPI()


# ═════════════════════════════ Exception Handlers ═════════════════════════════
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, e):
    return await http_exception_handler(request, e)


@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request, e):
    return await request_validation_exception_handler(request, e)


@app.exception_handler(AppExceptionCase)
async def custom_app_exception_handler(request, e):
    return await app_exception_handler(request, e)


# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════ Routers ═══════════════════════════════════
app.include_router(foo.router)


# ══════════════════════════════════════════════════════════════════════════════


# ════════════════════════════════ Health Check ════════════════════════════════
@app.get("/health")
async def health_check():
    return "OK"


@app.get("/health/db")
async def health_check_db(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await db.exec(text("SELECT 1"))
        return "OK"
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database is not healthy",
        )


# ══════════════════════════════════════════════════════════════════════════════
