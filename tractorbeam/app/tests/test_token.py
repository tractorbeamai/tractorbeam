import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio()
class TestCreateToken:
    async def test_create_token(self, client: AsyncClient, api_key: str):
        claims = {
            "tenant_id": "abc-123",
            "tenant_user_id": "def-456",
        }

        resp = await client.post(
            "/token/",
            headers={"X-API-Key": api_key},
            json=claims,
        )
        assert resp.status_code == status.HTTP_200_OK

        data = resp.json()
        assert "token" in data

    async def test_create_token_invalid_api_key(self, client: AsyncClient):
        resp = await client.post(
            "/token/",
            headers={"X-API-Key": "invalid-key"},
            json={"tenant_id": "abc-123", "tenant_user_id": "def-456"},
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    async def test_create_token_missing_api_key(self, client: AsyncClient):
        claims = {
            "tenant_id": "abc-123",
            "tenant_user_id": "def-456",
        }

        resp = await client.post(
            "/token/",
            json=claims,
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    async def test_create_token_invalid_claims(self, client: AsyncClient, api_key: str):
        claims = {
            "not-a-claim": "abc-123",
        }

        resp = await client.post(
            "/token/",
            headers={"X-API-Key": api_key},
            json=claims,
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio()
class TestUseToken:
    async def test_use_token(self, client: AsyncClient, api_key: str):
        claims = {
            "tenant_id": "abc-123",
            "tenant_user_id": "def-456",
        }

        resp = await client.post(
            "/token/",
            headers={"X-API-Key": api_key},
            json=claims,
        )
        assert resp.status_code == status.HTTP_200_OK

        data = resp.json()
        token = data["token"]

        resp = await client.get(
            "/documents/",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": "hello world"},
        )
        assert resp.status_code == status.HTTP_200_OK

    async def test_use_missing_token(self, client: AsyncClient):
        resp = await client.get(
            "/documents/",
            params={"q": "hello world"},
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    async def test_use_invalid_token(self, client: AsyncClient):
        token = "not-a-real-token"

        resp = await client.get(
            "/documents/",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": "hello world"},
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
