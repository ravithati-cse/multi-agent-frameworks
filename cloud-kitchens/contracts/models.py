"""
Shared Pydantic schemas — single source of truth for engine + all 5 agent adapters.
Import these everywhere; never redefine them per-framework.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    name: str
    quantity: int = 1


class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    prep_time_s: int
    items: list[OrderItem] = []
    status: Literal[
        "received", "confirmed", "prepping", "ready", "picked_up", "delivered", "cancelled"
    ] = "received"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ready_at: datetime | None = None
    picked_up_at: datetime | None = None


class Courier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assigned_order_id: str | None = None   # set at dispatch for Matched; None until pickup for FIFO
    dispatched_at: datetime = Field(default_factory=datetime.utcnow)
    arrived_at: datetime | None = None


class SimEvent(BaseModel):
    type: str   # OrderReceived | OrderReady | CourierDispatched | CourierArrived | OrderPickedUp
    payload: dict
    ts: datetime = Field(default_factory=datetime.utcnow)


class Metrics(BaseModel):
    avg_food_wait_ms: float = 0.0   # time order sat ready before pickup
    avg_courier_wait_ms: float = 0.0  # time courier waited after arriving before pickup
    sample_count: int = 0
