import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domains.payments.schemas import PaymentCreate, PaymentOut
from app.domains.payments.service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/", response_model=PaymentOut, status_code=201)
async def create_payment(body: PaymentCreate, db: DB):
    return await PaymentService(db).create(body)


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(payment_id: uuid.UUID, db: DB):
    p = await PaymentService(db).get(payment_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    return p


@router.get("/by-order/{order_id}", response_model=PaymentOut)
async def get_by_order(order_id: uuid.UUID, db: DB):
    p = await PaymentService(db).get_by_order(order_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    return p


@router.post("/{payment_id}/capture", response_model=PaymentOut)
async def capture_payment(payment_id: uuid.UUID, db: DB):
    p = await PaymentService(db).capture(payment_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    return p


@router.post("/{payment_id}/refund", response_model=PaymentOut)
async def refund_payment(payment_id: uuid.UUID, db: DB):
    p = await PaymentService(db).refund(payment_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    return p
