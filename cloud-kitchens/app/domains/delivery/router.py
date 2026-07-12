import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domains.delivery.schemas import DeliveryCreate, DeliveryOut, DeliveryStatusUpdate
from app.domains.delivery.service import DeliveryService

router = APIRouter(prefix="/deliveries", tags=["deliveries"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/", response_model=DeliveryOut, status_code=201)
async def create_delivery(body: DeliveryCreate, db: DB):
    return await DeliveryService(db).create(body)


@router.get("/{delivery_id}", response_model=DeliveryOut)
async def get_delivery(delivery_id: uuid.UUID, db: DB):
    d = await DeliveryService(db).get(delivery_id)
    if not d:
        raise HTTPException(404, "Delivery not found")
    return d


@router.get("/by-order/{order_id}", response_model=DeliveryOut)
async def get_by_order(order_id: uuid.UUID, db: DB):
    d = await DeliveryService(db).get_by_order(order_id)
    if not d:
        raise HTTPException(404, "Delivery not found")
    return d


@router.patch("/{delivery_id}/status", response_model=DeliveryOut)
async def update_status(delivery_id: uuid.UUID, body: DeliveryStatusUpdate, db: DB):
    d = await DeliveryService(db).update_status(delivery_id, body)
    if not d:
        raise HTTPException(404, "Delivery not found")
    return d
