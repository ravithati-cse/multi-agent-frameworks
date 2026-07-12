from __future__ import annotations
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.kitchen.service import KitchenService
from app.domains.kitchen.schemas import KitchenStatusUpdate
from app.domains.kitchen.models import KitchenStatus


async def get_kitchen_status(db: AsyncSession, kitchen_id: str) -> dict:
    svc = KitchenService(db)
    k = await svc.get(uuid.UUID(kitchen_id))
    if not k:
        return {"error": f"Kitchen {kitchen_id} not found"}
    return {"id": str(k.id), "name": k.name, "status": k.status}


async def set_kitchen_busy(db: AsyncSession, kitchen_id: str) -> dict:
    svc = KitchenService(db)
    k = await svc.set_status(uuid.UUID(kitchen_id), KitchenStatusUpdate(status=KitchenStatus.BUSY))
    return {"id": str(k.id), "status": k.status} if k else {"error": "not found"}
