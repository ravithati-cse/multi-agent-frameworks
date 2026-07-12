"""EventBus — single asyncio.Queue-based pub/sub.

Every engine component publishes typed events here; the agent layer subscribes
to this bus instead of polling, and the dashboard is a read-only subscriber.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable

from contracts import Event

Subscriber = Callable[[Event], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._wildcard: list[Subscriber] = []
        self._history: list[Event] = []
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: str, cb: Subscriber) -> None:
        """Subscribe to a specific event type, or '*' for all events."""
        if event_type == "*":
            self._wildcard.append(cb)
        else:
            self._subscribers[event_type].append(cb)

    @property
    def history(self) -> list[Event]:
        return list(self._history)

    async def publish(self, event: Event) -> None:
        async with self._lock:
            self._history.append(event)
        # deliver to specific subscribers then wildcard subscribers
        for cb in list(self._subscribers.get(event.type, [])) + list(self._wildcard):
            await cb(event)
