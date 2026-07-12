import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domains.orders.models import OrderStatus


class OrderItemIn(BaseModel):
    item_id: str
    qty: int = Field(ge=1)
    price: float = Field(ge=0)


class OrderCreate(BaseModel):
    customer_id: str
    brand_id: str
    kitchen_id: str
    items: list[OrderItemIn]
    delivery_address: dict[str, Any] = {}
    notes: str = ""


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    notes: str | None = None


class OrderOut(BaseModel):
    id: uuid.UUID
    customer_id: str
    brand_id: str
    kitchen_id: str
    status: str
    total_amount: float
    items: list[dict]
    delivery_address: dict
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
