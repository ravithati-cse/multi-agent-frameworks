import uuid
from datetime import datetime
from pydantic import BaseModel
from app.domains.delivery.models import DeliveryStatus


class DeliveryCreate(BaseModel):
    order_id: uuid.UUID
    pickup_address: dict
    dropoff_address: dict
    provider: str = "internal"
    estimated_minutes: int = 30


class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus
    driver_id: str | None = None
    tracking_url: str | None = None


class DeliveryOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    driver_id: str
    provider: str
    status: str
    pickup_address: dict
    dropoff_address: dict
    tracking_url: str
    estimated_minutes: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
