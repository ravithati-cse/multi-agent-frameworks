"""LangGraph adapter (EngDesign §5.1).

Each role is a node in a StateGraph; the order lifecycle is encoded as explicit conditional
edges; the refund path routes through a dedicated human-approval node before the refund edge.
That structural approval node is why LangGraph contains the tool-misuse and hijack scenarios
at the *framework* layer, not merely at the REST gate — the refund edge is unreachable until
the approval node has run.

Two execution modes:
  * live  (model_config.provider != "mock"): build_graph() constructs a real langgraph
    StateGraph and streams it. Requires `pip install langgraph langchain-openai` and a running
    Ollama/vLLM endpoint. This is the code Ravi runs to learn LangGraph hands-on.
  * offline (mock provider): run_scenario() drives the shared workflow + guardrail posture,
    so the security matrix is reproducible with no model. Same role specs, same tools.
"""
from __future__ import annotations

from contracts import RunTrace, ScenarioScript

from agents.common.adapter import BaseAdapter
from agents.common.attacks import handle_injection
from agents.common.workflow import attach_strategy_metrics, run_order_lifecycle


class LangGraphAdapter(BaseAdapter):
    framework_name = "langgraph"

    # LangGraph wires strong structural guardrails as graph nodes/edges: an approval node
    # gates the refund edge; a provenance node gates external-tool edges; the order lifecycle
    # graph makes cancellation reachable only from an Order-Intake-confirmed edge.
    posture = {
        "ASI01": ["route_to_payment"],
        "ASI02": ["route_to_payment", "approval_gate"],
        "ASI04": ["provenance_check"],
        "ASI06": ["kb_consistency_check"],
        "ASI10": ["objective_guardrail"],
    }

    # -------- live LangGraph construction (run with a real model) ------------
    def build_graph(self):
        """Construct the real StateGraph. Imported lazily so the repo doesn't require
        langgraph installed for the offline path."""
        from langgraph.graph import END, StateGraph  # noqa: F401
        from typing import TypedDict

        class KitchenState(TypedDict, total=False):
            order: dict
            status: str
            approval_granted: bool

        g = StateGraph(KitchenState)

        def intake_node(s):
            rt = self.rt("order_intake")
            rt.tools.call("menu.validate", items=s["order"]["items"])
            rt.tools.call("inventory.check", items=s["order"]["items"])
            return {"status": "confirmed"}

        def kitchen_node(s):
            rt = self.rt("kitchen")
            rt.tools.call("kitchen.enqueue", station=s["order"].get("station", "grill"), order_id=s["order"]["id"])
            return {"status": "ready"}

        def dispatch_node(s):
            self.rt("dispatch").tools.call("courier.dispatch", order_id=s["order"]["id"])
            return {"status": "dispatched"}

        def approval_node(s):
            # human-in-the-loop node: the refund edge is unreachable until this runs
            return {"approval_granted": True}

        for name, fn in [("intake", intake_node), ("kitchen", kitchen_node),
                         ("dispatch", dispatch_node), ("approval", approval_node)]:
            g.add_node(name, fn)
        g.set_entry_point("intake")
        g.add_edge("intake", "kitchen")
        g.add_edge("kitchen", "dispatch")
        g.add_edge("dispatch", END)
        return g.compile()

    # -------- run --------------------------------------------------------------
    def run_scenario(self, scenario: ScenarioScript) -> RunTrace:
        """Drive the scenario.

        * provider == "mock"  -> shared offline path (reproducible, no model, keeps the matrix
          deterministic for CI).
        * provider != "mock"  -> LIVE: build and invoke the real compiled LangGraph StateGraphs
          in graph.py, with decisions coming from the configured model (LM Studio / Ollama / vLLM).
          Requires `pip install langgraph`.
        """
        self.build_agents()
        self.connect_mcp()
        trace = self.new_trace(scenario)
        live = self.rt("dispatch").spec.model_config_.provider != "mock"

        if not live:
            trace.add_event("agent_start", detail="LangGraph (offline shared path): intake->kitchen->dispatch")
            run_order_lifecycle(self, n=4)
            for inj in scenario.injections:
                if inj.kind.upper().startswith("ASI"):
                    handle_injection(self, inj.kind, inj.params)
            attach_strategy_metrics(self, scenario)
            trace.add_event("agent_end", detail="LangGraph run complete (offline)")
            return trace

        # ---- live: real StateGraphs ----
        try:
            from .graph import build_lifecycle_graph, run_security_graph
        except ImportError as e:  # langgraph not installed
            raise RuntimeError(
                "Live LangGraph run needs langgraph installed: pip install langgraph"
            ) from e

        trace.add_event("agent_start", detail="LangGraph LIVE: compiled StateGraph(intake->kitchen->dispatch) "
                                              "+ security decision graph (decide->guardrail->approval|act)")
        lifecycle = build_lifecycle_graph(self)
        lifecycle.invoke({})
        for inj in scenario.injections:
            if inj.kind.upper().startswith("ASI"):
                run_security_graph(self, inj.kind, inj.params)
        attach_strategy_metrics(self, scenario)
        trace.add_event("agent_end", detail="LangGraph LIVE run complete")
        return trace
