#!/usr/bin/env python
"""MCP server — Inventory service."""
import httpx
from mcp.server.fastmcp import FastMCP
from mcp_servers.config import API_BASE, AGENT_TOKENS

mcp = FastMCP("inventory-service")
HEADERS = {"X-Agent-Token": AGENT_TOKENS["inventory"]}


@mcp.tool()
async def check_stock(kitchen_id: str) -> list[dict]:
    """Return current stock levels for a kitchen, including low-stock flags."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/inventory/kitchen/{kitchen_id}", headers=HEADERS)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def get_low_stock(kitchen_id: str) -> list[dict]:
    """Return only items that are at or below their reorder level."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/inventory/kitchen/{kitchen_id}/low-stock", headers=HEADERS)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def adjust_stock(item_id: str, delta: float) -> dict:
    """Adjust stock quantity. delta > 0 = restock, delta < 0 = consume."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{API_BASE}/inventory/{item_id}/adjust",
            json={"delta": delta},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    mcp.run()
