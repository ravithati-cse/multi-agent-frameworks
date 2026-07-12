"""ToolClient — the single MCP-tool call path used by every framework adapter.

All 5 frameworks call tools through this client, so there is no per-framework tool-binding
code (Epic D1/H2). It resolves a tool name via the shared registry, attaches the caller's
scoped token, executes the call against the REST tool layer, and records a ToolCallRecord
into the active RunTrace (Epic D3) — including the security-relevant flags the EvalHarness
inspects (scope denial, approval requirement, approval presence).

Two transports:
  * "http"      — real network calls to the running services (production-style).
  * "inprocess" — FastAPI TestClient, no network. Used for offline/CI runs and the
                  reproducible security matrix. Same auth + guardrails, zero flakiness.

A tool call may be routed to a *rogue* MCP server (ASI04) via `register_rogue`. Rogue tools
are flagged unverified in the trace so the EvalHarness can check the agent didn't act on
poisoned third-party data.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Optional

from contracts import RunTrace, ToolCallRecord
from mcp_servers.registry import TOOLS, ToolDef, fill_path
from services.state import STORE


class ToolClient:
    def __init__(
        self,
        agent_name: str,
        token: str,
        trace: RunTrace,
        transport: str = "inprocess",
        base_url: str = "http://localhost:8000",
    ) -> None:
        self.agent_name = agent_name
        self.token = token
        self.trace = trace
        self.transport = os.environ.get("CKA_TRANSPORT", transport)
        self.base_url = base_url
        self._rogue: dict[str, Callable[..., dict]] = {}
        self._client = None
        if self.transport == "inprocess":
            from fastapi.testclient import TestClient
            from services.app import app

            self._client = TestClient(app)

    # ---- rogue MCP server injection (ASI04) --------------------------------
    def register_rogue(self, name: str, fn: Callable[..., dict]) -> None:
        self._rogue[name] = fn

    def available_tool_names(self) -> list[str]:
        return list(TOOLS) + list(self._rogue)

    # ---- core call ----------------------------------------------------------
    def call(self, tool_name: str, **args: Any) -> dict:
        if tool_name in self._rogue:
            result = self._rogue[tool_name](**args)
            rec = ToolCallRecord(
                agent=self.agent_name, tool=tool_name, args=args, result=result, ok=True,
            )
            rec.result = result
            # mark provenance for the harness
            self.trace.add_tool_call(rec)
            self.trace.add_event(
                "tool_call", self.agent_name, f"ROGUE tool {tool_name}",
                tool=tool_name, provenance="unverified-third-party",
            )
            return {"status_code": 200, "data": result, "provenance": "unverified-third-party"}

        tdef = TOOLS.get(tool_name)
        if tdef is None:
            raise ValueError(f"unknown tool {tool_name!r}")

        approval_present = False
        if tdef.name == "payment.refund":
            approval_present = bool(STORE.approvals.get(args.get("order_id", ""), {}).get("approved"))

        resp = self._http(tdef, args)
        sc = resp["status_code"]
        rec = ToolCallRecord(
            agent=self.agent_name,
            tool=tool_name,
            args=args,
            result=resp.get("data"),
            ok=200 <= sc < 300,
            error=None if 200 <= sc < 300 else str(resp.get("data")),
            denied_by_scope=(sc == 403),
            required_approval=(sc == 428) or (tdef.name == "payment.refund"),
            approval_present=approval_present,
        )
        self.trace.add_tool_call(rec)
        self.trace.add_event(
            "tool_call", self.agent_name, f"{tool_name} -> {sc}",
            tool=tool_name, status=sc,
        )
        return resp

    def _http(self, tdef: ToolDef, args: dict) -> dict:
        path = fill_path(tdef.path, args)
        body = {k: args[k] for k in tdef.body_keys if k in args}
        headers = {"Authorization": f"Bearer {self.token}"}
        if self.transport == "inprocess":
            if tdef.method == "GET":
                r = self._client.get(path, headers=headers)
            else:
                r = self._client.request(tdef.method, path, json=body, headers=headers)
        else:
            import httpx

            url = self.base_url.rstrip("/") + path
            with httpx.Client(timeout=10) as c:
                if tdef.method == "GET":
                    r = c.get(url, headers=headers)
                else:
                    r = c.request(tdef.method, url, json=body, headers=headers)
        out: dict = {"status_code": r.status_code}
        try:
            out["data"] = r.json()
        except Exception:
            out["data"] = {"text": r.text}
        return out
