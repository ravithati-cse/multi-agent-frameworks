"""
Order domain tools — thin async wrappers over the service layer.
Agents call these instead of hitting HTTP, keeping everything in-process.
"""
from __future__ import annotations
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.orders.service import OrderService
from app.domains.orders.schemas import OrderCreate, OrderUpdate
from app.domains.orders.models import OrderStatus


async def get_order(db: AsyncSession, order_id: str) -> dict:
    svc = OrderService(db)
    order = await svc.get(uuid.UUID(order_id))
    if not order:
        return {"error": f"Order {order_id} not found"}
    return {"id": str(order.id), "status": order.status, "total": float(order.total_amount), "items": order.items}


async def list_kitchen_orders(db: AsyncSession, kitchen_id: str, status: str | None = None) -> list[dict]:
    svc = OrderService(db)
    orders = await svc.list_by_kitchen(kitchen_id, status)
    return [{"id": str(o.id), "status": o.status, "total": float(o.total_amount)} for o in orders]


async def advance_order_status(db: AsyncSession, order_id: str, status: str) -> dict:
    svc = OrderService(db)
    order = await svc.update_status(uuid.UUID(order_id), OrderStatus(status))
    if not order:
        return {"error": f"Order {order_id} not found"}
    return {"id": str(order.id), "status": order.status}
