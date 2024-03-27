import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ..database import get_db
from ..main import app


@pytest.mark.asyncio()
class TestHealthChecks:
    async def test_health(self: "TestHealthChecks", client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == "OK"

    async def test_health_db_connected(
        self: "TestHealthChecks",
        client: AsyncClient,
    ):
        response = await client.get("/api/v1/health/db")
        assert response.status_code == status.HTTP_200_OK

    async def test_health_db_missing(self: "TestHealthChecks", client: AsyncClient):
        bad_engine = create_async_engine(
            "postgresql+asyncpg://bad_url",
            future=True,
        )

        bad_session = async_sessionmaker(
            bad_engine,
            autoflush=False,
            expire_on_commit=False,
        )

        async def get_bad_db():
            async with bad_session() as session:
                yield session

        app.dependency_overrides[get_db] = get_bad_db
        response = await client.get("/api/v1/health/db")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        del app.dependency_overrides[get_db]

    async def test_health_db_api_error(
        self: "TestHealthChecks",
        monkeypatch,
        client: AsyncClient,
    ):
        from sqlalchemy.exc import DBAPIError

        async def mock_execute(*_args, **_kwargs):
            raise DBAPIError(statement="SELECT 1", params="", orig=None)

        monkeypatch.setattr("sqlalchemy.ext.asyncio.AsyncSession.execute", mock_execute)

        response = await client.get("/api/v1/health/db")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
