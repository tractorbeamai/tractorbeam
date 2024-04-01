from typing import Annotated

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..exceptions import AppException
from ..integrations.oauth2_integration import OAuth2Integration
from ..integrations.registry import IntegrationRegistry, get_integration_registry
from ..models import Connection
from ..schemas.connection import (
    ConnectionCreateSchema,
    ConnectionSchema,
    ConnectionUpdateSchema,
)
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims


class ConnectionCRUD:
    def __init__(
        self,
        db: AsyncSession,
        registry: IntegrationRegistry,
        tenant_id: str,
        tenant_user_id: str,
    ):
        self.db = db
        self.registry = registry
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, item: ConnectionCreateSchema) -> Connection | None:
        Integration = self.registry.get(item.integration)  # noqa: N806

        # For some reason, sqlalchemy allows None to be saved into a
        # non-nullable JSON column. I think it is converting it to a JSON value
        # of "null", which is valid JSON and not a SQL Null, which are banned.
        # To sidestep this, we avoid adding the config=None kwarg to the model
        # init below, unless it isn't None. This lets the sqlalchemy default
        # run as expecting, inserting an empty dict.
        connection = Connection(
            integration=item.integration,
            tenant_id=self.tenant_id,
            tenant_user_id=self.tenant_user_id,
        )

        # There's a special case for OAuth, since we want to create the record before.
        if issubclass(Integration, OAuth2Integration):
            # follow OAuth2 process
            pass

        elif item.config and not Integration.validate_connection(item.config):
            raise AppException.ConnectionInvalid

        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)

        return await self.find_one(connection.id)

    async def find_one(self, item_id: int) -> Connection | None:
        stmt = select(Connection).where(
            (Connection.id == item_id)
            & (Connection.tenant_id == self.tenant_id)
            & (Connection.tenant_user_id == self.tenant_user_id),
        )
        return await self.db.scalar(stmt)

    async def find_all(self) -> list[Connection]:
        stmt = select(Connection).where(
            (Connection.tenant_id == self.tenant_id)
            & (Connection.tenant_user_id == self.tenant_user_id),
        )
        result = await self.db.scalars(stmt)
        return list(result)

    async def update(
        self,
        item_id: int,
        item: ConnectionUpdateSchema,
    ) -> Connection | None:
        connection = await self.find_one(item_id)
        if not connection:
            return None

        Integration = self.registry.get(connection.integration)  # noqa: N806
        if not Integration.validate_connection(item.config):
            raise AppException.ConnectionInvalid

        connection.config = item.config
        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def delete(self, item_id: int) -> bool:
        stmt = delete(Connection).where(
            (Connection.id == item_id)
            & (Connection.tenant_id == self.tenant_id)
            & (Connection.tenant_user_id == self.tenant_user_id),
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0


class ConnectionService:
    def __init__(self, connection_crud: ConnectionCRUD):
        self.connection_crud = connection_crud

    async def create(self, item: ConnectionCreateSchema) -> ConnectionSchema:
        connection = await self.connection_crud.create(item)
        if not connection:
            raise AppException.ConnectionCreationFailed
        return ConnectionSchema.model_validate(connection)

    async def find_one(self, item_id: int) -> ConnectionSchema:
        connection = await self.connection_crud.find_one(item_id)
        if not connection:
            raise AppException.ConnectionNotFound
        return ConnectionSchema.model_validate(connection)

    async def find_all(self) -> list[ConnectionSchema]:
        connections = await self.connection_crud.find_all()
        return [
            ConnectionSchema.model_validate(connection) for connection in connections
        ]

    async def update(
        self,
        item_id: int,
        item: ConnectionUpdateSchema,
    ) -> ConnectionSchema:
        connection = await self.connection_crud.update(item_id, item)
        if not connection:
            raise AppException.ConnectionNotFound
        return ConnectionSchema.model_validate(connection)

    async def delete(self, item_id: int) -> bool:
        result = await self.connection_crud.delete(item_id)
        if not result:
            raise AppException.ConnectionNotFound
        return result


def get_connection_crud(
    db: Annotated[AsyncSession, Depends(get_db)],
    registry: Annotated[IntegrationRegistry, Depends(get_integration_registry)],
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
):
    return ConnectionCRUD(db, registry, claims.tenant_id, claims.tenant_user_id)


def get_connection_service(
    connection_crud: Annotated[ConnectionCRUD, Depends(get_connection_crud)],
):
    return ConnectionService(connection_crud)
