from pydantic import BaseModel, ConfigDict

from .chunk import ChunkSchema


class DocumentBaseSchema(BaseModel):
    title: str | None = None
    content: str


class DocumentSchema(DocumentBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chunks: list[ChunkSchema]


class DocumentCreateSchema(DocumentBaseSchema):
    model_config = ConfigDict(extra="forbid")
