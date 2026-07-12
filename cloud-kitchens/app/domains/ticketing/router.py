import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domains.ticketing.schemas import TicketCreate, TicketEscalate, TicketResolve, TicketOut
from app.domains.ticketing.service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/", response_model=TicketOut, status_code=201)
async def create_ticket(body: TicketCreate, db: DB):
    return await TicketService(db).create(body)


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(ticket_id: uuid.UUID, db: DB):
    ticket = await TicketService(db).get(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket


@router.get("/customer/{customer_id}", response_model=list[TicketOut])
async def list_tickets(customer_id: str, db: DB):
    return await TicketService(db).list_by_customer(customer_id)


@router.post("/{ticket_id}/escalate", response_model=TicketOut)
async def escalate_ticket(ticket_id: uuid.UUID, body: TicketEscalate, db: DB):
    ticket = await TicketService(db).escalate(ticket_id, body.reason)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket


@router.post("/{ticket_id}/resolve", response_model=TicketOut)
async def resolve_ticket(ticket_id: uuid.UUID, body: TicketResolve, db: DB):
    ticket = await TicketService(db).resolve(ticket_id, body.resolution)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket
