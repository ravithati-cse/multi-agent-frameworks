"""Scoped-token auth for the REST/MCP tool layer (ENGINEERING_DESIGN §4a.1, Epic H3).

Each agent role is issued a static per-role bearer token whose scopes list exactly
the endpoints it may call. An out-of-scope call is rejected with 403 at the API layer,
regardless of what the LLM "intends" to do. This is the mechanism the ASI02 (Tool
Misuse) scenario actually exercises — the boundary is real, not a convention.

Auth scheme decision (PRD/EngDesign open question): static per-role API keys. Simple,
reproducible, and identical across all 5 framework runs so privilege-boundary results
aren't an artifact of inconsistent credentials.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# A scope is "<service>:<action>", e.g. "payment:refund". "*" wildcards within a service.
ROLE_SCOPES: dict[str, set[str]] = {
    "order_intake": {"menu:read", "menu:validate", "inventory:check", "payment:authorize", "order:write", "order:read"},
    "kitchen": {"kitchen:*", "order:read", "order:write"},
    "inventory": {"inventory:*", "order:read"},
    "dispatch": {"courier:*", "kitchen:read", "order:read"},
    "payment": {"payment:charge", "payment:refund", "payment:authorize", "approval:request", "order:read"},
    "support": {"knowledge:query", "order:read", "ticket:create", "ticket:escalate"},
    "ops_supervisor": {"metrics:read", "order:read", "kitchen:read", "courier:read", "inventory:check", "alert:raise"},
    "customer": {"order:write", "order:read", "message:send"},
    # admin token used by the engine/harness for setup only
    "admin": {"*"},
}

# Static per-role tokens. In a real system these would be secrets; here they are fixed
# so every framework run uses identical credentials (EngDesign §12).
ROLE_TOKENS: dict[str, str] = {role: f"tok_{role}_v1" for role in ROLE_SCOPES}
TOKEN_TO_ROLE: dict[str, str] = {v: k for k, v in ROLE_TOKENS.items()}


@dataclass
class Principal:
    role: str
    scopes: set[str] = field(default_factory=set)

    def allows(self, required: str) -> bool:
        if "*" in self.scopes:
            return True
        service = required.split(":", 1)[0]
        if f"{service}:*" in self.scopes:
            return True
        return required in self.scopes


class ScopeError(Exception):
    def __init__(self, role: str, required: str) -> None:
        self.role = role
        self.required = required
        super().__init__(f"role '{role}' lacks scope '{required}'")


def principal_for_token(token: str | None) -> Principal | None:
    if not token:
        return None
    token = token.replace("Bearer ", "").strip()
    role = TOKEN_TO_ROLE.get(token)
    if role is None:
        return None
    return Principal(role=role, scopes=set(ROLE_SCOPES[role]))


def check_scope(token: str | None, required: str) -> Principal:
    """Raise ScopeError (=> 403) if the token's role lacks the required scope."""
    p = principal_for_token(token)
    if p is None:
        raise ScopeError(role="<unknown>", required=required)
    if not p.allows(required):
        raise ScopeError(role=p.role, required=required)
    return p
