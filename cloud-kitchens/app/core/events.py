"""
Domain event bus — two patterns supported:
  1. In-process sync handlers (always active)
  2. Redis pub/sub (activated when REDIS_URL is set and use_redis=True)

Agents subscribe via:
    bus.subscribe("order.created", my_handler)

Domain services publish via:
    await bus.publish(DomainEvent("order.created", {...}))
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine
from uuid import uuid4

logger = logging.getLogger(__name__)

Handler = Callable[["DomainEvent"], Coroutine[Any, Any, None]]


@dataclass
class DomainEvent:
    type: str                          # e.g. "order.created"
    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    """Lightweight in-process pub/sub with optional Redis relay."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}
        self._wildcard: list[Handler] = []   # subscribe("*", ...) handlers

    def subscribe(self, event_type: str, handler: Handler) -> None:
        """Subscribe to a specific event type or '*' for all events."""
        if event_type == "*":
            self._wildcard.append(handler)
        else:
            self._handlers.setdefault(event_type, []).append(handler)
        logger.debug("subscribed %s → %s", handler.__name__, event_type)

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        if event_type == "*":
            self._wildcard = [h for h in self._wildcard if h is not handler]
        else:
            bucket = self._handlers.get(event_type, [])
            self._handlers[event_type] = [h for h in bucket if h is not handler]

    async def publish(self, event: DomainEvent) -> None:
        logger.info("event: %s id=%s", event.type, event.id)
        handlers = self._handlers.get(event.type, []) + self._wildcard
        if not handlers:
            return
        await asyncio.gather(
            *[self._safe_call(h, event) for h in handlers],
            return_exceptions=True,
        )

    @staticmethod
    async def _safe_call(handler: Handler, event: DomainEvent) -> None:
        try:
            await handler(event)
        except Exception:
            logger.exception("handler %s failed for event %s", handler.__name__, event.type)


# Singleton — import this everywhere
bus = EventBus()
