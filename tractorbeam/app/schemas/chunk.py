from pydantic import BaseModel


class ChunkSchemaBase(BaseModel):
    text: str
    document_id: int


class ChunkSchema(ChunkSchemaBase):
    id: int


class ChunkSchemaCreate(ChunkSchemaBase):
    pass
