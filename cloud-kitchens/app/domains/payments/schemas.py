import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.domains.payments.models import PaymentStatus


class PaymentCreate(BaseModel):
    order_id: uuid.UUID
    amount: float = Field(ge=0)
    currency: str = "USD"
    provider: str = "stripe"


class PaymentOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    amount: float
    currency: str
    status: str
    provider: str
    provider_payment_id: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
