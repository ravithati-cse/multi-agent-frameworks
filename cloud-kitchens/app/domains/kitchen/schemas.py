import uuid
from datetime import datetime
from pydantic import BaseModel
from app.domains.kitchen.models import KitchenStatus


class KitchenCreate(BaseModel):
    name: str
    location: dict = {}
    brand_ids: list[str] = []
    operating_hours: dict = {}
    station_config: dict = {}


class KitchenStatusUpdate(BaseModel):
    status: KitchenStatus


class KitchenOut(BaseModel):
    id: uuid.UUID
    name: str
    location: dict
    status: str
    brand_ids: list
    station_config: dict
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}
