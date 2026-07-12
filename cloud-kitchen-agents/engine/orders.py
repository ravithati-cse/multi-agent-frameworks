"""OrderGenerator — emits orders at a configurable rate, deterministic given a seed."""
from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path
from typing import Optional

from contracts import Event, Order

# A tiny synthetic menu used when no orders file is supplied.
_SYNTHETIC_MENU = [
    ("Margherita Pizza", ["pizza_dough", "tomato", "mozzarella"], 12, 1450),
    ("Chicken Burrito", ["tortilla", "chicken", "rice", "beans"], 8, 1100),
    ("Pad Thai", ["noodles", "egg", "peanut", "shrimp"], 10, 1300),
    ("Caesar Salad", ["lettuce", "crouton", "parmesan"], 4, 900),
    ("Beef Ramen", ["ramen", "beef", "egg", "scallion"], 11, 1500),
    ("Veggie Bowl", ["quinoa", "avocado", "chickpea"], 6, 1050),
]


class OrderGenerator:
    def __init__(
        self,
        bus,
        rate_per_s: float = 2.0,
        seed: int = 42,
        orders_file: Optional[str] = None,
        station_names: Optional[list[str]] = None,
    ) -> None:
        self.bus = bus
        self.rate_per_s = rate_per_s
        self.rng = random.Random(seed)
        self.orders_file = orders_file
        self.station_names = station_names or ["grill", "fry", "salad"]
        self._counter = 0
        self.rate_multiplier = 1.0  # RushSpike adjusts this live

    def _load_file_orders(self) -> list[Order]:
        data = json.loads(Path(self.orders_file).read_text())
        orders: list[Order] = []
        for i, row in enumerate(data):
            orders.append(
                Order(
                    id=row.get("id", f"O{i:04d}"),
                    name=row.get("name", f"order-{i}"),
                    items=row.get("items", []),
                    prep_time_s=int(row.get("prepTime", row.get("prep_time_s", 6))),
                    total_cents=int(row.get("total_cents", 1000)),
                )
            )
        return orders

    def _synthetic_order(self) -> Order:
        name, items, prep, cents = self.rng.choice(_SYNTHETIC_MENU)
        oid = f"O{self._counter:04d}"
        self._counter += 1
        return Order(
            id=oid,
            name=name,
            items=list(items),
            prep_time_s=prep,
            total_cents=cents,
            station=self.rng.choice(self.station_names),
        )

    async def run(self, duration_s: float) -> None:
        """Emit OrderReceived events for duration_s seconds."""
        preset = self._load_file_orders() if self.orders_file else None
        idx = 0
        elapsed = 0.0
        while elapsed < duration_s:
            interval = 1.0 / max(self.rate_per_s * self.rate_multiplier, 0.001)
            if preset is not None:
                if idx >= len(preset):
                    break
                order = preset[idx]
                idx += 1
            else:
                order = self._synthetic_order()
            await self.bus.publish(Event(type="OrderReceived", payload={"order": order.model_dump(mode="json")}))
            await asyncio.sleep(interval)
            elapsed += interval
