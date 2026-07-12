"""MetricsCollector — computes food-wait and courier-wait, per pickup + running avg."""
from __future__ import annotations

from datetime import datetime

from contracts import Event, Metrics


def _ms(a: datetime, b: datetime) -> float:
    return (a - b).total_seconds() * 1000.0


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


class MetricsCollector:
    def __init__(self, strategy: str = "matched", verbose: bool = True) -> None:
        self.strategy = strategy
        self.verbose = verbose
        self.food_waits_ms: list[float] = []
        self.courier_waits_ms: list[float] = []

    def snapshot(self) -> Metrics:
        n = len(self.food_waits_ms)
        return Metrics(
            avg_food_wait_ms=sum(self.food_waits_ms) / n if n else 0.0,
            avg_courier_wait_ms=(
                sum(self.courier_waits_ms) / len(self.courier_waits_ms)
                if self.courier_waits_ms
                else 0.0
            ),
            sample_count=n,
            strategy=self.strategy,
        )

    async def on_pickup(self, event: Event) -> None:
        """OrderPickedUp carries: order_ready_at, courier_dispatched_at, courier_arrived_at, picked_up_at."""
        p = event.payload
        picked = _parse(p["picked_up_at"])
        # food wait = time between food ready and pickup
        if p.get("ready_at"):
            self.food_waits_ms.append(_ms(picked, _parse(p["ready_at"])))
        # courier wait = time between courier arrival and pickup
        if p.get("courier_arrived_at"):
            self.courier_waits_ms.append(
                _ms(picked, _parse(p["courier_arrived_at"]))
            )
        if self.verbose:
            m = self.snapshot()
            print(
                f"[metrics] order={p.get('order_id')} "
                f"food_wait={self.food_waits_ms[-1] if self.food_waits_ms else 0:.0f}ms "
                f"courier_wait={self.courier_waits_ms[-1] if self.courier_waits_ms else 0:.0f}ms "
                f"| running avg food={m.avg_food_wait_ms:.0f}ms courier={m.avg_courier_wait_ms:.0f}ms"
            )
