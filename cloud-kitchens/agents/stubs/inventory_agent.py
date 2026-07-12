"""
InventoryRestockAgent — reacts to low-stock events and drafts purchase orders.

Responsibilities:
  - Receive inventory.low events
  - Decide restock quantities based on usage patterns
  - Draft or auto-submit purchase orders to suppliers
"""
from __future__ import annotations
from agents.base import BaseAgent, tool
from agents.registry import register


@register
class InventoryRestockAgent(BaseAgent):
    name = "inventory_restock_agent"
    description = "Handles low-stock events and generates restock recommendations."

    @tool(
        name="check_low_stock",
        description="List ingredients below reorder level for a kitchen",
        parameters={
            "type": "object",
            "properties": {"kitchen_id": {"type": "string"}},
            "required": ["kitchen_id"],
        },
    )
    async def check_low_stock(self, kitchen_id: str) -> list:
        return []  # TODO: call inventory_tools.check_low_stock(db, kitchen_id)

    @tool(
        name="recommend_restock",
        description="Suggest restock quantities for a list of low items",
        parameters={
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "object"}},
                "days_ahead": {"type": "integer", "default": 7},
            },
            "required": ["items"],
        },
    )
    async def recommend_restock(self, items: list, days_ahead: int = 7) -> list:
        # TODO: LLM + historical usage → restock quantities
        return [{"item_id": i.get("id"), "recommended_qty": 0} for i in items]

    async def run(self, input: dict) -> dict:
        kitchen_id = input.get("kitchen_id")
        low = await self.check_low_stock(kitchen_id=kitchen_id)
        if not low:
            return {"status": "ok", "message": "No low stock items"}
        recs = await self.recommend_restock(items=low)
        return {"status": "action_needed", "recommendations": recs}
