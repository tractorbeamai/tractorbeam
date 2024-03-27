from typing import Annotated

import pytest
from fastapi import Depends, status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..main import app
from ..models import Chunk, Document
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims
from ..services.document import DocumentCRUD, get_document_crud


@pytest.mark.asyncio()
class TestCreateDocument:
    """POST /api/v1/documents/"""

    async def test_create_document(
        self: "TestCreateDocument",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.post(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Hello World Document", "content": "hello world\nchunk 2"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "content" in data
        assert "chunks" in data

    @pytest.fixture()
    def _override_get_document_crud_broken_create(self: "TestCreateDocument"):
        class BrokenCreateDocumentCRUD(DocumentCRUD):
            async def create(self, *_args, **_kwargs):
                return None

        def get_broken_create_document_crud(
            db: Annotated[AsyncSession, Depends(get_db)],
            claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
        ):
            return BrokenCreateDocumentCRUD(db, claims.tenant_id, claims.tenant_user_id)

        app.dependency_overrides[get_document_crud] = get_broken_create_document_crud

        yield

        del app.dependency_overrides[get_document_crud]

    @pytest.mark.usefixtures("_override_get_document_crud_broken_create")
    async def test_create_document_crud_create_error(
        self: "TestCreateDocument",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.post(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Failed Document", "content": "This should not be created"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.fixture()
    def _override_get_document_crud_broken_find_one(
        self: "TestCreateDocument",
    ):
        class BrokenFindDocumentCRUD(DocumentCRUD):
            async def find_one(self, _item_id: int):
                return None

        def get_broken_find_document_crud(
            db: Annotated[AsyncSession, Depends(get_db)],
            claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
        ):
            return BrokenFindDocumentCRUD(db, claims.tenant_id, claims.tenant_user_id)

        app.dependency_overrides[get_document_crud] = get_broken_find_document_crud

        yield

        del app.dependency_overrides[get_document_crud]

    @pytest.mark.usefixtures("_override_get_document_crud_broken_find_one")
    async def test_create_document_crud_find_error(
        self: "TestCreateDocument",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.post(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Failed Document", "content": "This should not be created"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    async def test_create_document_missing_body(
        self: "TestCreateDocument",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.post(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_document_invalid_body(
        self: "TestCreateDocument",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.post(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
            json={"invalid_field": "Invalid data"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_document_missing_auth(
        self: "TestCreateDocument",
        client: AsyncClient,
    ):
        response = await client.post(
            "/api/v1/documents/",
            json={
                "title": "Unauthorized Document",
                "content": "This should not be created",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestGetDocuments:
    """GET /api/v1/documents/"""

    async def test_get_documents(
        self: "TestGetDocuments",
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
        response = await client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1  # Ensure at least one document is returned
        found = False
        for doc in data:
            if doc["id"] == document.id:
                assert doc["title"] == "Test Document for Get All"
                assert doc["content"] == "This is a test document content for get all."
                found = True
                break
        assert found  # Ensure the created document is in the returned list

    async def test_get_documents_not_found(
        self: "TestGetDocuments",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0  # Ensure no documents are returned

    async def test_get_documents_different_tenant(
        self: "TestGetDocuments",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a document with a different tenant_id
        document = Document(
            title="Different Tenant Document",
            content="This document belongs to a different tenant.",
            tenant_id="different_tenant_id",
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(document)
        await session.commit()

        # Attempt to fetch documents
        response = await client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(
            doc["tenant_id"] == claims.tenant_id for doc in data
        )  # Ensure no documents from different tenants are returned

    async def test_get_documents_different_user(
        self: "TestGetDocuments",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a document with a different tenant_user_id
        document = Document(
            title="Different User Document",
            content="This document belongs to a different user.",
            tenant_id=claims.tenant_id,
            tenant_user_id="different_user_id",
        )
        session.add(document)
        await session.commit()

        # Attempt to fetch documents
        response = await client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(
            doc["tenant_user_id"] == claims.tenant_user_id for doc in data
        )  # Ensure no documents from different users are returned

    async def test_get_documents_missing_auth(
        self: "TestGetDocuments",
        client: AsyncClient,
    ):
        # Attempt to fetch documents without authorization
        response = await client.get("/api/v1/documents/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestGetDocument:
    """GET /api/v1/documents/{document_id}/"""

    async def test_get_document(
        self: "TestGetDocument",
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
        response = await client.get(
            f"/api/v1/documents/{document.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Test Document for Get"
        assert data["content"] == "This is a test document content."
        assert "chunks" in data
        assert len(data["chunks"]) == 1
        assert data["chunks"][0]["content"] == "This is a test document content."

    async def test_get_document_not_found(
        self: "TestGetDocument",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.get(
            "/api/v1/documents/999999/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_document_different_tenant(
        self: "TestGetDocument",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a document owned by another tenant
        another_tenant_document = Document(
            title="Another Tenant's Document",
            content="This document is owned by another tenant.",
            tenant_id="another_tenant_id",  # Assuming a different tenant ID
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(another_tenant_document)
        await session.commit()
        await session.refresh(another_tenant_document)

        # Attempt to fetch the document not owned by the token's tenant
        response = await client.get(
            f"/api/v1/documents/{another_tenant_document.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_document_different_user(
        self: "TestGetDocument",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a document owned by another user within the same tenant
        another_user_document = Document(
            title="Another User's Document",
            content="This document is owned by another user within the same tenant.",
            tenant_id=claims.tenant_id,
            tenant_user_id="another_user_id",  # Assuming a different user ID
        )
        session.add(another_user_document)
        await session.commit()
        await session.refresh(another_user_document)

        # Attempt to fetch the document not owned by the token's user but within the same tenant
        response = await client.get(
            f"/api/v1/documents/{another_user_document.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_document_missing_auth(
        self: "TestGetDocument",
        client: AsyncClient,
    ):
        # Attempt to fetch a document without authorization
        response = await client.get("/api/v1/documents/1/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestDeleteDocument:
    """DELETE /api/v1/documents/{document_id}/"""

    async def test_delete_document(
        self: "TestDeleteDocument",
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

        response = await client.delete(
            f"/api/v1/documents/{document.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        stmt = select(Document).where(Document.id == document.id)
        result = await session.execute(stmt)
        assert result.scalar() is None

    async def test_delete_document_different_tenant(
        self: "TestDeleteDocument",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a document owned by another tenant
        another_tenant_document = Document(
            title="Another Tenant's Document",
            content="This document is owned by another tenant.",
            tenant_id="another_tenant_id",  # Assuming a different tenant ID
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(another_tenant_document)
        await session.commit()
        await session.refresh(another_tenant_document)

        # Attempt to delete the document not owned by the token's tenant
        response = await client.delete(
            f"/api/v1/documents/{another_tenant_document.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_document_different_user(
        self: "TestDeleteDocument",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        # Create a document owned by another user within the same tenant
        another_user_document = Document(
            title="Another User's Document",
            content="This document is owned by another user within the same tenant.",
            tenant_id=claims.tenant_id,
            tenant_user_id="another_user_id",  # Assuming a different user ID
        )
        session.add(another_user_document)
        await session.commit()
        await session.refresh(another_user_document)

        # Attempt to delete the document not owned by the token's user but within the same tenant
        response = await client.delete(
            f"/api/v1/documents/{another_user_document.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_document_missing_auth(
        self: "TestDeleteDocument",
        client: AsyncClient,
        session: AsyncSession,
    ):
        # Create a document to attempt to delete without authorization
        document = Document(
            title="Unauthorized Delete Attempt",
            content="This document should not be deletable without proper authorization.",
            tenant_id="test_tenant_id",
            tenant_user_id="test_tenant_user_id",
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

        # Attempt to delete the document without providing an authorization token
        response = await client.delete(
            f"/api/v1/documents/{document.id}/",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestQueryDocuments:
    """POST /api/v1/documents/query/"""

    async def test_query_documents(
        self: "TestQueryDocuments",
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

        response = await client.post(
            "/api/v1/documents/query/",
            headers={"Authorization": f"Bearer {token}"},
            json={"q": "hello world"},
        )

        assert response.status_code == status.HTTP_200_OK
        chunks = response.json()
        assert len(chunks) == 1

    async def test_query_documents_missing_auth(
        self: "TestQueryDocuments",
        client: AsyncClient,
    ):
        response = await client.post(
            "/api/v1/documents/query/",
            json={"q": "hello world"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_query_documents_missing_body(
        self: "TestQueryDocuments",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.post(
            "/api/v1/documents/query/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_query_documents_invalid_body(
        self: "TestQueryDocuments",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.post(
            "/api/v1/documents/query/",
            headers={"Authorization": f"Bearer {token}"},
            json={"invalid_field": "Invalid data"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
