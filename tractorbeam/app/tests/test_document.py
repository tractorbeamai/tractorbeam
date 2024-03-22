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
        f"/documents/{document.id}/",
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
async def test_get_document_not_found(
    client: AsyncClient,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, _ = token_with_claims

    resp = await client.get(
        "/documents/999999/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_get_document_not_owned(
    client: AsyncClient,
    session: AsyncSession,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims

    # Create a document owned by another user
    another_user_document = Document(
        title="Another User's Document",
        content="This document is owned by another user.",
        tenant_id=claims.tenant_id,
        tenant_user_id="another_user_id",  # Assuming a different user ID
    )
    session.add(another_user_document)
    await session.commit()
    await session.refresh(another_user_document)

    # Attempt to fetch the document not owned by the token's user
    resp = await client.get(
        f"/documents/{another_user_document.id}/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_get_documents(
    client: AsyncClient,
    session: AsyncSession,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, claims = token_with_claims

    # Create a document
    document = Document(
        title="Test Document for Get All",
        content="This is a test document content for get all.",
        tenant_id=claims.tenant_id,
        tenant_user_id=claims.tenant_user_id,
        chunks=[
            Chunk(
                content="This is a test document content for get all.",
                tenant_id=claims.tenant_id,
                tenant_user_id=claims.tenant_user_id,
            ),
        ],
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    # Fetch all documents
    resp = await client.get(
        "/documents/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert len(data) >= 1  # Ensure at least one document is returned
    found = False
    for doc in data:
        if doc["id"] == document.id:
            assert doc["title"] == "Test Document for Get All"
            assert doc["content"] == "This is a test document content for get all."
            found = True
            break
    assert found  # Ensure the created document is in the returned list


@pytest.mark.asyncio()
async def test_get_documents_not_found(
    client: AsyncClient,
    token_with_claims: tuple[str, TokenClaimsSchema],
):
    token, _ = token_with_claims

    resp = await client.get(
        "/documents/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert len(data) == 0  # Ensure no documents are returned


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

    resp = await client.post(
        "/documents/query/",
        headers={"Authorization": f"Bearer {token}"},
        json={"q": "hello world"},
    )

    assert resp.status_code == status.HTTP_200_OK
    chunks = resp.json()
    assert len(chunks) == 1
