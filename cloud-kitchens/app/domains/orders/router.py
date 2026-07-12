import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domains.orders.schemas import OrderCreate, OrderOut, OrderUpdate
from app.domains.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/", response_model=OrderOut, status_code=201)
async def create_order(body: OrderCreate, db: DB):
    svc = OrderService(db)
    return await svc.create(body)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: uuid.UUID, db: DB):
    svc = OrderService(db)
    order = await svc.get(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.get("/kitchen/{kitchen_id}", response_model=list[OrderOut])
async def list_kitchen_orders(
    kitchen_id: str, db: DB, status: str | None = Query(None)
):
    svc = OrderService(db)
    return await svc.list_by_kitchen(kitchen_id, status)


@router.patch("/{order_id}", response_model=OrderOut)
async def update_order(order_id: uuid.UUID, body: OrderUpdate, db: DB):
    svc = OrderService(db)
    if body.status:
        order = await svc.update_status(order_id, body.status)
    else:
        order = await svc.get(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.delete("/{order_id}", status_code=204)
async def cancel_order(order_id: uuid.UUID, db: DB):
    svc = OrderService(db)
    order = await svc.cancel(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
