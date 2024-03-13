from typing import Tuple

import pytest
from httpx import AsyncClient

from ..schemas.token import TokenClaimsSchema


@pytest.mark.asyncio
async def test_create_document(
    async_client: AsyncClient, token_with_claims: Tuple[str, TokenClaimsSchema]
):
    token, _ = token_with_claims

    resp = await async_client.post(
        "/documents/",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "hello world"},
    )

    print(resp.json())
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert "chunks" in data
