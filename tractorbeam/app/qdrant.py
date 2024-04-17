from qdrant_client import AsyncQdrantClient, models

from .settings import get_settings

client = AsyncQdrantClient(
    url=get_settings().qdrant_url,
    port=get_settings().qdrant_port,
)


async def ensure_collection(collection_name: str) -> None:
    collection_exists = await client.collection_exists(collection_name=collection_name)
    if collection_exists:
        return

    await client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "text-dense": models.VectorParams(
                size=1024,
                distance=models.Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "text-sparse": models.SparseVectorParams(),
        },
        hnsw_config={
            "m": 0,  # disable global index
            "payload_m": 16,  # configure payload index
        },
    )

    await client.create_payload_index(
        collection_name=collection_name,
        field_name="tenant_id",
        field_schema="keyword",
    )

    await client.create_payload_index(
        collection_name=collection_name,
        field_name="tenant_user_id",
        field_schema="keyword",
    )


def get_qdrant_client() -> AsyncQdrantClient:
    return client
