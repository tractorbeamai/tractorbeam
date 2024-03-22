import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Chunk
from ..schemas.token import TokenClaimsSchema


@pytest.mark.asyncio()
async def test_create_chunk(
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


@pytest.mark.asyncio()
async def test_get_chunks(
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
        "/chunks/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2  # Expecting two chunks
    assert data[0]["content"] == "First test chunk"
    assert data[1]["content"] == "Second test chunk"


@pytest.mark.asyncio()
async def test_get_chunk(
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
        f"/chunks/{chunk.id}/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "This is a test chunk"


@pytest.mark.asyncio()
async def test_get_chunk_not_found(
    client: AsyncClient,
    session: AsyncSession,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims

    response = await client.get(
        "/chunks/1/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_get_chunk_not_owned(
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
        f"/chunks/{another_user_chunk.id}/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_delete_chunk(
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
        f"/chunks/{chunk.id}/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify the chunk is deleted
    stmt = select(Chunk).where(Chunk.id == chunk.id)
    result = await session.execute(stmt)
    assert result.scalar() is None


@pytest.mark.asyncio()
async def test_delete_chunk_not_found(
    client: AsyncClient,
    session: AsyncSession,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims

    # Attempt to delete a chunk that does not exist
    response = await client.delete(
        "/chunks/999999/",  # Assuming 999999 is an ID that does not exist
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_delete_chunk_not_owned(
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
        f"/chunks/{chunk.id}/",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Expect unauthorized access error
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_query_chunks(
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
        "/chunks/query/",
        headers={"Authorization": f"Bearer {token}"},
        json={"q": "query test"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2  # Expecting two chunks
    assert data[0]["content"] == "First query test chunk"
    assert data[1]["content"] == "Second query test chunk"
