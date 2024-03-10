from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FooItem, FooItemCreate
from ..services.foo import FooService
from ..utils.service_result import handle_result

router = APIRouter(
    prefix="/foo",
    tags=["items"],
)


@router.post("/item/", response_model=FooItem)
async def create_item(item: FooItemCreate, db: Annotated[Session, Depends(get_db)]):
    result = await FooService(db).create_item(item)
    return handle_result(result)


@router.get("/item/{item_id}", response_model=FooItem)
async def get_item(item_id: int, db: Annotated[Session, Depends(get_db)]):
    result = await FooService(db).get_item(item_id)
    return handle_result(result)
