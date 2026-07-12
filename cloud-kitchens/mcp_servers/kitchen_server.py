#!/usr/bin/env python
"""MCP server — Kitchen service."""
import httpx
from mcp.server.fastmcp import FastMCP
from mcp_servers.config import API_BASE, AGENT_TOKENS

mcp = FastMCP("kitchen-service")
HEADERS = {"X-Agent-Token": AGENT_TOKENS["kitchen"]}


@mcp.tool()
async def get_kitchen_status(kitchen_id: str) -> dict:
    """Return current kitchen status, station capacity, and active order count."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/kitchen/{kitchen_id}", headers=HEADERS)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def list_kitchens() -> list[dict]:
    """List all kitchens with their current status."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/kitchen/", headers=HEADERS)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def update_kitchen_status(kitchen_id: str, status: str) -> dict:
    """Update kitchen operational status: open | busy | closed."""
    async with httpx.AsyncClient() as client:
        r = await client.patch(
            f"{API_BASE}/kitchen/{kitchen_id}/status",
            json={"status": status},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    mcp.run()
