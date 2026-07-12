"""Tool registry — the single definition of every MCP tool, wrapping a REST endpoint.

This is the shared tool layer (ENGINEERING_DESIGN §4a.2). Tool *definitions* live here
once, by construction — not per framework. All 5 framework adapters call these same tools
through the ToolClient (agents/common/tool_client.py), so there is no per-framework tool
schema to drift.

Each ToolDef maps an MCP tool name to (HTTP method, path template, required scope). The
FastMCP servers in servers.py are generated directly from this registry, so the "real"
MCP surface and what the agents call can never disagree.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolDef:
    name: str
    service: str
    method: str
    path: str  # may contain {placeholders} filled from args
    scope: str
    description: str
    # which arg keys go in the JSON body (the rest fill path placeholders / query)
    body_keys: tuple[str, ...] = ()


TOOLS: dict[str, ToolDef] = {
    # menu
    "menu.items": ToolDef("menu.items", "menu", "GET", "/menu/items", "menu:read", "List all menu items."),
    "menu.validate": ToolDef("menu.validate", "menu", "POST", "/menu/validate", "menu:validate", "Validate order item ids against the menu.", ("items",)),
    # inventory
    "inventory.check": ToolDef("inventory.check", "inventory", "POST", "/inventory/check", "inventory:check", "Check stock for a list of items.", ("items",)),
    "inventory.reorder": ToolDef("inventory.reorder", "inventory", "POST", "/inventory/reorder", "inventory:reorder", "Reorder stock of an item.", ("item", "qty")),
    # kitchen
    "kitchen.enqueue": ToolDef("kitchen.enqueue", "kitchen", "POST", "/kitchen/{station}/enqueue", "kitchen:enqueue", "Enqueue an order at a station.", ("order_id",)),
    "kitchen.status": ToolDef("kitchen.status", "kitchen", "GET", "/kitchen/{station}/status", "kitchen:read", "Get a station's queue status."),
    "kitchen.markReady": ToolDef("kitchen.markReady", "kitchen", "POST", "/kitchen/{station}/markReady", "kitchen:markReady", "Mark an order ready.", ("order_id",)),
    # courier
    "courier.dispatch": ToolDef("courier.dispatch", "courier", "POST", "/courier/dispatch", "courier:dispatch", "Dispatch a courier for an order.", ("order_id",)),
    "courier.status": ToolDef("courier.status", "courier", "GET", "/courier/{courier_id}/status", "courier:read", "Get a courier's status."),
    # payment
    "payment.authorize": ToolDef("payment.authorize", "payment", "POST", "/payment/authorize", "payment:authorize", "Authorize/hold a payment.", ("order_id", "amount_cents")),
    "payment.charge": ToolDef("payment.charge", "payment", "POST", "/payment/charge", "payment:charge", "Charge an order.", ("order_id", "amount_cents")),
    "payment.refund": ToolDef("payment.refund", "payment", "POST", "/payment/refund", "payment:refund", "Refund an order (>= threshold requires prior approval).", ("order_id", "amount_cents")),
    "approval.request": ToolDef("approval.request", "payment", "POST", "/payment/approval/request", "approval:request", "Request human approval for a refund.", ("order_id", "amount_cents", "approver")),
    # ticketing
    "ticket.create": ToolDef("ticket.create", "ticket", "POST", "/ticket/create", "ticket:create", "Create a support ticket.", ("order_id", "subject", "body")),
    "ticket.escalate": ToolDef("ticket.escalate", "ticket", "POST", "/ticket/escalate", "ticket:escalate", "Escalate a support ticket.", ("ticket_id", "reason")),
    # order store
    "order.upsert": ToolDef("order.upsert", "order", "POST", "/order/upsert", "order:write", "Create/update an order.", ("id", "name", "items", "status", "total_cents")),
    "order.get": ToolDef("order.get", "order", "GET", "/order/{order_id}", "order:read", "Get one order."),
    "order.list": ToolDef("order.list", "order", "GET", "/order", "order:read", "List all orders."),
    # ops
    "metrics.summary": ToolDef("metrics.summary", "metrics", "GET", "/metrics/summary", "metrics:read", "Read run metrics summary."),
    "alert.raise": ToolDef("alert.raise", "ops", "POST", "/alert/raise", "alert:raise", "Raise an ops alert.", ("severity", "message")),
    # knowledge base tool is served by the knowledge MCP server (see knowledge_server.py),
    # registered dynamically at runtime; declared here for name discovery.
    "knowledge.query": ToolDef("knowledge.query", "knowledge", "POST", "/knowledge/query", "knowledge:query", "Query the RAG knowledge base.", ("query", "k")),
}


def tools_for_service(service: str) -> list[ToolDef]:
    return [t for t in TOOLS.values() if t.service == service]


def fill_path(path: str, args: dict) -> str:
    out = path
    for key, val in list(args.items()):
        token = "{" + key + "}"
        if token in out:
            out = out.replace(token, str(val))
    return out
