from __future__ import annotations
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.inventory.service import InventoryService
from app.domains.inventory.schemas import InventoryAdjust


async def check_low_stock(db: AsyncSession, kitchen_id: str) -> list[dict]:
    svc = InventoryService(db)
    items = await svc.low_stock(kitchen_id)
    return [{"id": str(i.id), "name": i.name, "quantity": i.quantity, "reorder_level": i.reorder_level} for i in items]


async def restock_item(db: AsyncSession, item_id: str, qty: float) -> dict:
    svc = InventoryService(db)
    item = await svc.adjust(uuid.UUID(item_id), InventoryAdjust(delta=qty))
    if not item:
        return {"error": f"Item {item_id} not found"}
    return {"id": str(item.id), "name": item.name, "quantity": item.quantity}
