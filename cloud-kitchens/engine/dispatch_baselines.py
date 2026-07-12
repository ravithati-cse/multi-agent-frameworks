"""
Dispatch strategy baselines — TWO strategies to implement (Ravi writes these).

Both strategies receive the same inputs every time a trigger fires:
  ready_orders   : list[Order]   — orders whose status == "ready", in arrival order
  waiting_couriers: list[Courier] — couriers who have arrived but not yet picked up, in arrival order

Both must return a list of (Order, Courier) pairs to match for pickup right now.
Unmatched orders and couriers stay in their lists until the next trigger.

The runner calls do_pickup() for every pair you return, which:
  - sets order.status = "picked_up", order.picked_up_at = now
  - publishes OrderPickedUp with food_wait_ms and courier_wait_ms
  - removes the order and courier from their lists

Strategy descriptions (from the original challenge rubric):

MATCHED
-------
Each order is pre-assigned exactly one courier at the moment the order is
received (before the courier arrives or the order is ready). When a courier
arrives and their assigned order is ready, they pick it up immediately.
If the courier arrives before the order is ready, they wait. If the order is
ready before the courier arrives, it waits. A courier is never re-assigned.

Trigger: called on every CourierArrived AND every OrderReady event.
Hint: the Courier has an assigned_order_id; match on that.

FIFO
----
No pre-assignment. When either an order becomes ready OR a courier arrives,
check if there is both a ready order AND a waiting courier. If yes:
  - assign the earliest-arrived courier to the earliest-ready order.
  - repeat until no more pairs exist.
"Earliest" = by .ready_at for orders, by .arrived_at for couriers.
Ties broken arbitrarily (but keep it deterministic given the same input).

Trigger: called on every CourierArrived AND every OrderReady event.
"""
from __future__ import annotations

from contracts.models import Courier, Order


def matched_strategy(
    ready_orders: list[Order],
    waiting_couriers: list[Courier],
) -> list[tuple[Order, Courier]]:
    """
    Return (order, courier) pairs where courier.assigned_order_id == order.id
    AND both the order is ready AND the courier has arrived.
    """
    ready_index = {o.id: o for o in ready_orders}
    pairs = []
    for courier in waiting_couriers:
        order = ready_index.get(courier.assigned_order_id)
        if order is not None:
            pairs.append((order, courier))
    return pairs


def fifo_strategy(
    ready_orders: list[Order],
    waiting_couriers: list[Courier],
) -> list[tuple[Order, Courier]]:
    """
    Pair earliest-ready order with earliest-arrived courier, repeat until one list empties.
    """
    orders_by_ready = sorted(ready_orders, key=lambda o: o.ready_at)
    couriers_by_arrived = sorted(waiting_couriers, key=lambda c: c.arrived_at)
    return list(zip(orders_by_ready, couriers_by_arrived))
