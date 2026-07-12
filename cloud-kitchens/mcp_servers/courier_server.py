#!/usr/bin/env python
"""MCP server — Courier/Delivery pool service."""
import httpx
from mcp.server.fastmcp import FastMCP
from mcp_servers.config import API_BASE, AGENT_TOKENS

mcp = FastMCP("courier-service")
HEADERS = {"X-Agent-Token": AGENT_TOKENS["dispatch"]}


@mcp.tool()
async def dispatch_courier(order_id: str, delivery_address: dict) -> dict:
    """Dispatch a courier for an order. Returns delivery record with estimated arrival."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{API_BASE}/delivery/",
            json={"order_id": order_id, "delivery_address": delivery_address},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def get_delivery_status(delivery_id: str) -> dict:
    """Get current status of a delivery by ID."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/delivery/{delivery_id}", headers=HEADERS)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def list_active_deliveries() -> list[dict]:
    """List all in-flight deliveries (dispatched or en_route)."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/delivery/active", headers=HEADERS)
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    mcp.run()
