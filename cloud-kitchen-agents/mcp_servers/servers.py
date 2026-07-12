"""FastMCP servers that wrap the REST tool layer (ENGINEERING_DESIGN §4a.2).

Each REST service becomes a thin MCP server whose tools are generated directly from the
shared registry (registry.py), so the MCP surface can never drift from what agents call.
Agents connect via an MCP client (agents/common/tool_client.py) instead of framework-native
tool decorators — this is the real unifying layer across the 5 frameworks.

The `mcp` package is optional. If it isn't installed, importing this module still works
(so the registry/tests don't need it); only build_mcp_server() requires it. In v1 the
agents talk to the tool layer through the registry-backed ToolClient over REST, which is
the same boundary these MCP servers expose — documented so the comparison stays honest.

Run one server over stdio:
    python -m mcp_servers.servers --service payment
"""
from __future__ import annotations

import argparse
import os

import httpx

from .registry import TOOLS, ToolDef, fill_path

DEFAULT_BASE = os.environ.get("CKA_TOOL_BASE_URL", "http://localhost:8000")


def _http_call(tdef: ToolDef, args: dict, token: str, base_url: str) -> dict:
    url = base_url.rstrip("/") + fill_path(tdef.path, args)
    body = {k: args[k] for k in tdef.body_keys if k in args}
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=10) as c:
        if tdef.method == "GET":
            r = c.get(url, headers=headers)
        else:
            r = c.request(tdef.method, url, json=body, headers=headers)
    out = {"status_code": r.status_code}
    try:
        out["data"] = r.json()
    except Exception:
        out["data"] = {"text": r.text}
    return out


def build_mcp_server(service: str, base_url: str = DEFAULT_BASE):
    """Build a FastMCP server exposing all tools for one service.

    Every tool takes an explicit `agent_token` argument (the scoped credential). The MCP
    server does not itself decide scope — it forwards the token to the REST layer, which is
    where the 403 boundary is enforced. This mirrors real MCP deployments where the tool
    server is a proxy and the resource server owns authz.
    """
    from mcp.server.fastmcp import FastMCP  # optional dependency

    mcp = FastMCP(f"cloud-kitchen-{service}")
    for tdef in TOOLS.values():
        if tdef.service != service:
            continue

        def _make(td: ToolDef):
            async def _tool(agent_token: str, **kwargs) -> dict:
                return _http_call(td, kwargs, agent_token, base_url)

            _tool.__name__ = td.name.replace(".", "_")
            _tool.__doc__ = td.description
            return _tool

        mcp.tool(name=tdef.name, description=tdef.description)(_make(tdef))
    return mcp


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--service", required=True, help="menu|inventory|kitchen|courier|payment|ticket|order|metrics|ops|knowledge")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    args = ap.parse_args()
    server = build_mcp_server(args.service, args.base_url)
    server.run()  # stdio transport
