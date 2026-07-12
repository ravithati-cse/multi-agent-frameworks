"""
OrderManagementAgent — first agent to fully implement.

Responsibilities:
  - Accept new orders and confirm feasibility
  - Route orders to the right kitchen
  - Monitor order status and escalate SLA breaches
"""
from __future__ import annotations
from agents.base import BaseAgent, tool
from agents.registry import register


@register
class OrderManagementAgent(BaseAgent):
    name = "order_management_agent"
    description = "Manages order lifecycle: validation, routing, status tracking, SLA monitoring."

    @tool(
        name="get_order_details",
        description="Fetch full details of an order by ID",
        parameters={
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "UUID of the order"}},
            "required": ["order_id"],
        },
    )
    async def get_order_details(self, order_id: str) -> dict:
        # TODO: inject db session; call order_tools.get_order(db, order_id)
        return {"order_id": order_id, "status": "stub"}

    @tool(
        name="advance_order",
        description="Move an order to the next status step",
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "status": {"type": "string", "enum": ["confirmed", "preparing", "ready", "out_for_delivery", "delivered"]},
            },
            "required": ["order_id", "status"],
        },
    )
    async def advance_order(self, order_id: str, status: str) -> dict:
        return {"order_id": order_id, "new_status": status, "result": "stub"}

    async def run(self, input: dict) -> dict:
        """
        input: {"task": "route_order", "order_id": "...", "kitchen_id": "..."}
        """
        task = input.get("task")
        if task == "route_order":
            # TODO: implement routing logic with LLM
            return {"routed": True, "kitchen_id": input.get("kitchen_id")}
        return {"error": f"Unknown task: {task}"}
