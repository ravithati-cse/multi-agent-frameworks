"""
KitchenOpsAgent — monitors kitchen load and adjusts routing.

Responsibilities:
  - Watch kitchen queue depth
  - Rebalance orders across stations
  - Signal when kitchen is overloaded
"""
from __future__ import annotations
from agents.base import BaseAgent, tool
from agents.registry import register


@register
class KitchenOpsAgent(BaseAgent):
    name = "kitchen_ops_agent"
    description = "Monitors kitchen operations: queue depth, station load, overload detection."

    @tool(
        name="get_kitchen_queue",
        description="Return pending + in-prep orders for a kitchen",
        parameters={
            "type": "object",
            "properties": {"kitchen_id": {"type": "string"}},
            "required": ["kitchen_id"],
        },
    )
    async def get_kitchen_queue(self, kitchen_id: str) -> dict:
        return {"kitchen_id": kitchen_id, "queue_depth": 0, "result": "stub"}

    async def run(self, input: dict) -> dict:
        task = input.get("task")
        if task == "check_load":
            return {"kitchen_id": input.get("kitchen_id"), "load": "normal", "result": "stub"}
        return {"error": f"Unknown task: {task}"}
