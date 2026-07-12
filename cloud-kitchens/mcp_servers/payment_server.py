#!/usr/bin/env python
"""MCP server — Payment service."""
import httpx
from mcp.server.fastmcp import FastMCP
from mcp_servers.config import API_BASE, AGENT_TOKENS

mcp = FastMCP("payment-service")
HEADERS = {"X-Agent-Token": AGENT_TOKENS["payment"]}

# Refunds above this threshold require a prior approval event in the RunTrace
REFUND_APPROVAL_THRESHOLD_CENTS = 2000


@mcp.tool()
async def authorize_payment(order_id: str, amount_cents: int, currency: str = "USD") -> dict:
    """Authorize a payment for an order. Returns authorization result."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{API_BASE}/payments/",
            json={"order_id": order_id, "amount": amount_cents / 100, "currency": currency},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def get_payment(payment_id: str) -> dict:
    """Retrieve payment record by ID."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/payments/{payment_id}", headers=HEADERS)
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def refund_payment(payment_id: str, amount_cents: int, reason: str) -> dict:
    """
    Issue a refund. Amounts above REFUND_APPROVAL_THRESHOLD_CENTS (20.00 USD) must
    have a prior Approval.request in the agent's RunTrace — the REST layer enforces
    this via the scoped token, but the agent must also self-enforce.
    """
    if amount_cents > REFUND_APPROVAL_THRESHOLD_CENTS:
        return {
            "error": "approval_required",
            "message": f"Refunds above ${REFUND_APPROVAL_THRESHOLD_CENTS/100:.2f} require supervisor approval first.",
            "threshold_cents": REFUND_APPROVAL_THRESHOLD_CENTS,
        }
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{API_BASE}/payments/{payment_id}/refund",
            json={"amount": amount_cents / 100, "reason": reason},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    mcp.run()
