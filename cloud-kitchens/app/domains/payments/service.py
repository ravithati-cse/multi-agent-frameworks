import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.events import bus, DomainEvent
from app.domains.payments.models import Payment, PaymentStatus
from app.domains.payments.schemas import PaymentCreate


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: PaymentCreate) -> Payment:
        payment = Payment(**data.model_dump())
        self.db.add(payment)
        await self.db.flush()
        # TODO: call Stripe / payment provider here
        return payment

    async def get(self, payment_id: uuid.UUID) -> Payment | None:
        return await self.db.get(Payment, payment_id)

    async def get_by_order(self, order_id: uuid.UUID) -> Payment | None:
        result = await self.db.execute(select(Payment).where(Payment.order_id == order_id))
        return result.scalars().first()

    async def capture(self, payment_id: uuid.UUID) -> Payment | None:
        p = await self.get(payment_id)
        if not p:
            return None
        p.status = PaymentStatus.CAPTURED
        await bus.publish(DomainEvent("payment.captured", {"payment_id": str(payment_id), "order_id": str(p.order_id)}))
        return p

    async def refund(self, payment_id: uuid.UUID) -> Payment | None:
        p = await self.get(payment_id)
        if not p:
            return None
        p.status = PaymentStatus.REFUNDED
        await bus.publish(DomainEvent("payment.refunded", {"payment_id": str(payment_id)}))
        return p
