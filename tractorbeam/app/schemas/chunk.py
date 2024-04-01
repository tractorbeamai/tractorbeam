from pydantic import BaseModel, ConfigDict


class ChunkBaseSchema(BaseModel):
    content: str
    document_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ChunkSchema(ChunkBaseSchema):
    id: int


class ChunkCreateSchema(ChunkBaseSchema):
    model_config = ConfigDict(extra="forbid")
