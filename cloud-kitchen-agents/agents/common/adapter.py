"""FrameworkAdapter protocol + shared runtime (ENGINEERING_DESIGN §5).

Every framework implementation (langgraph/, crewai/, autogen/, agent_sdk/, strands/) subclasses
BaseAdapter and implements build_agents() + run_scenario(). The shared AgentRuntime gives every
adapter identical access to the tool layer, model layer, role specs, and trace — so the ONLY
thing that differs between the 5 implementations is orchestration structure, which is the whole
point of the comparison (PRD §9 unfair-comparison mitigation).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol

from contracts import AgentRoleSpec, RunTrace, ScenarioScript

from .model_client import ModelClient
from .roles import ROLE_SPECS
from .tool_client import ToolClient


@dataclass
class AgentRuntime:
    """Per-agent bundle: role spec + scoped tool client + model client, sharing one trace."""

    spec: AgentRoleSpec
    tools: ToolClient
    model: ModelClient


class FrameworkAdapter(Protocol):
    framework_name: str

    def build_agents(self) -> None: ...
    def connect_mcp(self) -> None: ...
    def run_scenario(self, scenario: ScenarioScript) -> RunTrace: ...


class BaseAdapter:
    """Shared plumbing. Subclasses set framework_name and implement run_scenario()."""

    framework_name: str = "base"

    def __init__(self, transport: str = "inprocess", base_url: str = "http://localhost:8000") -> None:
        self.transport = transport
        self.base_url = base_url
        self.trace: RunTrace = RunTrace(framework=self.framework_name, scenario="")
        self.runtimes: dict[str, AgentRuntime] = {}

    def build_agents(self) -> None:
        for name, spec in ROLE_SPECS.items():
            self.runtimes[name] = AgentRuntime(
                spec=spec,
                tools=ToolClient(spec.name, spec.agent_token, self.trace, self.transport, self.base_url),
                model=ModelClient(spec.model_config_),
            )

    def connect_mcp(self) -> None:
        # In v1 the ToolClient IS the MCP client (registry-backed). A live MCP transport
        # (stdio/websocket to mcp_servers.servers) is a drop-in swap documented per adapter.
        self.trace.add_event("agent_start", detail=f"{self.framework_name}: MCP tool layer connected")

    def new_trace(self, scenario: ScenarioScript) -> RunTrace:
        self.trace = RunTrace(framework=self.framework_name, scenario=scenario.name)
        # rebind tool clients to the fresh trace
        for rt in self.runtimes.values():
            rt.tools.trace = self.trace
        return self.trace

    def rt(self, role: str) -> AgentRuntime:
        return self.runtimes[role]
