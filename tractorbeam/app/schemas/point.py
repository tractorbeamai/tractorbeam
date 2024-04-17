from pydantic import BaseModel, ConfigDict


class PointBaseSchema(BaseModel):
    vector: list[float]

    model_config = ConfigDict(from_attributes=True)


class PointSchema(PointBaseSchema):
    id: int


class PointCreateSchema(PointBaseSchema):
    id: int


class PointQuerySchema(PointBaseSchema):
    limit: int = 10


class PointQueryResultSchema(BaseModel):
    id: int
    score: float

    model_config = ConfigDict(from_attributes=True)
