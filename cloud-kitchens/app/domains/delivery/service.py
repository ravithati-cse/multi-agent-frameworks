import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.events import bus, DomainEvent
from app.domains.delivery.models import Delivery, DeliveryStatus
from app.domains.delivery.schemas import DeliveryCreate, DeliveryStatusUpdate


class DeliveryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: DeliveryCreate) -> Delivery:
        delivery = Delivery(**data.model_dump())
        self.db.add(delivery)
        await self.db.flush()
        await bus.publish(DomainEvent("delivery.created", {"delivery_id": str(delivery.id), "order_id": str(delivery.order_id)}))
        return delivery

    async def get(self, delivery_id: uuid.UUID) -> Delivery | None:
        return await self.db.get(Delivery, delivery_id)

    async def get_by_order(self, order_id: uuid.UUID) -> Delivery | None:
        result = await self.db.execute(
            select(Delivery).where(Delivery.order_id == order_id)
        )
        return result.scalars().first()

    async def update_status(self, delivery_id: uuid.UUID, data: DeliveryStatusUpdate) -> Delivery | None:
        d = await self.get(delivery_id)
        if not d:
            return None
        d.status = data.status
        if data.driver_id:
            d.driver_id = data.driver_id
        if data.tracking_url:
            d.tracking_url = data.tracking_url
        await bus.publish(DomainEvent("delivery.status_changed", {"delivery_id": str(delivery_id), "status": data.status}))
        return d
