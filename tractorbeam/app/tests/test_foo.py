import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_foo_item(async_session: AsyncSession, async_client: AsyncClient):
    resp = await async_client.post(
        "/api/v1/foo/item/",
        json={"description": "test description", "public": False},
    )
    assert resp.status_code == 200

    content = resp.json()

    assert "id" in content
    assert content["description"] == "test description"
    assert not content["public"]
