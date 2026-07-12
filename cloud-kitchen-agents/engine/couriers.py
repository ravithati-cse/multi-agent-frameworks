"""CourierSim — dispatches a courier on order receipt; arrival ~ Uniform(3,15)s."""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone

from contracts import Courier, Event, Order

from .kitchen import TIME_SCALE


class CourierSim:
    def __init__(self, bus, seed: int = 42) -> None:
        self.bus = bus
        self.rng = random.Random(seed + 1)
        self.couriers: dict[str, Courier] = {}
        self._counter = 0
        self._tasks: set[asyncio.Task] = set()
        self._no_show: set[str] = set()  # courier ids forced to never arrive (ASI/exception)

    def force_no_show(self, courier_id: str) -> None:
        self._no_show.add(courier_id)

    def pool_status(self) -> dict[str, int]:
        idle = dispatched = arrived = 0
        for c in self.couriers.values():
            if c.arrived_at is not None:
                arrived += 1
            elif c.assigned_order_id is not None:
                dispatched += 1
            else:
                idle += 1
        return {"idle": idle, "dispatched": dispatched, "arrived": arrived}

    async def on_order_received(self, event: Event) -> None:
        order = Order(**event.payload["order"])
        cid = f"C{self._counter:04d}"
        self._counter += 1
        courier = Courier(id=cid, dispatched_at=datetime.now(timezone.utc), assigned_order_id=order.id)
        self.couriers[cid] = courier
        await self.bus.publish(
            Event(type="CourierDispatched", payload={"courier_id": cid, "order_id": order.id})
        )
        delay = self.rng.uniform(3, 15)
        task = asyncio.create_task(self._arrive(cid, delay))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _arrive(self, courier_id: str, delay_s: float) -> None:
        await asyncio.sleep(delay_s * TIME_SCALE)
        if courier_id in self._no_show:
            await self.bus.publish(
                Event(type="CourierNoShow", payload={"courier_id": courier_id})
            )
            return
        courier = self.couriers[courier_id]
        courier.arrived_at = datetime.now(timezone.utc)
        await self.bus.publish(
            Event(
                type="CourierArrived",
                payload={"courier_id": courier_id, "order_id": courier.assigned_order_id},
            )
        )

    async def drain(self) -> None:
        if self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)
