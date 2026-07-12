"""
KitchenSim — simulates order preparation.

Each order occupies a prep slot for prep_time_s seconds (asyncio.sleep).
When prep finishes, emits OrderReady and calls back into the dispatch strategy.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from contracts.models import Order, SimEvent
from engine.events import SimEventBus

logger = logging.getLogger(__name__)


class KitchenSim:
    def __init__(self, bus: SimEventBus, max_concurrent: int = 10, speed: float = 1.0) -> None:
        self._bus = bus
        self._speed = speed
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._ready_orders: list[Order] = []
        self._on_ready_cb = None  # set by the runner after construction

    def set_on_ready(self, cb) -> None:
        """Callback invoked (with the ready Order) when prep finishes."""
        self._on_ready_cb = cb

    @property
    def ready_orders(self) -> list[Order]:
        return list(self._ready_orders)

    def remove_ready(self, order: Order) -> None:
        self._ready_orders.remove(order)

    async def enqueue(self, order: Order) -> None:
        asyncio.create_task(self._prep(order))

    async def _prep(self, order: Order) -> None:
        async with self._semaphore:
            order.status = "prepping"
            logger.info("[KITCHEN] %s prepping for %ds", order.name, order.prep_time_s)
            await self._bus.publish(SimEvent(type="OrderPrepping", payload={"order_id": order.id}))
            await asyncio.sleep(order.prep_time_s / self._speed)

            order.status = "ready"
            order.ready_at = datetime.utcnow()
            self._ready_orders.append(order)
            await self._bus.publish(SimEvent(type="OrderReady", payload={"order_id": order.id}))
            logger.info("[KITCHEN] %s ready", order.name)

            if self._on_ready_cb:
                await self._on_ready_cb(order)
