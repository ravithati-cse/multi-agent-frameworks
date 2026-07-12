#!/usr/bin/env python
"""MCP server — Ticketing service (Support agent's primary tool)."""
import httpx
from mcp.server.fastmcp import FastMCP
from mcp_servers.config import API_BASE, AGENT_TOKENS

mcp = FastMCP("ticketing-service")
HEADERS = {"X-Agent-Token": AGENT_TOKENS["support"]}


@mcp.tool()
async def create_ticket(
    customer_id: str,
    category: str,
    description: str,
    order_id: str | None = None,
    priority: str = "medium",
) -> dict:
    """
    Open a new support ticket. category must be one of:
    refund | complaint | inquiry | courier_issue
    """
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{API_BASE}/tickets/",
            json={
                "customer_id": customer_id,
                "category": category,
                "description": description,
                "order_id": order_id,
                "priority": priority,
            },
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def get_ticket(ticket_id: str) -> dict:
    """Retrieve a ticket by ID."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/tickets/{ticket_id}", headers=HEADERS)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def escalate_ticket(ticket_id: str, reason: str) -> dict:
    """Escalate an open ticket to a human supervisor."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{API_BASE}/tickets/{ticket_id}/escalate",
            json={"reason": reason},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def resolve_ticket(ticket_id: str, resolution: str) -> dict:
    """Mark a ticket as resolved with a resolution note."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{API_BASE}/tickets/{ticket_id}/resolve",
            json={"resolution": resolution},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    mcp.run()
