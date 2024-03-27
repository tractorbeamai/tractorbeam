from typing import Annotated

import pytest
from fastapi import Depends, status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..main import app
from ..models import Chunk
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims
from ..services.chunk import ChunkCRUD, get_chunk_crud


@pytest.mark.asyncio()
class TestCreateChunk:
    """POST /api/v1/chunks/"""

    async def test_create_chunk(
        self: "TestCreateChunk",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        response = await client.post(
            "/api/v1/chunks/",
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

    @pytest.fixture()
    def _override_get_chunk_crud_broken_create(self: "TestCreateChunk"):
        class BrokenCreateChunkCRUD(ChunkCRUD):
            async def create(self, _item):
                return None

        def get_broken_create_chunk_crud(
            db: Annotated[AsyncSession, Depends(get_db)],
            claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
        ):
            return BrokenCreateChunkCRUD(db, claims.tenant_id, claims.tenant_user_id)

        app.dependency_overrides[get_chunk_crud] = get_broken_create_chunk_crud

        yield

        del app.dependency_overrides[get_chunk_crud]

    @pytest.mark.usefixtures("_override_get_chunk_crud_broken_create")
    async def test_create_chunk_crud_error(
        self: "TestCreateChunk",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.post(
            "/api/v1/chunks/",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "This is a test chunk"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    async def test_create_chunk_invalid_body(
        self: "TestCreateChunk",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        response = await client.post(
            "/api/v1/chunks/",
            headers={"Authorization": f"Bearer {token}"},
            json={"invalid_key": "This is a test chunk"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_chunk_missing_body(
        self: "TestCreateChunk",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        response = await client.post(
            "/api/v1/chunks/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_chunk_missing_auth(
        self: "TestCreateChunk",
        client: AsyncClient,
    ):
        response = await client.post(
            "/api/v1/chunks/",
            json={"content": "This chunk should not be created"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestGetChunks:
    """GET /api/v1/chunks/"""

    async def test_get_chunks(
        self: "TestGetChunks",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        chunk1 = Chunk(
            content="First test chunk",
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        chunk2 = Chunk(
            content="Second test chunk",
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(chunk1)
        session.add(chunk2)
        await session.commit()

        response = await client.get(
            "/api/v1/chunks/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # noqa: PLR2004
        assert data[0]["content"] == "First test chunk"
        assert data[1]["content"] == "Second test chunk"

    async def test_get_chunks_not_found(
        self: "TestGetChunks",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        response = await client.get(
            "/api/v1/chunks/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    async def test_get_chunks_different_tenant(
        self: "TestGetChunks",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        another_tenant_id = "another_tenant_id"
        chunk1 = Chunk(
            content="User's test chunk",
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        chunk2 = Chunk(
            content="Another tenant's test chunk",
            tenant_id=another_tenant_id,  # Different tenant
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(chunk1)
        session.add(chunk2)
        await session.commit()

        response = await client.get(
            "/api/v1/chunks/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1  # Expecting only one chunk that is owned by the tenant
        assert data[0]["content"] == "User's test chunk"

    async def test_get_chunks_different_user(
        self: "TestGetChunks",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        another_user_id = "another_user_id"
        chunk1 = Chunk(
            content="User's test chunk",
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        chunk2 = Chunk(
            content="Another user's test chunk",
            tenant_id=claims.tenant_id,
            tenant_user_id=another_user_id,  # Different user
        )
        session.add(chunk1)
        session.add(chunk2)
        await session.commit()

        response = await client.get(
            "/api/v1/chunks/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1  # Expecting only one chunk that is owned
        assert data[0]["content"] == "User's test chunk"

    async def test_get_chunks_missing_auth(
        self: "TestGetChunks",
        client: AsyncClient,
    ):
        # Attempt to fetch chunks without authorization
        response = await client.get("/api/v1/chunks/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestGetChunk:
    """GET /api/v1/chunks/{chunk_id}/"""

    async def test_get_chunk(
        self: "TestGetChunk",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        chunk = Chunk(
            content="This is a test chunk",
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(chunk)
        await session.commit()
        await session.refresh(chunk)

        response = await client.get(
            f"/api/v1/chunks/{chunk.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "This is a test chunk"

    async def test_get_chunk_not_found(
        self: "TestGetChunk",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.get(
            "/api/v1/chunks/1/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_chunk_different_tenant(
        self: "TestGetChunk",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a chunk owned by a user in a different tenant
        different_tenant_chunk = Chunk(
            content="This chunk is owned by a user in a different tenant",
            tenant_id="different_tenant_id",  # Assuming a different tenant ID
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(different_tenant_chunk)
        await session.commit()
        await session.refresh(different_tenant_chunk)

        # Attempt to fetch the chunk from a different tenant
        response = await client.get(
            f"/api/v1/chunks/{different_tenant_chunk.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_chunk_different_user(
        self: "TestGetChunk",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a chunk owned by another user
        another_user_chunk = Chunk(
            content="This chunk is owned by another user",
            tenant_id=claims.tenant_id,
            tenant_user_id="another_user_id",  # Assuming a different user ID
        )
        session.add(another_user_chunk)
        await session.commit()
        await session.refresh(another_user_chunk)

        # Attempt to fetch the chunk not owned by the token's user
        response = await client.get(
            f"/api/v1/chunks/{another_user_chunk.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_chunk_missing_auth(
        self: "TestGetChunk",
        client: AsyncClient,
    ):
        # Attempt to fetch a chunk without authorization
        response = await client.get("/api/v1/chunks/1/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestDeleteChunk:
    """DELETE /api/v1/chunks/{chunk_id}/"""

    async def test_delete_chunk(
        self: "TestDeleteChunk",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a chunk to delete later
        chunk = Chunk(
            content="This is a test chunk for deletion",
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(chunk)
        await session.commit()
        await session.refresh(chunk)

        # Delete the chunk
        response = await client.delete(
            f"/api/v1/chunks/{chunk.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify the chunk is deleted
        stmt = select(Chunk).where(Chunk.id == chunk.id)
        result = await session.execute(stmt)
        assert result.scalar() is None

    async def test_delete_chunk_not_found(
        self: "TestDeleteChunk",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Attempt to delete a chunk that does not exist
        response = await client.delete(
            "/api/v1/chunks/999999/",  # Assuming 999999 is an ID that does not exist
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_chunk_different_tenant(
        self: "TestDeleteChunk",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a chunk with a different tenant_id
        different_tenant_id = "different_tenant_id"
        chunk = Chunk(
            content="This chunk belongs to a different tenant",
            tenant_id=different_tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(chunk)
        await session.commit()
        await session.refresh(chunk)

        # Attempt to delete the chunk
        response = await client.delete(
            f"/api/v1/chunks/{chunk.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect unauthorized access error
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_chunk_different_user(
        self: "TestDeleteChunk",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a chunk with a different tenant_user_id
        other_user_id = "other_user_id"
        chunk = Chunk(
            content="This chunk belongs to another user",
            tenant_id=claims.tenant_id,
            tenant_user_id=other_user_id,
        )
        session.add(chunk)
        await session.commit()
        await session.refresh(chunk)

        # Attempt to delete the chunk
        response = await client.delete(
            f"/api/v1/chunks/{chunk.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Expect unauthorized access error
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_chunk_missing_auth(
        self: "TestDeleteChunk",
        client: AsyncClient,
    ):
        # Attempt to delete a chunk without providing an authorization token
        response = await client.delete("/api/v1/chunks/1/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestQueryChunks:
    """POST /api/v1/chunks/query/"""

    async def test_query_chunks(
        self: "TestQueryChunks",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create multiple chunks for testing
        chunk1 = Chunk(
            content="First query test chunk",
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        chunk2 = Chunk(
            content="Second query test chunk",
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(chunk1)
        session.add(chunk2)
        await session.commit()

        # Query chunks
        response = await client.post(
            "/api/v1/chunks/query/",
            headers={"Authorization": f"Bearer {token}"},
            json={"q": "query test"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # noqa: PLR2004
        assert data[0]["content"] == "First query test chunk"
        assert data[1]["content"] == "Second query test chunk"

    async def test_query_chunks_different_tenant(
        self: "TestQueryChunks",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a chunk for a different tenant
        different_tenant_chunk = Chunk(
            content="Different tenant chunk",
            tenant_id="different_tenant_id",
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(different_tenant_chunk)
        await session.commit()

        # Query chunks with the original tenant's token
        response = await client.post(
            "/api/v1/chunks/query/",
            headers={"Authorization": f"Bearer {token}"},
            json={"q": "tenant"},
        )

        # Since the chunk belongs to a different tenant, it should not be returned
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0  # Expecting no chunks

    async def test_query_chunks_different_user(
        self: "TestQueryChunks",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a chunk for the same tenant but different user
        different_user_chunk = Chunk(
            content="Different user chunk",
            tenant_id=claims.tenant_id,
            tenant_user_id="different_user_id",
        )
        session.add(different_user_chunk)
        await session.commit()

        # Query chunks with the original user's token
        response = await client.post(
            "/api/v1/chunks/query/",
            headers={"Authorization": f"Bearer {token}"},
            json={"q": "user"},
        )

        # Since the chunk belongs to the same tenant but a different user, it should not be returned
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0  # Expecting no chunks

    async def test_query_chunks_missing_auth(
        self: "TestQueryChunks",
        client: AsyncClient,
    ):
        # Attempt to query chunks without providing an authorization token
        response = await client.post("/api/v1/chunks/query/", json={"q": "query test"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_query_chunks_missing_body(
        self: "TestQueryChunks",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        # Attempt to query chunks without providing a body
        response = await client.post(
            "/api/v1/chunks/query/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_query_chunks_invalid_body(
        self: "TestQueryChunks",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        # Attempt to query chunks with an invalid body
        response = await client.post(
            "/api/v1/chunks/query/",
            headers={"Authorization": f"Bearer {token}"},
            json={"invalid_field": "Invalid data"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
