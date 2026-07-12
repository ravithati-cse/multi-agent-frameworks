"""
Simulation runner — wires all engine components and supports:
  - CLI usage: python -m engine.runner --strategy matched
  - WebSocket usage: SimRunner(ws_broadcast=callback) from the dashboard API
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable

from contracts.models import Courier, Order, SimEvent
from engine.couriers import CourierSim, ARRIVAL_MAX_S
from engine.dispatch_baselines import fifo_strategy, matched_strategy
from engine.events import SimEventBus
from engine.kitchen import KitchenSim
from engine.metrics import MetricsCollector
from engine.orders import OrderGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

STRATEGY_MAP = {"matched": matched_strategy, "fifo": fifo_strategy}
DEFAULT_ORDERS = Path(__file__).parent / "data" / "orders.json"

Broadcast = Callable[[dict], Awaitable[None]]


class SimRunner:
    def __init__(
        self,
        strategy_name: str,
        orders_path: Path = DEFAULT_ORDERS,
        seed: int = 42,
        rate: float = 2.0,
        speed: float = 1.0,
        ws_broadcast: Broadcast | None = None,
    ) -> None:
        self.strategy_name = strategy_name
        self.strategy = STRATEGY_MAP[strategy_name]
        self.speed = speed
        self._ws = ws_broadcast

        self.bus = SimEventBus()
        self.rng = random.Random(seed)
        self.kitchen = KitchenSim(self.bus, speed=speed)
        self.couriers = CourierSim(self.bus, self.rng, speed=speed)
        self.metrics = MetricsCollector(self.bus)
        self.generator = OrderGenerator(self.bus, orders_path, rate * speed)

        self._orders: dict[str, Order] = {}
        self._couriers: dict[str, dict] = {}  # courier_id → {id, assigned_order_id, eta_s, status}
        self._pickup_count = 0

        self.kitchen.set_on_ready(self._on_trigger)
        self.couriers.set_on_arrived(self._on_trigger)

        # subscribe to bus events for WebSocket broadcasting
        self.bus.subscribe("OrderPrepping", self._ws_order_prepping)
        self.bus.subscribe("OrderReady", self._ws_order_ready)
        self.bus.subscribe("CourierDispatched", self._ws_courier_dispatched)
        self.bus.subscribe("CourierArrived", self._ws_courier_arrived)
        self.bus.subscribe("OrderPickedUp", self._ws_order_picked_up)

    # ── WebSocket event enrichers ───────────────────────────────────────────

    async def _emit(self, msg: dict) -> None:
        if self._ws:
            await self._ws(msg)

    async def _ws_order_prepping(self, event: SimEvent) -> None:
        order = self._orders.get(event.payload["order_id"])
        if order:
            await self._emit({"type": "order_prepping", "id": order.id, "name": order.name})

    async def _ws_order_ready(self, event: SimEvent) -> None:
        order = self._orders.get(event.payload["order_id"])
        if order:
            await self._emit({"type": "order_ready", "id": order.id, "name": order.name})

    async def _ws_courier_dispatched(self, event: SimEvent) -> None:
        p = event.payload
        self._couriers[p["courier_id"]] = {
            "id": p["courier_id"], "assigned_order_id": p.get("order_id"),
            "eta_s": p.get("eta_s", 9), "status": "en_route"
        }
        await self._emit({"type": "courier_dispatched", **self._couriers[p["courier_id"]]})

    async def _ws_courier_arrived(self, event: SimEvent) -> None:
        cid = event.payload["courier_id"]
        if cid in self._couriers:
            self._couriers[cid]["status"] = "waiting"
        await self._emit({"type": "courier_arrived", "id": cid})

    async def _ws_order_picked_up(self, event: SimEvent) -> None:
        p = event.payload
        if p["courier_id"] in self._couriers:
            del self._couriers[p["courier_id"]]
        m = self.metrics.snapshot()
        await self._emit({
            "type": "order_picked_up",
            "order_id": p["order_id"],
            "courier_id": p["courier_id"],
            "food_wait_ms": round(p["food_wait_ms"]),
            "courier_wait_ms": round(p["courier_wait_ms"]),
        })
        await self._emit({
            "type": "metrics_update",
            "completed": m.sample_count,
            "total": len(self._orders),
            "avg_food_wait_ms": round(m.avg_food_wait_ms),
            "avg_courier_wait_ms": round(m.avg_courier_wait_ms),
        })

    # ── Dispatch logic ──────────────────────────────────────────────────────

    async def _on_trigger(self, _) -> None:
        pairs = self.strategy(self.kitchen.ready_orders, self.couriers.waiting_couriers)
        for order, courier in pairs:
            await self._do_pickup(order, courier)

    async def _do_pickup(self, order: Order, courier: Courier) -> None:
        now = datetime.utcnow()
        food_wait_ms = (now - order.ready_at).total_seconds() * 1000
        courier_wait_ms = (now - courier.arrived_at).total_seconds() * 1000

        order.status = "picked_up"
        order.picked_up_at = now
        self._pickup_count += 1
        self.kitchen.remove_ready(order)
        self.couriers.remove_waiting(courier)

        await self.bus.publish(SimEvent(type="OrderPickedUp", payload={
            "order_id": order.id, "courier_id": courier.id,
            "food_wait_ms": food_wait_ms, "courier_wait_ms": courier_wait_ms,
        }))
        logger.info("[PICKUP] %s | food=%.0fms courier=%.0fms", order.name, food_wait_ms, courier_wait_ms)

    # ── Main loop ───────────────────────────────────────────────────────────

    async def run(self) -> None:
        logger.info("=== Simulation start | strategy=%s speed=%.1fx ===", self.strategy_name, self.speed)

        import json
        total = len(json.loads(self.generator._orders_path.read_text()))

        await self._emit({"type": "sim_started", "strategy": self.strategy_name, "total": total})

        dispatch_task = asyncio.create_task(self.bus.dispatch_loop())

        async for order in self.generator.run():
            self._orders[order.id] = order
            await self.kitchen.enqueue(order)
            assigned_id = order.id if self.strategy_name == "matched" else None
            await self.couriers.dispatch_for(assigned_id)
            await self._emit({
                "type": "order_received",
                "id": order.id, "name": order.name, "prep_time_s": order.prep_time_s,
            })

        # Poll until every order is picked up.
        # Fixed sleep is unreliable: with many orders the kitchen queue drains
        # much longer than (max_prep + courier_ETA). Use a generous real-time
        # safety cap (120s) so the loop always terminates.
        elapsed = 0.0
        while self._pickup_count < total and elapsed < 120.0:
            await asyncio.sleep(0.2)
            elapsed += 0.2
        if self._pickup_count < total:
            logger.warning("Simulation ended with %d/%d orders picked up", self._pickup_count, total)
        dispatch_task.cancel()

        m = self.metrics.snapshot()
        await self._emit({
            "type": "sim_complete",
            "avg_food_wait_ms": round(m.avg_food_wait_ms),
            "avg_courier_wait_ms": round(m.avg_courier_wait_ms),
            "completed": m.sample_count,
        })
        self.metrics.print_summary()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=["matched", "fifo"], default="matched")
    parser.add_argument("--orders", type=Path, default=DEFAULT_ORDERS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rate", type=float, default=2.0)
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()
    asyncio.run(SimRunner(args.strategy, args.orders, args.seed, args.rate, args.speed).run())


if __name__ == "__main__":
    main()
