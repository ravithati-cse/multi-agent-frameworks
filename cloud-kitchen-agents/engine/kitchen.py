"""KitchenSim — one prep queue per station, capacity-limited, asyncio-timer prep."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from contracts import Event, Order


class KitchenSim:
    def __init__(self, bus, stations: dict[str, int] | None = None) -> None:
        # station name -> max concurrent prep slots
        self.stations = stations or {"grill": 3, "fry": 3, "salad": 2}
        self.bus = bus
        self._semaphores = {s: asyncio.Semaphore(cap) for s, cap in self.stations.items()}
        self._in_prep: dict[str, int] = {s: 0 for s in self.stations}
        self._tasks: set[asyncio.Task] = set()

    def utilization(self) -> dict[str, dict[str, int]]:
        return {
            s: {"in_prep": self._in_prep[s], "capacity": cap}
            for s, cap in self.stations.items()
        }

    def _pick_station(self, order: Order) -> str:
        if order.station and order.station in self.stations:
            return order.station
        # least-loaded station
        return min(self.stations, key=lambda s: self._in_prep[s])

    async def on_order_received(self, event: Event) -> None:
        order = Order(**event.payload["order"])
        station = self._pick_station(order)
        task = asyncio.create_task(self._prep(order, station))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _prep(self, order: Order, station: str) -> None:
        sem = self._semaphores[station]
        async with sem:  # enforces capacity — waits if station full
            self._in_prep[station] += 1
            await self.bus.publish(
                Event(type="OrderPrepping", payload={"order_id": order.id, "station": station})
            )
            try:
                await asyncio.sleep(order.prep_time_s * TIME_SCALE)
            finally:
                self._in_prep[station] -= 1
            order.status = "ready"
            order.station = station
            order.ready_at = datetime.now(timezone.utc)
            await self.bus.publish(
                Event(
                    type="OrderReady",
                    payload={"order": order.model_dump(mode="json"), "station": station},
                )
            )

    async def drain(self) -> None:
        if self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)


# Real-time-but-fast: 1 "prep second" == TIME_SCALE wall seconds.
# Keeps runs quick while preserving relative timing. Override via env if needed.
import os  # noqa: E402

TIME_SCALE = float(os.environ.get("CKA_TIME_SCALE", "0.1"))
