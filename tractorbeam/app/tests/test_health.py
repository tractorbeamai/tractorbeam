import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..database import get_db
from ..main import app


@pytest.mark.asyncio()
class TestHealthChecks:
    async def test_health(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == "OK"

    async def test_health_db_connected(
        self,
        client: AsyncClient,
        session: AsyncSession,
    ):
        response = await client.get("/health/db")
        assert response.status_code == status.HTTP_200_OK

    async def test_health_no_db(self, client: AsyncClient):
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
        response = await client.get("/health/db")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        del app.dependency_overrides[get_db]
