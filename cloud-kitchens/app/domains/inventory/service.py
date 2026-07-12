import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.events import bus, DomainEvent
from app.domains.inventory.models import InventoryItem
from app.domains.inventory.schemas import InventoryItemCreate, InventoryAdjust


class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: InventoryItemCreate) -> InventoryItem:
        item = InventoryItem(**data.model_dump())
        self.db.add(item)
        await self.db.flush()
        return item

    async def get(self, item_id: uuid.UUID) -> InventoryItem | None:
        return await self.db.get(InventoryItem, item_id)

    async def list_by_kitchen(self, kitchen_id: str):
        result = await self.db.execute(
            select(InventoryItem).where(InventoryItem.kitchen_id == kitchen_id)
        )
        return result.scalars().all()

    async def adjust(self, item_id: uuid.UUID, adj: InventoryAdjust) -> InventoryItem | None:
        item = await self.get(item_id)
        if not item:
            return None
        item.quantity = max(0.0, item.quantity + adj.delta)
        if item.quantity <= item.reorder_level:
            await bus.publish(DomainEvent(
                "inventory.low",
                {"item_id": str(item_id), "kitchen_id": item.kitchen_id, "quantity": item.quantity}
            ))
        return item

    async def low_stock(self, kitchen_id: str) -> list[InventoryItem]:
        items = await self.list_by_kitchen(kitchen_id)
        return [i for i in items if i.quantity <= i.reorder_level]
