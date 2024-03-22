from pydantic import BaseModel


class Query(BaseModel):
    q: str


class QueryResult(BaseModel):
    content: str
    score: float
