import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class MenuItemCreate(BaseModel):
    brand_id: str
    name: str
    description: str = ""
    price: float = Field(ge=0)
    category: str = ""
    tags: list[str] = []
    ingredients: list[dict] = []
    is_available: bool = True
    prep_time_minutes: int = 15


class MenuItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category: str | None = None
    tags: list[str] | None = None
    is_available: bool | None = None
    prep_time_minutes: int | None = None


class MenuItemOut(BaseModel):
    id: uuid.UUID
    brand_id: str
    name: str
    description: str
    price: float
    category: str
    tags: list
    is_available: bool
    prep_time_minutes: int
    created_at: datetime
    model_config = {"from_attributes": True}
