"""
OrderGenerator — reads orders from JSON and emits them at the configured rate.

JSON format (array of objects):
  [{"name": "Burger", "prepTime": 5}, ...]

prepTime in the source JSON is in seconds; stored as prep_time_s.
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from contracts.models import Order, OrderItem, SimEvent
from engine.events import SimEventBus

logger = logging.getLogger(__name__)


class OrderGenerator:
    def __init__(
        self,
        bus: SimEventBus,
        orders_path: Path,
        rate_per_second: float = 2.0,
    ) -> None:
        self._bus = bus
        self._orders_path = orders_path
        self._interval = 1.0 / rate_per_second

    def _load(self) -> list[Order]:
        raw = json.loads(self._orders_path.read_text())
        orders = []
        for obj in raw:
            orders.append(
                Order(
                    name=obj["name"],
                    prep_time_s=obj["prepTime"],
                )
            )
        return orders

    async def run(self) -> None:
        orders = self._load()
        logger.info("OrderGenerator: loaded %d orders, rate=%.1f/s", len(orders), 1 / self._interval)
        for i, order in enumerate(orders):
            await self._bus.publish(SimEvent(type="OrderReceived", payload={"order_id": order.id}))
            logger.info("[ORDER] %s received (prep=%ds)", order.name, order.prep_time_s)
            yield order
            if i < len(orders) - 1:
                await asyncio.sleep(self._interval)
