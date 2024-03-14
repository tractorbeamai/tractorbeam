from pydantic import BaseModel, ConfigDict


class ChunkSchemaBase(BaseModel):
    content: str
    document_id: int | None = None


class ChunkSchema(ChunkSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ChunkSchemaCreate(ChunkSchemaBase):
    pass
