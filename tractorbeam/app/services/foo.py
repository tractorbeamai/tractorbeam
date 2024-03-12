from ..models import FooItem, FooItemCreate
from ..utils.app_exceptions import AppException
from ..utils.service_result import ServiceResult
from .common import AppCRUD, AppService


class FooService(AppService):
    async def create_item(self, item: FooItemCreate) -> ServiceResult:
        foo_item = await FooCRUD(self.db).create_item(item)
        if not foo_item:
            return ServiceResult(AppException.FooCreateItem())
        return ServiceResult(foo_item)

    async def get_item(self, item_id: int) -> ServiceResult:
        foo_item = await FooCRUD(self.db).get_item(item_id)
        if not foo_item:
            return ServiceResult(AppException.FooGetItem({"item_id": item_id}))
        if not foo_item.public:
            return ServiceResult(AppException.FooItemRequiresAuth())
        return ServiceResult(foo_item)


class FooCRUD(AppCRUD):
    async def create_item(self, item: FooItemCreate) -> FooItem:
        foo_item = FooItem(description=item.description, public=item.public)
        self.db.add(foo_item)
        await self.db.commit()
        await self.db.refresh(foo_item)
        return foo_item

    async def get_item(self, item_id: int) -> FooItem:
        foo_item = await self.db.query(FooItem).filter(FooItem.id == item_id).first()
        if foo_item:
            return foo_item
        return None
