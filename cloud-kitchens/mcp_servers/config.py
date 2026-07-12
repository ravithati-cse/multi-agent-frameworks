"""Shared config for all MCP servers — base URL and per-role tokens."""

API_BASE = "http://localhost:8000/api/v1"

# Must match app/core/auth.py AGENT_TOKENS
AGENT_TOKENS = {
    "order_intake":   "tok-order-intake",
    "kitchen":        "tok-kitchen",
    "inventory":      "tok-inventory",
    "dispatch":       "tok-dispatch",
    "payment":        "tok-payment",
    "support":        "tok-support",
    "ops_supervisor": "tok-ops-supervisor",
    "admin":          "tok-admin",
}

CHROMA_PATH = "mcp_servers/chroma_db"
KB_COLLECTION = "kitchen_kb"
