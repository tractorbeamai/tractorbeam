from typing import Annotated

from fastapi import APIRouter, Depends

from ..integrations.registry import IntegrationRegistry, get_integration_registry
from ..schemas.integration import IntegrationSchema
from ..security import get_token_claims

router = APIRouter(
    prefix="/integrations",
    tags=["integrations"],
    dependencies=[Depends(get_token_claims)],
)


@router.get("/")
async def get_integrations(
    registry: Annotated[IntegrationRegistry, Depends(get_integration_registry)],
) -> list[IntegrationSchema]:
    return [
        IntegrationSchema(
            slug=integration.slug,
            name=integration.name,
            logo_url=integration.logo_url,
        )
        for integration in registry.get_all()
    ]


@router.get("/{slug}/")
async def get_integration(
    slug: str,
    registry: Annotated[IntegrationRegistry, Depends(get_integration_registry)],
) -> IntegrationSchema:
    integration = registry.get(slug)
    return IntegrationSchema(
        slug=integration.slug,
        name=integration.name,
        logo_url=integration.logo_url,
    )
