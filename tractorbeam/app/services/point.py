from typing import Annotated

from fastapi import Depends
from qdrant_client import AsyncQdrantClient, models

from ..exceptions import AppException
from ..qdrant import get_qdrant_client
from ..schemas.point import (
    PointCreateSchema,
    PointQueryResultSchema,
    PointQuerySchema,
    PointSchema,
)
from ..schemas.token import TokenClaimsSchema
from ..security import get_token_claims
from ..settings import Settings, get_settings


class PointCRUD:
    def __init__(
        self,
        qdrant: AsyncQdrantClient,
        collection_name: str,
        tenant_id: str,
        tenant_user_id: str,
    ) -> None:
        self.qdrant = qdrant
        self.collection_name = collection_name
        self.tenant_id = tenant_id
        self.tenant_user_id = tenant_user_id

    async def create(self, item: PointCreateSchema) -> bool:
        # try:
        await self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=item.id,
                    vector={
                        "text-dense": item.vector,
                    },
                    payload={
                        "tenant_id": self.tenant_id,
                        "tenant_user_id": self.tenant_user_id,
                    },
                ),
            ],
        )
        # except:
        # return False
        return True

    async def query(self, item: PointQuerySchema) -> list[PointQueryResultSchema]:
        try:
            query_results = await self.qdrant.search(
                collection_name=self.collection_name,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="tenant_id",
                            match=models.MatchValue(
                                value=self.tenant_id,
                            ),
                        ),
                        models.FieldCondition(
                            key="tenant_user_id",
                            match=models.MatchValue(
                                value=self.tenant_user_id,
                            ),
                        ),
                    ],
                ),
                query_vector=models.NamedVector(
                    name="text-dense",
                    vector=item.vector,
                ),
                limit=item.limit,
            )
        except Exception as e:
            print(e)
            raise AppException.PointQueryFailed from e

        return [
            PointQueryResultSchema(
                id=int(result.id),
                score=result.score,
            )
            for result in query_results
            if result.payload
            and result.payload.get("tenant_id") == self.tenant_id
            and result.payload.get("tenant_user_id") == self.tenant_user_id
        ]

    async def delete(self, item_id: str) -> bool:
        try:
            await self.qdrant.delete(
                collection_name="chunks",
                points_selector=[item_id],
            )
        except:
            return False
        return True


class PointService:
    def __init__(self, point_crud: PointCRUD) -> None:
        self.point_crud = point_crud

    async def create(self, item: PointCreateSchema) -> PointSchema:
        point = await self.point_crud.create(item)
        if point is None:
            raise AppException.PointInsertFailed
        return PointSchema.model_validate(point)

    async def query(self, item: PointQuerySchema) -> PointQueryResultSchema:
        query_results = await self.point_crud.query(item)
        if not query_results:
            raise AppException.PointQueryFailed
        return PointQueryResultSchema.model_validate(query_results)

    async def delete(self, item_id: str) -> bool:
        deleted = await self.point_crud.delete(item_id)
        if not deleted:
            raise AppException.PointNotFound
        return deleted


def get_point_crud(
    qdrant: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
    claims: Annotated[TokenClaimsSchema, Depends(get_token_claims)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PointCRUD:
    return PointCRUD(
        qdrant,
        settings.qdrant_collection_name,
        claims.tenant_id,
        claims.tenant_user_id,
    )
