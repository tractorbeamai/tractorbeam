from pydantic import BaseModel


class IntegrationSchema(BaseModel):
    slug: str
    name: str
    logo_url: str | None
