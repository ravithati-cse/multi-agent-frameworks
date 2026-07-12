"""
MetricsCollector — subscribes to OrderPickedUp events and computes running averages.

food_wait  = time from order.ready_at   → pickup
courier_wait = time from courier.arrived_at → pickup
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from contracts.models import Metrics, SimEvent
from engine.events import SimEventBus

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self, bus: SimEventBus) -> None:
        self._metrics = Metrics()
        bus.subscribe("OrderPickedUp", self._on_picked_up)

    async def _on_picked_up(self, event: SimEvent) -> None:
        food_wait_ms = event.payload.get("food_wait_ms", 0.0)
        courier_wait_ms = event.payload.get("courier_wait_ms", 0.0)

        n = self._metrics.sample_count
        self._metrics.avg_food_wait_ms = (self._metrics.avg_food_wait_ms * n + food_wait_ms) / (n + 1)
        self._metrics.avg_courier_wait_ms = (self._metrics.avg_courier_wait_ms * n + courier_wait_ms) / (n + 1)
        self._metrics.sample_count += 1

        logger.info(
            "[METRICS] pickup #%d | food_wait=%.0fms courier_wait=%.0fms | "
            "avg_food=%.0fms avg_courier=%.0fms",
            self._metrics.sample_count,
            food_wait_ms,
            courier_wait_ms,
            self._metrics.avg_food_wait_ms,
            self._metrics.avg_courier_wait_ms,
        )

    def snapshot(self) -> Metrics:
        return self._metrics.model_copy()

    def print_summary(self) -> None:
        m = self._metrics
        print("\n=== Final Metrics ===")
        print(f"  Orders completed : {m.sample_count}")
        print(f"  Avg food wait    : {m.avg_food_wait_ms:.1f} ms")
        print(f"  Avg courier wait : {m.avg_courier_wait_ms:.1f} ms")
        print("=====================\n")
