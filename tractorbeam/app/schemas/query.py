from pydantic import BaseModel


class QuerySchema(BaseModel):
    q: str


class QueryResultSchema(BaseModel):
    content: str
    score: float
