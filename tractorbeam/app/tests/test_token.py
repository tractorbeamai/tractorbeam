import datetime

import jwt
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_token(async_client: AsyncClient, api_key: str):
    claims = {
        "tenant_id": "abc-123",
        "tenant_user_id": "def-456",
    }

    resp = await async_client.post(
        "/token/",
        headers={"X-API-Key": api_key},
        json=claims,
    )
    assert resp.status_code == 200

    data = resp.json()
    assert "token" in data


@pytest.mark.asyncio
async def test_create_token_invalid_api_key(async_client: AsyncClient):
    resp = await async_client.post(
        "/token/",
        headers={"X-API-Key": "invalid-key"},
        json={"tenant_id": "abc-123", "tenant_user_id": "def-456"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_token_expiration_time(async_client: AsyncClient, api_key: str):
    claims = {
        "tenant_id": "abc-123",
        "tenant_user_id": "def-456",
    }

    resp = await async_client.post(
        "/token/",
        headers={"X-API-Key": api_key},
        json=claims,
    )
    assert resp.status_code == 200

    data = resp.json()
    token = data["token"]

    decoded_token = jwt.decode(token, options={"verify_signature": False})
    assert "exp" in decoded_token

    expiration_time = datetime.datetime.fromtimestamp(
        decoded_token["exp"], tz=datetime.timezone.utc
    )
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    assert (expiration_time - now) < datetime.timedelta(
        days=1, seconds=5 * 60
    )  # Allowing a 5 minute leeway
    assert (expiration_time - now) > datetime.timedelta(
        days=1, seconds=-5 * 60
    )  # Allowing a 5 minute leeway
