from pydantic import BaseModel


class DocumentSchemaBase(BaseModel):
    title: str | None = None


class DocumentSchema(DocumentSchemaBase):
    id: int


class DocumentSchemaCreate(DocumentSchemaBase):
    text: str
