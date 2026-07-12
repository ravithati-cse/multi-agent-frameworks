"""Baseline dispatch strategies: Matched and FIFO.

Both are pure functions over (ready_orders, waiting_couriers) -> assignments,
matching the original take-home rubric's rules exactly. The Agentic strategy is
NOT here — it lives in the agent layer (agents/common/dispatch_agent) because it
requires an LLM. These two are the deterministic baselines it is compared against.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class DispatchStrategy(ABC):
    name: str = "base"

    @abstractmethod
    def assign(
        self, ready_order_ids: list[str], waiting_courier_ids: list[str]
    ) -> list[tuple[str, str]]:
        """Return list of (courier_id, order_id) pickups to execute now."""


class MatchedStrategy(DispatchStrategy):
    """1:1 courier-order binding: the courier dispatched for an order picks up
    exactly that order. A pickup happens when that specific courier has arrived
    and that specific order is ready."""

    name = "matched"

    def assign(self, ready_order_ids, waiting_courier_ids):
        # In Matched mode the caller passes couriers whose assigned_order_id is in
        # ready_order_ids; pairing is identity on the shared order id.
        ready = set(ready_order_ids)
        out = []
        for cid, oid in waiting_courier_ids:  # here couriers carry their bound order
            if oid in ready:
                out.append((cid, oid))
        return out


class FIFOStrategy(DispatchStrategy):
    """Earliest-arrived courier gets the next-available (earliest-ready) order.
    Ties broken deterministically by id ordering."""

    name = "fifo"

    def assign(self, ready_order_ids, waiting_courier_ids):
        # waiting_courier_ids: list of courier ids in arrival order (earliest first)
        # ready_order_ids: list of order ids in ready order (earliest first)
        pairs = []
        couriers = list(waiting_courier_ids)
        orders = list(ready_order_ids)
        while couriers and orders:
            pairs.append((couriers.pop(0), orders.pop(0)))
        return pairs


def make_strategy(name: str) -> DispatchStrategy:
    name = name.lower()
    if name == "matched":
        return MatchedStrategy()
    if name == "fifo":
        return FIFOStrategy()
    raise ValueError(f"Unknown baseline strategy: {name!r} (agentic lives in the agent layer)")
