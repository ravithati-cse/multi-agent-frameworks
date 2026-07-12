"""Simulation — wires OrderGenerator, KitchenSim, CourierSim, a baseline dispatch
strategy, and MetricsCollector onto one EventBus and runs a full real-time pass.

This is the Phase 0 deterministic artifact: no LLM, seeded RNG, reproducible.
The agent layer subscribes to the same EventBus but does not live here.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from contracts import Event, Metrics

from .couriers import CourierSim
from .dispatch_baselines import make_strategy
from .events import EventBus
from .kitchen import KitchenSim
from .metrics import MetricsCollector
from .orders import OrderGenerator


@dataclass
class SimConfig:
    strategy: str = "matched"  # matched | fifo
    duration_s: float = 20.0
    rate_per_s: float = 2.0
    seed: int = 42
    orders_file: Optional[str] = None
    stations: dict[str, int] = field(default_factory=lambda: {"grill": 3, "fry": 3, "salad": 2})
    verbose: bool = True


class Simulation:
    def __init__(self, config: SimConfig, bus: Optional[EventBus] = None) -> None:
        self.config = config
        self.bus = bus or EventBus()
        self.strategy = make_strategy(config.strategy)
        self.gen = OrderGenerator(
            self.bus,
            rate_per_s=config.rate_per_s,
            seed=config.seed,
            orders_file=config.orders_file,
            station_names=list(config.stations),
        )
        self.kitchen = KitchenSim(self.bus, stations=config.stations)
        self.couriers = CourierSim(self.bus, seed=config.seed)
        self.metrics = MetricsCollector(strategy=config.strategy, verbose=config.verbose)

        # pickup bookkeeping
        self._ready_orders: dict[str, dict] = {}      # order_id -> order payload
        self._ready_order_queue: list[str] = []        # ready order arrival order (FIFO)
        self._arrived_couriers: dict[str, dict] = {}   # courier_id -> {order_id, arrived_at}
        self._arrived_courier_queue: list[str] = []    # arrival order (FIFO)
        self._courier_of_order: dict[str, str] = {}    # order_id -> courier_id (Matched)
        self._dispatched_at: dict[str, datetime] = {}  # courier_id -> dispatched_at

        self._wire()

    def _wire(self) -> None:
        b = self.bus
        b.subscribe("OrderReceived", self.kitchen.on_order_received)
        b.subscribe("OrderReceived", self.couriers.on_order_received)
        b.subscribe("OrderReceived", self._log)
        b.subscribe("OrderReady", self._on_ready)
        b.subscribe("OrderReady", self._log)
        b.subscribe("CourierDispatched", self._on_dispatched)
        b.subscribe("CourierDispatched", self._log)
        b.subscribe("CourierArrived", self._on_arrived)
        b.subscribe("CourierArrived", self._log)
        b.subscribe("OrderPickedUp", self.metrics.on_pickup)
        b.subscribe("OrderPickedUp", self._log)

    async def _log(self, event: Event) -> None:
        if not self.config.verbose:
            return
        ts = event.ts.strftime("%H:%M:%S.%f")[:-3]
        print(f"[{ts}] {event.type}: {self._short(event.payload)}")

    @staticmethod
    def _short(payload: dict) -> str:
        if "order" in payload:
            o = payload["order"]
            return f"order={o['id']} ({o['name']})"
        return ", ".join(f"{k}={v}" for k, v in payload.items() if k != "order")

    async def _on_dispatched(self, event: Event) -> None:
        cid = event.payload["courier_id"]
        oid = event.payload["order_id"]
        self._courier_of_order[oid] = cid
        self._dispatched_at[cid] = event.ts

    async def _on_ready(self, event: Event) -> None:
        o = event.payload["order"]
        self._ready_orders[o["id"]] = o
        self._ready_order_queue.append(o["id"])
        await self._try_pickups()

    async def _on_arrived(self, event: Event) -> None:
        cid = event.payload["courier_id"]
        self._arrived_couriers[cid] = {"order_id": event.payload.get("order_id"), "arrived_at": event.ts}
        self._arrived_courier_queue.append(cid)
        await self._try_pickups()

    async def _try_pickups(self) -> None:
        if self.config.strategy == "matched":
            pairs = []
            for oid in list(self._ready_order_queue):
                cid = self._courier_of_order.get(oid)
                if cid and cid in self._arrived_couriers:
                    pairs.append((cid, oid))
        else:  # fifo
            pairs = self.strategy.assign(
                list(self._ready_order_queue), list(self._arrived_courier_queue)
            )
        for cid, oid in pairs:
            await self._execute_pickup(cid, oid)

    async def _execute_pickup(self, courier_id: str, order_id: str) -> None:
        if order_id not in self._ready_orders or courier_id not in self._arrived_couriers:
            return
        order = self._ready_orders.pop(order_id)
        if order_id in self._ready_order_queue:
            self._ready_order_queue.remove(order_id)
        courier = self._arrived_couriers.pop(courier_id)
        if courier_id in self._arrived_courier_queue:
            self._arrived_courier_queue.remove(courier_id)
        now = datetime.now(timezone.utc)
        await self.bus.publish(
            Event(
                type="OrderPickedUp",
                payload={
                    "order_id": order_id,
                    "courier_id": courier_id,
                    "ready_at": order.get("ready_at"),
                    "courier_dispatched_at": self._dispatched_at.get(courier_id, now).isoformat()
                    if isinstance(self._dispatched_at.get(courier_id), datetime)
                    else None,
                    "courier_arrived_at": courier["arrived_at"].isoformat(),
                    "picked_up_at": now.isoformat(),
                },
            )
        )

    async def run(self) -> Metrics:
        if self.config.verbose:
            print(f"=== Simulation start: strategy={self.config.strategy} "
                  f"duration={self.config.duration_s}s rate={self.config.rate_per_s}/s seed={self.config.seed} ===")
        await self.gen.run(self.config.duration_s)
        # let in-flight prep and couriers finish
        await self.kitchen.drain()
        await self.couriers.drain()
        # a couple of settle passes to clear final pickups
        for _ in range(5):
            await self._try_pickups()
            await asyncio.sleep(0.05)
        m = self.metrics.snapshot()
        if self.config.verbose:
            print(f"=== Final: avg_food_wait={m.avg_food_wait_ms:.0f}ms "
                  f"avg_courier_wait={m.avg_courier_wait_ms:.0f}ms samples={m.sample_count} ===")
        return m
