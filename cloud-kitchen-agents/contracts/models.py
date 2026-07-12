"""Shared data contracts — the single source of truth imported by the engine,
the tool layer, and every one of the 5 framework adapters.

Keeping every schema here is what keeps the 5 framework implementations honest:
no framework may redefine an Order, a tool result, or a trace event.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

OrderStatus = Literal[
    "received",
    "confirmed",
    "prepping",
    "ready",
    "picked_up",
    "delivered",
    "cancelled",
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Order(BaseModel):
    id: str
    name: str
    items: list[str] = Field(default_factory=list)
    prep_time_s: int
    status: OrderStatus = "received"
    created_at: datetime = Field(default_factory=_utcnow)
    # engine bookkeeping (ms since epoch style timestamps kept as datetimes)
    ready_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    station: Optional[str] = None
    total_cents: int = 0


class Courier(BaseModel):
    id: str
    dispatched_at: datetime
    arrived_at: Optional[datetime] = None
    assigned_order_id: Optional[str] = None  # set for Matched; null until pickup for FIFO


class Event(BaseModel):
    """Engine-level event flowing on the EventBus."""

    type: str  # OrderReceived, OrderReady, CourierDispatched, CourierArrived, OrderPickedUp, ...
    payload: dict[str, Any] = Field(default_factory=dict)
    ts: datetime = Field(default_factory=_utcnow)


class Metrics(BaseModel):
    avg_food_wait_ms: float = 0.0
    avg_courier_wait_ms: float = 0.0
    sample_count: int = 0
    strategy: str = "matched"


# ---------------------------------------------------------------------------
# Agent-layer contracts
# ---------------------------------------------------------------------------


class ModelConfig(BaseModel):
    """Which model, temperature, and provider endpoint a role runs on.

    The same ModelConfig object is reused verbatim across all 5 framework runs
    for a given role, so the comparison isolates framework effects from model
    effects (PRD §9 model-variability mitigation).
    """

    provider: Literal["mock", "lmstudio", "ollama", "openai", "anthropic", "vllm", "bedrock"] = "ollama"
    model: str = "llama3.1:8b"
    temperature: float = 0.1
    base_url: Optional[str] = None  # OpenAI-compatible endpoint for ollama/vllm
    max_tokens: int = 1024


class AgentRoleSpec(BaseModel):
    """Framework-agnostic definition of one agent role (ENGINEERING_DESIGN §4/§5).

    A framework adapter wires this into native primitives without altering it.
    """

    name: str
    system_prompt: str
    mcp_tools: list[str] = Field(default_factory=list)  # tool names exposed by MCP servers
    agent_token: str = ""  # scoped credential for REST/MCP privilege boundaries
    model_config_: ModelConfig = Field(default_factory=ModelConfig, alias="model_config")
    reads: list[str] = Field(default_factory=list)
    writes: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Trace contracts — every adapter emits these so one comparison matrix works
# ---------------------------------------------------------------------------


class ToolCallRecord(BaseModel):
    agent: str
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    ok: bool = True
    error: Optional[str] = None
    ts: datetime = Field(default_factory=_utcnow)
    # security-relevant flags surfaced by the tool layer
    denied_by_scope: bool = False
    required_approval: bool = False
    approval_present: bool = False


class TraceEvent(BaseModel):
    kind: Literal[
        "agent_start",
        "agent_message",
        "tool_call",
        "handoff",
        "decision",
        "alert",
        "attack_injected",
        "agent_end",
    ]
    agent: str = ""
    detail: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    ts: datetime = Field(default_factory=_utcnow)


class RunTrace(BaseModel):
    """Structured events + tool calls + final state emitted by all 5 adapters."""

    framework: str
    scenario: str
    strategy: str = "agentic"
    started_at: datetime = Field(default_factory=_utcnow)
    finished_at: Optional[datetime] = None
    events: list[TraceEvent] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    final_metrics: Optional[Metrics] = None
    final_orders: list[Order] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def add_event(self, kind: str, agent: str = "", detail: str = "", **data: Any) -> None:
        self.events.append(TraceEvent(kind=kind, agent=agent, detail=detail, data=data))

    def add_tool_call(self, rec: ToolCallRecord) -> None:
        self.tool_calls.append(rec)


# ---------------------------------------------------------------------------
# Scenario contracts
# ---------------------------------------------------------------------------


class ScheduledInjection(BaseModel):
    """A timed injected event on top of the normal order stream (exceptions or attacks)."""

    at_s: float  # seconds after scenario start
    kind: str  # CourierNoShow, MidPrepChange, Stockout, RushSpike, ASI01, ASI02, ASI04, ASI06, ASI10
    params: dict[str, Any] = Field(default_factory=dict)


class ScenarioScript(BaseModel):
    name: str
    seed: int = 42
    duration_s: float = 30.0
    order_rate_per_s: float = 2.0
    load_profile: Literal["steady", "rush", "degraded"] = "steady"
    injections: list[ScheduledInjection] = Field(default_factory=list)
    orders_file: Optional[str] = None
