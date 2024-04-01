from pydantic import BaseModel, ConfigDict, Field


class QuerySchema(BaseModel):
    q: str = Field(..., min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class QueryResultSchema(BaseModel):
    content: str
    score: float
