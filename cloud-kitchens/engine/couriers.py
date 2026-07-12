"""
CourierSim — simulates courier dispatch and arrival.

On dispatch_for(order), schedules a courier to arrive after
Uniform(3, 15) seconds, then emits CourierArrived and calls back
into the dispatch strategy.
"""
from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime

from contracts.models import Courier, SimEvent
from engine.events import SimEventBus

logger = logging.getLogger(__name__)

ARRIVAL_MIN_S = 3
ARRIVAL_MAX_S = 15


class CourierSim:
    def __init__(self, bus: SimEventBus, rng: random.Random, speed: float = 1.0) -> None:
        self._bus = bus
        self._rng = rng
        self._speed = speed
        self._waiting_couriers: list[Courier] = []
        self._on_arrived_cb = None  # set by the runner after construction

    def set_on_arrived(self, cb) -> None:
        """Callback invoked (with the arrived Courier) when courier arrives."""
        self._on_arrived_cb = cb

    @property
    def waiting_couriers(self) -> list[Courier]:
        return list(self._waiting_couriers)

    def remove_waiting(self, courier: Courier) -> None:
        self._waiting_couriers.remove(courier)

    async def dispatch_for(self, order_id: str | None = None) -> Courier:
        """Dispatch a courier. For Matched strategy, pass the order_id to pre-assign."""
        courier = Courier(assigned_order_id=order_id)
        delay = self._rng.uniform(ARRIVAL_MIN_S, ARRIVAL_MAX_S)
        await self._bus.publish(SimEvent(type="CourierDispatched", payload={
            "courier_id": courier.id, "order_id": order_id, "eta_s": round(delay, 1)
        }))
        logger.info("[COURIER] dispatched, arriving in %.1fs", delay)
        asyncio.create_task(self._arrive(courier, delay))
        return courier

    async def _arrive(self, courier: Courier, delay: float) -> None:
        await asyncio.sleep(delay / self._speed)
        courier.arrived_at = datetime.utcnow()
        self._waiting_couriers.append(courier)
        await self._bus.publish(SimEvent(type="CourierArrived", payload={"courier_id": courier.id}))
        logger.info("[COURIER] %s arrived", courier.id[:8])

        if self._on_arrived_cb:
            await self._on_arrived_cb(courier)
