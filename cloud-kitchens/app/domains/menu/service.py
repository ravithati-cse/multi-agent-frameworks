import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.menu.models import MenuItem
from app.domains.menu.schemas import MenuItemCreate, MenuItemUpdate


class MenuService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: MenuItemCreate) -> MenuItem:
        item = MenuItem(**data.model_dump())
        self.db.add(item)
        await self.db.flush()
        return item

    async def get(self, item_id: uuid.UUID) -> MenuItem | None:
        return await self.db.get(MenuItem, item_id)

    async def list_by_brand(self, brand_id: str, available_only: bool = False):
        q = select(MenuItem).where(MenuItem.brand_id == brand_id)
        if available_only:
            q = q.where(MenuItem.is_available == True)
        result = await self.db.execute(q.order_by(MenuItem.category, MenuItem.name))
        return result.scalars().all()

    async def update(self, item_id: uuid.UUID, data: MenuItemUpdate) -> MenuItem | None:
        item = await self.get(item_id)
        if not item:
            return None
        for field, val in data.model_dump(exclude_none=True).items():
            setattr(item, field, val)
        return item

    async def delete(self, item_id: uuid.UUID) -> bool:
        item = await self.get(item_id)
        if not item:
            return False
        await self.db.delete(item)
        return True
