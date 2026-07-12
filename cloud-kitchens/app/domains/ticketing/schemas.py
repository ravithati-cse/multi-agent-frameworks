import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class TicketCreate(BaseModel):
    order_id: str | None = None
    customer_id: str
    category: Literal["refund", "complaint", "inquiry", "courier_issue"]
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    description: str


class TicketEscalate(BaseModel):
    reason: str


class TicketResolve(BaseModel):
    resolution: str


class TicketOut(BaseModel):
    id: uuid.UUID
    order_id: str | None
    customer_id: str
    category: str
    status: str
    priority: str
    description: str
    resolution: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
