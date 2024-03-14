import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Chunk
from ..schemas.token import TokenClaimsSchema


@pytest.mark.asyncio()
class TestCreateChunk:
    async def test_create_chunk(
        self,
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        response = await client.post(
            "/chunks/",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "This is a test chunk"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "This is a test chunk"
        # Verify the chunk is created in the database
        chunk_id = data["id"]
        stmt = select(Chunk).where(Chunk.id == chunk_id).limit(1)
        db_chunk = await session.scalar(stmt)
        assert db_chunk is not None
        assert db_chunk.content == "This is a test chunk"
        assert db_chunk.tenant_id == claims.tenant_id
        assert db_chunk.tenant_user_id == claims.tenant_user_id
