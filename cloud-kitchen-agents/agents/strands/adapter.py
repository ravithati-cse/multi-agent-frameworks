"""Strands Agents adapter (EngDesign §5.1, §13).

Model-driven loop: the LLM plans its own steps rather than following a hardcoded graph; tools
are registered with the @tool decorator. Strands natively supports Ollama/LiteLLM providers,
making it the easiest to point at the AMD GPU vLLM/Ollama stack — and the direct migration path
to Bedrock AgentCore (Phase 6). Because the loop is model-driven, Strands leans on explicit
guardrail hooks: this adapter registers an approval hook before refunds, a provenance hook on
external tools, and a hard objective guardrail on cancellation. KB-consistency is left to the
Payment threshold + REST gate, matching how a model-driven loop tends to trust retrieved text.

Live mode: `pip install strands-agents`; set the provider to Ollama/LiteLLM in ModelConfig.
"""
from __future__ import annotations

from contracts import RunTrace, ScenarioScript

from agents.common.adapter import BaseAdapter
from agents.common.attacks import handle_injection
from agents.common.workflow import attach_strategy_metrics, run_order_lifecycle


class StrandsAdapter(BaseAdapter):
    framework_name = "strands"

    posture = {
        "ASI01": ["route_to_payment"],
        "ASI02": ["route_to_payment", "approval_gate"],
        "ASI04": ["provenance_check"],   # explicit provenance hook on external tools
        "ASI06": [],                      # model-driven loop trusts retrieved text -> REST gate
        "ASI10": ["objective_guardrail"],
    }

    def build_agent(self):
        """Construct a real Strands Agent with @tool-registered tools. Lazy import."""
        from strands import Agent, tool  # noqa: F401
        from strands.models.ollama import OllamaModel  # provider example

        @tool
        def dispatch_courier(order_id: str) -> dict:
            return self.rt("dispatch").tools.call("courier.dispatch", order_id=order_id)

        @tool
        def request_approval(order_id: str, amount_cents: int) -> dict:
            return self.rt("payment").tools.call("approval.request", order_id=order_id, amount_cents=amount_cents)

        model = OllamaModel(host="http://localhost:11434", model_id=self.rt("dispatch").spec.model_config_.model)
        return Agent(model=model, tools=[dispatch_courier, request_approval],
                     system_prompt=self.rt("dispatch").spec.system_prompt)

    def run_scenario(self, scenario: ScenarioScript) -> RunTrace:
        self.build_agents()
        self.connect_mcp()
        trace = self.new_trace(scenario)
        trace.add_event("agent_start", detail="Strands model-driven loop with approval + provenance + objective hooks")
        run_order_lifecycle(self, n=4)
        for inj in scenario.injections:
            if inj.kind.upper().startswith("ASI"):
                handle_injection(self, inj.kind, inj.params)
        attach_strategy_metrics(self, scenario)
        trace.add_event("agent_end", detail="Strands run complete")
        return trace
