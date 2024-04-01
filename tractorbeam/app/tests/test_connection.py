import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Connection, ConnectionStatus
from ..schemas.token import TokenClaimsSchema


@pytest.mark.asyncio()
class TestConnectionCreate:
    """POST /api/v1/connections/"""

    async def test_create_connection(
        self: "TestConnectionCreate",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims
        response = await client.post(
            "/api/v1/connections/",
            headers={"Authorization": f"Bearer {token}"},
            json={"integration": "mock_oauth2"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["integration"] == "mock_oauth2"
        assert data["status"] == "PENDING"

        stmt = select(Connection).where(Connection.id == data["id"])
        db_connection = await session.scalar(stmt)
        assert db_connection is not None
        assert db_connection.integration == "mock_oauth2"
        assert db_connection.status == ConnectionStatus.PENDING
        assert db_connection.tenant_id == claims.tenant_id
        assert db_connection.tenant_user_id == claims.tenant_user_id

    @pytest.mark.parametrize(
        "request_body",
        [
            ({"invalid_key": "invalid_value"}),
            ({"integration": "nonexistent", "extra_field": "extra_value"}),
            (None),
            (""),
        ],
    )
    async def test_create_connection_invalid_body(
        self: "TestConnectionCreate",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
        request_body,
    ):
        token, _ = token_with_claims
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            "/api/v1/connections/",
            headers=headers,
            json=request_body,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_connection_invalid_integration(
        self: "TestConnectionCreate",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims
        response = await client.post(
            "/api/v1/connections/",
            headers={"Authorization": f"Bearer {token}"},
            json={"integration": "nonexistent"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_connection_missing_auth(
        self: "TestConnectionCreate",
        client: AsyncClient,
    ):
        response = await client.post(
            "/api/v1/connections/",
            json={"integration": "mock_oauth2"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
class TestGetConnections:
    """GET /api/v1/connections/"""

    async def test_get_connections(
        self: "TestGetConnections",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection_a = Connection(
            integration="mock_oauth2",
            config={"access_token": "abc", "refresh_token": "def"},
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection_a)
        connection_b = Connection(
            integration="mock_oauth2",
            config={"access_token": "ghi", "refresh_token": "jkl"},
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection_b)
        await session.commit()
        await session.refresh(connection_a)
        await session.refresh(connection_b)

        response = await client.get(
            "/api/v1/connections/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2
        assert any(
            conn["integration"] == "mock_oauth2"
            and conn["config"]["access_token"] == "abc"
            for conn in data
        )
        assert any(
            conn["integration"] == "mock_oauth2"
            and conn["config"]["access_token"] == "ghi"
            for conn in data
        )

    async def test_get_connections_not_found(
        self: "TestGetConnections",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.get(
            "/api/v1/connections/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    async def test_get_connections_different_tenant(
        self: "TestGetConnections",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "xyz", "refresh_token": "uvw"},
            tenant_id="different_tenant_id",
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection)
        await session.commit()

        response = await client.get(
            "/api/v1/connections/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(conn["tenant_id"] == claims.tenant_id for conn in data)

    async def test_get_connections_different_user(
        self: "TestGetConnections",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "xyz", "refresh_token": "uvw"},
            tenant_id=claims.tenant_id,
            tenant_user_id="different_tenant_user_id",
        )
        session.add(connection)
        await session.commit()

        response = await client.get(
            "/api/v1/connections/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(conn["tenant_user_id"] == claims.tenant_user_id for conn in data)

    async def test_get_connections_missing_auth(
        self: "TestGetConnections",
        client: AsyncClient,
    ):
        response = await client.get("/api/v1/connections/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetConnection:
    """GET /api/v1/connections/{connection_id}"""

    async def test_get_connection(
        self: "TestGetConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "abc", "refresh_token": "def"},
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection)
        await session.commit()
        await session.refresh(connection)

        response = await client.get(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == connection.id
        assert data["integration"] == "mock_oauth2"
        assert "tenant_id" not in data
        assert "tenant_user_id" not in data

    async def test_get_connection_not_found(
        self: "TestGetConnection",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.get(
            "/api/v1/connections/999999/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_connection_different_tenant(
        self: "TestGetConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "ghi", "refresh_token": "jkl"},
            tenant_id="different_tenant_id",
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection)
        await session.commit()

        response = await client.get(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_connection_different_user(
        self: "TestGetConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "mno", "refresh_token": "pqr"},
            tenant_id=claims.tenant_id,
            tenant_user_id="different_user_id",
        )
        session.add(connection)
        await session.commit()

        response = await client.get(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_connection_missing_auth(
        self: "TestGetConnection",
        client: AsyncClient,
    ):
        response = await client.get(
            "/api/v1/connections/1/",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateConnection:
    """PUT /api/v1/connections/{connection_id}"""

    async def test_update_connection(
        self: "TestUpdateConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "abc", "refresh_token": "def"},
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection)
        await session.commit()

        response = await client.put(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "config": {"access_token": "xyz", "refresh_token": "uvw"},
            },
        )

        assert response.status_code == status.HTTP_200_OK
        updated_connection = response.json()
        assert updated_connection["config"]["access_token"] == "xyz"
        assert updated_connection["config"]["refresh_token"] == "uvw"

    @pytest.mark.parametrize(
        "invalid_config",
        [
            ("invalid_config_format"),
            ({"missing_access_token": "xyz"}),
            ({"access_token": 123, "refresh_token": 456}),
            ({"integration": "new_integration"}),
            ({}),
            (None),
        ],
    )
    async def test_update_connection_invalid_body(
        self: "TestUpdateConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
        invalid_config,
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "abc", "refresh_token": "def"},
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection)
        await session.commit()

        response = await client.put(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "config": invalid_config,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_connection_not_found(
        self: "TestUpdateConnection",
        client: AsyncClient,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.put(
            "/api/v1/connections/999999/",
            headers={"Authorization": f"Bearer {token}"},
            json={"config": {"access_token": "nonexistent"}},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_connection_different_tenant(
        self: "TestUpdateConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "ghi", "refresh_token": "jkl"},
            tenant_id="different_tenant_id",
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection)
        await session.commit()

        response = await client.put(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
            json={"config": {"access_token": "should_not_update"}},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_connection_different_user(
        self: "TestUpdateConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "mno", "refresh_token": "pqr"},
            tenant_id=claims.tenant_id,
            tenant_user_id="different_user_id",
        )
        session.add(connection)
        await session.commit()

        response = await client.put(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
            json={"config": {"access_token": "should_not_update"}},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_connection_missing_auth(
        self: "TestUpdateConnection",
        client: AsyncClient,
    ):
        response = await client.put(
            "/api/v1/connections/1/",
            json={"config": {"access_token": "no_auth"}},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteConnection:
    """DELETE /api/v1/connections/{connection_id}"""

    async def test_delete_connection(
        self: "TestDeleteConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "abc", "refresh_token": "def"},
            tenant_id=claims.tenant_id,
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection)
        await session.commit()

        response = await client.delete(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        stmt = select(Connection).where(Connection.id == connection.id)
        deleted_connection = await session.scalar(stmt)
        assert deleted_connection is None

    async def test_delete_connection_not_found(
        self: "TestDeleteConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, _ = token_with_claims

        response = await client.delete(
            "/api/v1/connections/999999/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_connection_different_tenant(
        self: "TestDeleteConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "xyz", "refresh_token": "uvw"},
            tenant_id="different_tenant_id",
            tenant_user_id=claims.tenant_user_id,
        )
        session.add(connection)
        await session.commit()

        response = await client.delete(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_connection_different_user(
        self: "TestDeleteConnection",
        client: AsyncClient,
        session: AsyncSession,
        token_with_claims: tuple[str, TokenClaimsSchema],
    ):
        token, claims = token_with_claims

        connection = Connection(
            integration="mock_oauth2",
            config={"access_token": "xyz", "refresh_token": "uvw"},
            tenant_id=claims.tenant_id,
            tenant_user_id="different_user_id",
        )
        session.add(connection)
        await session.commit()

        response = await client.delete(
            f"/api/v1/connections/{connection.id}/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_connection_missing_auth(
        self: "TestDeleteConnection",
        client: AsyncClient,
        session: AsyncSession,
    ):
        response = await client.delete("/api/v1/connections/1/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
