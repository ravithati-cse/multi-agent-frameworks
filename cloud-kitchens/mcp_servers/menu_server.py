#!/usr/bin/env python
"""MCP server — Menu service. Run as: python mcp_servers/menu_server.py"""
import httpx
from mcp.server.fastmcp import FastMCP
from mcp_servers.config import API_BASE, AGENT_TOKENS

mcp = FastMCP("menu-service")
HEADERS = {"X-Agent-Token": AGENT_TOKENS["order_intake"]}


@mcp.tool()
async def list_menu_items() -> list[dict]:
    """Return all available menu items."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/menu/", headers=HEADERS)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def validate_menu_item(item_id: str) -> dict:
    """Check whether a specific menu item exists and is available."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/menu/{item_id}", headers=HEADERS)
        if r.status_code == 404:
            return {"valid": False, "item_id": item_id}
        r.raise_for_status()
        return {"valid": True, **r.json()}


if __name__ == "__main__":
    mcp.run()
