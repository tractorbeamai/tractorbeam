from pydantic import BaseModel


class QueryResult(BaseModel):
    content: str
    score: float
