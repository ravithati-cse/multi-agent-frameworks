import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.events import bus, DomainEvent
from app.domains.kitchen.models import Kitchen, KitchenStatus
from app.domains.kitchen.schemas import KitchenCreate, KitchenStatusUpdate


class KitchenService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: KitchenCreate) -> Kitchen:
        kitchen = Kitchen(**data.model_dump())
        self.db.add(kitchen)
        await self.db.flush()
        return kitchen

    async def get(self, kitchen_id: uuid.UUID) -> Kitchen | None:
        return await self.db.get(Kitchen, kitchen_id)

    async def list_all(self, active_only: bool = True):
        q = select(Kitchen)
        if active_only:
            q = q.where(Kitchen.is_active == True)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def set_status(self, kitchen_id: uuid.UUID, data: KitchenStatusUpdate) -> Kitchen | None:
        kitchen = await self.get(kitchen_id)
        if not kitchen:
            return None
        kitchen.status = data.status
        await bus.publish(DomainEvent("kitchen.status_changed", {"kitchen_id": str(kitchen_id), "status": data.status}))
        return kitchen
