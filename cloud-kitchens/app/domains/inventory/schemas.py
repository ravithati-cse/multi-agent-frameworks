import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class InventoryItemCreate(BaseModel):
    kitchen_id: str
    name: str
    unit: str = "unit"
    quantity: float = Field(ge=0)
    reorder_level: float = Field(ge=0, default=0)
    cost_per_unit: float = Field(ge=0, default=0)


class InventoryAdjust(BaseModel):
    delta: float   # positive = restock, negative = consume


class InventoryItemOut(BaseModel):
    id: uuid.UUID
    kitchen_id: str
    name: str
    unit: str
    quantity: float
    reorder_level: float
    cost_per_unit: float
    is_low: bool = False
    updated_at: datetime
    model_config = {"from_attributes": True}
