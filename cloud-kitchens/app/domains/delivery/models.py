import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class DeliveryStatus(str, PyEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    FAILED = "failed"


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    driver_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    provider: Mapped[str] = mapped_column(String(32), default="internal")   # internal | doordash | uber_eats
    status: Mapped[str] = mapped_column(String(32), default=DeliveryStatus.PENDING, index=True)
    pickup_address: Mapped[dict] = mapped_column(JSONB, default=dict)
    dropoff_address: Mapped[dict] = mapped_column(JSONB, default=dict)
    tracking_url: Mapped[str] = mapped_column(String(512), default="")
    estimated_minutes: Mapped[int] = mapped_column(default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
