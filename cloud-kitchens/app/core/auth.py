"""
Scoped API key auth for agent roles.

Each agent role is issued a static token at startup. Endpoints that agents
call enforce scope via the require_scope() dependency. The admin token bypasses
all checks (local dev / testing only).

Header: X-Agent-Token: <token>
"""
from fastapi import Header, HTTPException

# token → role mapping (generated once at startup; swap for short-lived tokens in prod)
AGENT_TOKENS: dict[str, str] = {
    "tok-order-intake":    "order_intake",
    "tok-kitchen":         "kitchen",
    "tok-inventory":       "inventory",
    "tok-dispatch":        "dispatch",
    "tok-payment":         "payment",
    "tok-support":         "support",
    "tok-ops-supervisor":  "ops_supervisor",
    "tok-admin":           "admin",
}

# role → set of allowed path prefixes (checked as startswith)
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "order_intake":   {"/api/v1/menu", "/api/v1/inventory/check", "/api/v1/payments/authorize", "/api/v1/orders"},
    "kitchen":        {"/api/v1/kitchen", "/api/v1/orders"},
    "inventory":      {"/api/v1/inventory"},
    "dispatch":       {"/api/v1/delivery", "/api/v1/orders"},
    "payment":        {"/api/v1/payments"},
    "support":        {"/api/v1/orders", "/api/v1/tickets", "/api/v1/menu"},
    "ops_supervisor": {"/api/v1/"},   # read-only enforced by HTTP method check
    "admin":          {"/api/v1/"},
}


def require_scope(*allowed_roles: str):
    """
    FastAPI dependency factory. Usage:

        @router.post("/charge", dependencies=[Depends(require_scope("payment", "admin"))])
    """
    async def _check(x_agent_token: str = Header(default="")):
        if not x_agent_token:
            raise HTTPException(401, "X-Agent-Token header required")
        role = AGENT_TOKENS.get(x_agent_token)
        if role is None:
            raise HTTPException(403, "Invalid agent token")
        if role not in allowed_roles and role != "admin":
            raise HTTPException(403, f"Role '{role}' not allowed here (need one of {allowed_roles})")
    return _check
