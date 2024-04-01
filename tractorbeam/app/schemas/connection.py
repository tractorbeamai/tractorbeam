from pydantic import BaseModel, ConfigDict

from ..models import ConnectionStatus


class ConnectionBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ConnectionSchema(ConnectionBaseSchema):
    id: int
    integration: str
    config: dict
    status: ConnectionStatus


class ConnectionCreateSchema(ConnectionBaseSchema):
    integration: str
    config: dict | None = None

    model_config = ConfigDict(extra="forbid")


class ConnectionUpdateSchema(ConnectionBaseSchema):
    config: dict

    model_config = ConfigDict(extra="forbid")
