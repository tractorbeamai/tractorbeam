from typing import Annotated

from fastapi import Depends
from openai import OpenAI

from ..settings import Settings, get_settings


class EmbeddingService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def get_dense_embedding(self, text: str) -> list[float]:
        result = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-large",
            dimensions=1024,
        )

        return result.data[0].embedding


class FakeEmbeddingService:
    def get_dense_embedding(self, text: str) -> list[float]:
        return [0.0] * 1024


def get_embedding_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmbeddingService:
    return EmbeddingService(settings.openai_api_key)
