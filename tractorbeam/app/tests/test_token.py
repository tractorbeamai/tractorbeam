import datetime

import pytest
from fastapi import status
from httpx import AsyncClient

from ..schemas.token import TokenClaimsSchema
from ..services.token import TokenService
from ..settings import get_settings


@pytest.mark.asyncio()
class TestCreateToken:
    async def test_create_token(
        self: "TestCreateToken",
        client: AsyncClient,
        api_key: str,
    ):
        claims = {
            "tenant_id": "abc-123",
            "tenant_user_id": "def-456",
        }

        resp = await client.post(
            "/api/v1/token/",
            headers={"X-API-Key": api_key},
            json=claims,
        )
        assert resp.status_code == status.HTTP_200_OK

        data = resp.json()
        assert "token" in data

    async def test_create_token_invalid_api_key(
        self: "TestCreateToken",
        client: AsyncClient,
    ):
        resp = await client.post(
            "/api/v1/token/",
            headers={"X-API-Key": "invalid-key"},
            json={"tenant_id": "abc-123", "tenant_user_id": "def-456"},
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    async def test_create_token_missing_api_key(
        self: "TestCreateToken",
        client: AsyncClient,
    ):
        claims = {
            "tenant_id": "abc-123",
            "tenant_user_id": "def-456",
        }

        resp = await client.post(
            "/api/v1/token/",
            json=claims,
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    async def test_create_token_invalid_claims(
        self: "TestCreateToken",
        client: AsyncClient,
        api_key: str,
    ):
        claims = {
            "not-a-claim": "abc-123",
        }

        resp = await client.post(
            "/api/v1/token/",
            headers={"X-API-Key": api_key},
            json=claims,
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio()
class TestUseToken:
    async def test_use_token(
        self: "TestUseToken",
        client: AsyncClient,
        api_key: str,
    ):
        claims = {
            "tenant_id": "abc-123",
            "tenant_user_id": "def-456",
        }

        resp = await client.post(
            "/api/v1/token/",
            headers={"X-API-Key": api_key},
            json=claims,
        )
        assert resp.status_code == status.HTTP_200_OK

        data = resp.json()
        token = data["token"]

        resp = await client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": "hello world"},
        )
        assert resp.status_code == status.HTTP_200_OK

    async def test_use_missing_token(
        self: "TestUseToken",
        client: AsyncClient,
    ):
        resp = await client.get(
            "/api/v1/documents/",
            params={"q": "hello world"},
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    async def test_use_invalid_token(
        self: "TestUseToken",
        client: AsyncClient,
    ):
        token = "not-a-real-token"

        resp = await client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": "hello world"},
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    async def test_use_expired_token(
        self: "TestUseToken",
        client: AsyncClient,
    ):
        settings = get_settings()
        secret = settings.secret

        # Create an expired token using the TokenService
        token_service = TokenService()
        claims = TokenClaimsSchema(
            tenant_id="abc-123",
            tenant_user_id="def-456",
            iat=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=2),
            exp=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1),
        )
        token_schema = await token_service.create(claims, secret)
        expired_token = token_schema.token

        resp = await client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {expired_token}"},
            params={"q": "hello world"},
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
