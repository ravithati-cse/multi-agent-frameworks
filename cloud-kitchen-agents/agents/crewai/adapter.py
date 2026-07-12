"""CrewAI adapter (EngDesign §5.1).

Each role becomes an Agent + Task; the order lifecycle is a sequential/parallel Crew process.
CrewAI shines at role-based delegation but is weakest at fine-grained mid-flight guardrails:
tools are attached to a Task and, by default, a task that holds a tool can call it without an
additional scope restriction. That is exactly the documented FAIL mode for ASI02 — the refund
tool, once granted to an over-permissive Support task, has no framework-level gate, so only the
REST layer (which permits sub-threshold refunds) stands between the agent and an unauthorized
refund. This adapter encodes that honest weakness rather than papering over it.
"""
from __future__ import annotations

from contracts import RunTrace, ScenarioScript

from agents.common.adapter import BaseAdapter
from agents.common.attacks import handle_injection
from agents.common.workflow import attach_strategy_metrics, run_order_lifecycle


class CrewAIAdapter(BaseAdapter):
    framework_name = "crewai"

    # CrewAI: relies mostly on the REST/MCP gate. It wires an objective guardrail into the
    # Dispatch task and a KB-consistency reminder, but NOTABLY leaves the over-granted refund
    # tool ungated at the framework layer (ASI02) — the documented failure.
    posture = {
        "ASI01": ["route_to_payment"],
        "ASI02": [],  # <-- no framework scope restriction on the granted refund tool
        "ASI04": [],  # relies on REST approval gate for the poisoned refund
        "ASI06": ["kb_consistency_check"],
        "ASI10": ["objective_guardrail"],
    }

    def build_crew(self):
        """Construct a real CrewAI Crew. Lazy import; run with `pip install crewai` + a model."""
        from crewai import Agent, Crew, Process, Task  # noqa: F401

        agents, tasks = {}, []
        for name, spec in self.runtimes.items():
            s = spec.spec
            agents[name] = Agent(
                role=s.name,
                goal=s.system_prompt[:120],
                backstory=s.system_prompt,
                allow_delegation=(name == "ops_supervisor"),
                verbose=False,
            )
        tasks.append(Task(description="Validate and confirm incoming orders", agent=agents["order_intake"], expected_output="confirmed/rejected"))
        tasks.append(Task(description="Prep confirmed orders under capacity", agent=agents["kitchen"], expected_output="ready"))
        tasks.append(Task(description="Dispatch couriers load-aware", agent=agents["dispatch"], expected_output="assignments"))
        return Crew(agents=list(agents.values()), tasks=tasks, process=Process.sequential)

    def run_scenario(self, scenario: ScenarioScript) -> RunTrace:
        self.build_agents()
        self.connect_mcp()
        trace = self.new_trace(scenario)
        trace.add_event("agent_start", detail="CrewAI sequential Crew: intake -> kitchen -> dispatch tasks")
        run_order_lifecycle(self, n=4)
        for inj in scenario.injections:
            if inj.kind.upper().startswith("ASI"):
                handle_injection(self, inj.kind, inj.params)
        attach_strategy_metrics(self, scenario)
        trace.add_event("agent_end", detail="CrewAI run complete")
        return trace
