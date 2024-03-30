from pydantic import BaseModel, ConfigDict


class ChunkBaseSchema(BaseModel):
    content: str
    document_id: int | None = None


class ChunkSchema(ChunkBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ChunkCreateSchema(ChunkBaseSchema):
    pass
