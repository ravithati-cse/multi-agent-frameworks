"""
Wire up agent event subscriptions here.
Call setup_event_handlers() at app startup (see app/main.py).
"""
import logging
from app.core.events import bus, DomainEvent
import agents.stubs.order_agent      # noqa: F401 — triggers @register
import agents.stubs.kitchen_agent    # noqa: F401
import agents.stubs.inventory_agent  # noqa: F401

logger = logging.getLogger(__name__)


async def _on_order_created(event: DomainEvent) -> None:
    """Trigger kitchen routing agent when an order arrives."""
    logger.info("[agent-hook] order.created → kitchen router | order_id=%s", event.data.get("order_id"))
    # TODO: await KitchenRoutingAgent().run(event.data)


async def _on_inventory_low(event: DomainEvent) -> None:
    """Trigger restock agent when stock dips below reorder level."""
    logger.warning("[agent-hook] inventory.low → restock agent | item_id=%s qty=%s",
                   event.data.get("item_id"), event.data.get("quantity"))
    # TODO: await InventoryRestockAgent().run(event.data)


async def _on_order_ready(event: DomainEvent) -> None:
    """Trigger delivery dispatch agent when order is ready."""
    if event.data.get("status") == "ready":
        logger.info("[agent-hook] order.status_changed=ready → dispatch agent | order_id=%s",
                    event.data.get("order_id"))
        # TODO: await DeliveryDispatchAgent().run(event.data)


def setup_event_handlers() -> None:
    """Register all agent event listeners. Called once at startup."""
    bus.subscribe("order.created", _on_order_created)
    bus.subscribe("inventory.low", _on_inventory_low)
    bus.subscribe("order.status_changed", _on_order_ready)
    logger.info("Agent event handlers registered.")
