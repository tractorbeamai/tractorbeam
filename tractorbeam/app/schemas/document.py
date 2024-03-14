from pydantic import BaseModel, ConfigDict

from .chunk import ChunkSchema


class DocumentSchemaBase(BaseModel):
    title: str | None = None
    content: str


class DocumentSchema(DocumentSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chunks: list[ChunkSchema]


class DocumentSchemaCreate(DocumentSchemaBase):
    pass
