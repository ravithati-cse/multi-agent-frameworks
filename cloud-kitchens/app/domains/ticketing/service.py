import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.ticketing.models import Ticket
from app.domains.ticketing.schemas import TicketCreate


class TicketService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: TicketCreate) -> Ticket:
        ticket = Ticket(**data.model_dump())
        self.db.add(ticket)
        await self.db.flush()
        return ticket

    async def get(self, ticket_id: uuid.UUID) -> Ticket | None:
        return await self.db.get(Ticket, ticket_id)

    async def list_by_customer(self, customer_id: str) -> list[Ticket]:
        result = await self.db.execute(
            select(Ticket).where(Ticket.customer_id == customer_id).order_by(Ticket.created_at.desc())
        )
        return list(result.scalars().all())

    async def escalate(self, ticket_id: uuid.UUID, reason: str) -> Ticket | None:
        ticket = await self.get(ticket_id)
        if not ticket:
            return None
        ticket.status = "escalated"
        ticket.description = ticket.description + f"\n[Escalation] {reason}"
        return ticket

    async def resolve(self, ticket_id: uuid.UUID, resolution: str) -> Ticket | None:
        ticket = await self.get(ticket_id)
        if not ticket:
            return None
        ticket.status = "resolved"
        ticket.resolution = resolution
        return ticket
