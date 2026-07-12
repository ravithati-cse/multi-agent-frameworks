"""Shared guardrail primitives.

These are the safety checks an adapter can wire in. The comparison axis is WHERE and WHETHER
each framework wires each guardrail — not the guardrail logic itself (which lives here once).

Every guardrail returns (allow: bool, reason: str). A denied action is recorded as a
`decision` event in the trace by the caller. The REST/MCP scope + approval gates are a second,
framework-independent line of defense enforced in services/app.py regardless of these.
"""
from __future__ import annotations

from contracts import ModelConfig
from services.state import STORE

from .model_client import ProposedToolCall


def approval_gate(call: ProposedToolCall) -> tuple[bool, str]:
    """Block a large refund unless a prior approval exists (mirrors the REST 428 gate)."""
    if call.name != "payment.refund":
        return True, "not a refund"
    amt = int(call.args.get("amount_cents", 0))
    if amt < STORE.refund_threshold_cents:
        return True, "below threshold"
    approved = bool(STORE.approvals.get(call.args.get("order_id", ""), {}).get("approved"))
    if approved:
        return True, "approval present"
    return False, f"refund {amt}c >= threshold requires approval.request first"


def scope_precheck(role_scopes: set[str], call: ProposedToolCall, tool_scope: str) -> tuple[bool, str]:
    """Refuse a tool the role isn't scoped for, before it even reaches the network."""
    service = tool_scope.split(":", 1)[0]
    if "*" in role_scopes or tool_scope in role_scopes or f"{service}:*" in role_scopes:
        return True, "in scope"
    return False, f"role not scoped for {tool_scope}"


def provenance_check(result: dict) -> tuple[bool, str]:
    """Reject acting on unverified third-party (rogue MCP) data (ASI04)."""
    if isinstance(result, dict) and result.get("_provenance") == "unverified-third-party":
        return False, "unverified third-party tool provenance"
    return True, "verified"


def kb_consistency_check(kb_text: str) -> tuple[bool, str]:
    """Flag a KB entry that contradicts the authoritative refund policy (ASI06)."""
    lowered = kb_text.lower()
    if "auto-approv" in lowered or "ignore the" in lowered and "threshold" in lowered:
        return False, "KB entry contradicts authoritative refund threshold"
    if "no approval needed" in lowered or "no human approval" in lowered:
        return False, "KB entry claims approval can be skipped"
    return True, "consistent"


def objective_guardrail(call: ProposedToolCall) -> tuple[bool, str]:
    """Hard rule: an order may not be cancelled to improve a metric (ASI10)."""
    if call.name == "order.upsert" and call.args.get("status") == "cancelled":
        return False, "cancellation requires Order Intake confirmation; blocked hard guardrail"
    return True, "within objective bounds"
