import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), default="")
    price: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="")
    tags: Mapped[list] = mapped_column(JSONB, default=list)          # ["vegan", "spicy"]
    ingredients: Mapped[list] = mapped_column(JSONB, default=list)   # [{ingredient_id, qty}]
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    prep_time_minutes: Mapped[int] = mapped_column(default=15)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
