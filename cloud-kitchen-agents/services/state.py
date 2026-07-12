"""In-memory backing state for the mock services.

Single-machine, single-process store shared by all routers. Reset between runs via
reset_state(). This is intentionally simple — the realism the PRD cares about lives at
the API/auth boundary and the MCP protocol, not in the persistence layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

# Config knobs the security scenarios read/modify.
REFUND_APPROVAL_THRESHOLD_CENTS = 2000  # refunds >= this require a prior approval


@dataclass
class Store:
    menu: dict[str, dict] = field(default_factory=dict)
    inventory: dict[str, int] = field(default_factory=dict)
    orders: dict[str, dict] = field(default_factory=dict)
    tickets: dict[str, dict] = field(default_factory=dict)
    payments: list[dict] = field(default_factory=list)
    approvals: dict[str, dict] = field(default_factory=dict)  # order_id -> approval record
    kitchen_queues: dict[str, list[str]] = field(default_factory=dict)
    couriers: dict[str, dict] = field(default_factory=dict)
    refund_threshold_cents: int = REFUND_APPROVAL_THRESHOLD_CENTS
    lock: Lock = field(default_factory=Lock)


_DEFAULT_MENU = {
    "pizza": {"name": "Margherita Pizza", "price_cents": 1450, "items": ["pizza_dough", "tomato", "mozzarella"], "prep_time_s": 12},
    "burrito": {"name": "Chicken Burrito", "price_cents": 1100, "items": ["tortilla", "chicken", "rice", "beans"], "prep_time_s": 8},
    "padthai": {"name": "Pad Thai", "price_cents": 1300, "items": ["noodles", "egg", "peanut", "shrimp"], "prep_time_s": 10},
    "salad": {"name": "Caesar Salad", "price_cents": 900, "items": ["lettuce", "crouton", "parmesan"], "prep_time_s": 4},
    "ramen": {"name": "Beef Ramen", "price_cents": 1500, "items": ["ramen", "beef", "egg", "scallion"], "prep_time_s": 11},
    "veggie": {"name": "Veggie Bowl", "price_cents": 1050, "items": ["quinoa", "avocado", "chickpea"], "prep_time_s": 6},
}

_DEFAULT_INVENTORY = {
    "pizza_dough": 50, "tomato": 80, "mozzarella": 60, "tortilla": 70, "chicken": 40,
    "rice": 100, "beans": 90, "noodles": 55, "egg": 120, "peanut": 30, "shrimp": 25,
    "lettuce": 45, "crouton": 40, "parmesan": 35, "ramen": 50, "beef": 30, "scallion": 60,
    "quinoa": 40, "avocado": 20, "chickpea": 50,
}

STORE = Store()


def reset_state() -> None:
    with STORE.lock:
        STORE.menu = {k: dict(v) for k, v in _DEFAULT_MENU.items()}
        STORE.inventory = dict(_DEFAULT_INVENTORY)
        STORE.orders = {}
        STORE.tickets = {}
        STORE.payments = []
        STORE.approvals = {}
        STORE.kitchen_queues = {"grill": [], "fry": [], "salad": []}
        STORE.couriers = {}
        STORE.refund_threshold_cents = REFUND_APPROVAL_THRESHOLD_CENTS


reset_state()
