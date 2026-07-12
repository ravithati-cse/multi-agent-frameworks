import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class KitchenStatus(str, PyEnum):
    OPEN = "open"
    CLOSED = "closed"
    BUSY = "busy"


class Kitchen(Base):
    __tablename__ = "kitchens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    location: Mapped[dict] = mapped_column(JSONB, default=dict)   # {lat, lng, address}
    status: Mapped[str] = mapped_column(String(32), default=KitchenStatus.OPEN, index=True)
    brand_ids: Mapped[list] = mapped_column(JSONB, default=list)   # virtual brands served
    operating_hours: Mapped[dict] = mapped_column(JSONB, default=dict)
    station_config: Mapped[dict] = mapped_column(JSONB, default=dict)  # {grill: 2, fry: 3}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
