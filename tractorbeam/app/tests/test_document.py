import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Chunk, Document
from ..schemas.token import TokenClaimsSchema


@pytest.mark.asyncio()
async def test_create_document(
    client: AsyncClient,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, _ = token_with_claims

    resp = await client.post(
        "/documents/",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Hello World Document", "content": "hello world\nchunk 2"},
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "id" in data
    assert "content" in data
    assert "chunks" in data


@pytest.mark.asyncio()
async def test_query_documents(
    client: AsyncClient,
    session: AsyncSession,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims

    document = Document(
        title="Hello World Document",
        content="hello world\nchunk 2",
        tenant_id=claims.tenant_id,
        tenant_user_id=claims.tenant_user_id,
        chunks=[
            Chunk(
                content="hello world",
                tenant_id=claims.tenant_id,
                tenant_user_id=claims.tenant_user_id,
            ),
            Chunk(
                content="chunk 2",
                tenant_id=claims.tenant_id,
                tenant_user_id=claims.tenant_user_id,
            ),
        ],
    )
    session.add(document)
    await session.commit()

    resp = await client.get(
        "/documents/",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": "hello world"},
    )

    assert resp.status_code == status.HTTP_200_OK
    chunks = resp.json()
    assert len(chunks) > 0


@pytest.mark.asyncio()
async def test_get_document(
    client: AsyncClient,
    session: AsyncSession,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims

    # Create a document to fetch later
    document = Document(
        title="Test Document for Get",
        content="This is a test document content.",
        tenant_id=claims.tenant_id,
        tenant_user_id=claims.tenant_user_id,
        chunks=[
            Chunk(
                content="This is a test document content.",
                tenant_id=claims.tenant_id,
                tenant_user_id=claims.tenant_user_id,
            ),
        ],
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    # Fetch the document
    resp = await client.get(
        f"/documents/{document.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["title"] == "Test Document for Get"
    assert data["content"] == "This is a test document content."
    assert "chunks" in data
    assert len(data["chunks"]) == 1
    assert data["chunks"][0]["content"] == "This is a test document content."


@pytest.mark.asyncio()
async def test_delete_document(
    client: AsyncClient,
    session: AsyncSession,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims

    document = Document(
        title="Hello World Document",
        content="hello world\nchunk 2",
        tenant_id=claims.tenant_id,
        tenant_user_id=claims.tenant_user_id,
        chunks=[
            Chunk(
                content="hello world",
                tenant_id=claims.tenant_id,
                tenant_user_id=claims.tenant_user_id,
            ),
            Chunk(
                content="chunk 2",
                tenant_id=claims.tenant_id,
                tenant_user_id=claims.tenant_user_id,
            ),
        ],
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    resp = await client.delete(
        f"/documents/{document.id}/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == status.HTTP_200_OK

    stmt = select(Document).where(Document.id == document.id)
    result = await session.execute(stmt)
    assert result.scalar() is None
