"""
SimEventBus — asyncio.Queue-based pub/sub used by all engine components.

All engine mutation happens inside single-threaded asyncio callbacks, so no
locks are needed. External subscribers (agent layer, dashboard) call subscribe()
before the simulation starts.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable

from contracts.models import SimEvent

logger = logging.getLogger(__name__)

Handler = Callable[[SimEvent], Awaitable[None]]


class SimEventBus:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[SimEvent] = asyncio.Queue()
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event: SimEvent) -> None:
        await self._queue.put(event)

    async def dispatch_loop(self) -> None:
        """Drain the queue and fan out to subscribers. Run as a background task."""
        while True:
            event = await self._queue.get()
            handlers = self._subscribers.get(event.type, [])
            for h in handlers:
                try:
                    await h(event)
                except Exception:
                    logger.exception("Handler %s failed for event %s", h, event.type)
            self._queue.task_done()
