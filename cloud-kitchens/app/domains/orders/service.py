import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import bus, DomainEvent
from app.domains.orders.models import Order, OrderStatus
from app.domains.orders.schemas import OrderCreate, OrderUpdate


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: OrderCreate) -> Order:
        total = sum(i.qty * i.price for i in data.items)
        order = Order(
            customer_id=data.customer_id,
            brand_id=data.brand_id,
            kitchen_id=data.kitchen_id,
            items=[i.model_dump() for i in data.items],
            delivery_address=data.delivery_address,
            notes=data.notes,
            total_amount=total,
        )
        self.db.add(order)
        await self.db.flush()
        await bus.publish(DomainEvent("order.created", {"order_id": str(order.id), "brand_id": order.brand_id}))
        return order

    async def get(self, order_id: uuid.UUID) -> Order | None:
        return await self.db.get(Order, order_id)

    async def list_by_kitchen(self, kitchen_id: str, status: str | None = None) -> Sequence[Order]:
        q = select(Order).where(Order.kitchen_id == kitchen_id)
        if status:
            q = q.where(Order.status == status)
        result = await self.db.execute(q.order_by(Order.created_at.desc()))
        return result.scalars().all()

    async def update_status(self, order_id: uuid.UUID, status: OrderStatus) -> Order | None:
        order = await self.get(order_id)
        if not order:
            return None
        order.status = status
        await bus.publish(DomainEvent("order.status_changed", {"order_id": str(order_id), "status": status}))
        return order

    async def cancel(self, order_id: uuid.UUID) -> Order | None:
        return await self.update_status(order_id, OrderStatus.CANCELLED)
