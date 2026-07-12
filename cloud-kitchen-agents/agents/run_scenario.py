"""Scenario-runner CLI (Epic D2).

One entry point runs the identical scenario against any of the 5 frameworks and emits the
same RunTrace schema, so downstream comparison tooling (security matrix, dashboard) is
framework-agnostic.

    python -m agents.run_scenario --framework langgraph --scenario steady
    python -m agents.run_scenario --framework crewai --scenario security_all --out trace.json
    python -m agents.run_scenario --framework all --scenario security_all --matrix matrix.json
"""
from __future__ import annotations

import argparse
import importlib
import json

from contracts import RunTrace
from scenarios.library import get_scenario, list_scenarios

FRAMEWORKS = ["langgraph", "crewai", "autogen", "agent_sdk", "strands"]


def load_adapter(framework: str):
    mod = importlib.import_module(f"agents.{framework}")
    return mod.ADAPTER()


def run_one(framework: str, scenario_name: str) -> RunTrace:
    from services.state import reset_state

    reset_state()
    scenario = get_scenario(scenario_name)
    adapter = load_adapter(framework)
    return adapter.run_scenario(scenario)


ASI_SCENARIOS = ["asi01", "asi02", "asi04", "asi06", "asi10"]


def run_security_matrix(frameworks: list[str]) -> dict:
    """Run each framework against each single-ASI scenario in isolation, then build the matrix.
    Isolation per (framework, ASI) keeps one attack's actions out of another's ledger check."""
    from security.eval_harness import build_matrix

    cell_traces: dict[str, dict[str, RunTrace]] = {}
    for fw in frameworks:
        cell_traces[fw] = {}
        for asi in ASI_SCENARIOS:
            trace = run_one(fw, asi)
            code = asi.upper()
            cell_traces[fw][code] = trace
    return build_matrix(cell_traces)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--framework", default="langgraph", help="one of: " + ", ".join(FRAMEWORKS) + ", or 'all'")
    ap.add_argument("--scenario", default="steady", help="scenario name; see --list")
    ap.add_argument("--list", action="store_true", help="list available scenarios and exit")
    ap.add_argument("--out", default=None, help="write the RunTrace JSON here")
    ap.add_argument("--matrix", default=None, help="with --framework all, write the security matrix JSON here")
    args = ap.parse_args()

    if args.list:
        print("Scenarios:", ", ".join(list_scenarios()))
        return

    frameworks = FRAMEWORKS if args.framework == "all" else [args.framework]

    if args.matrix:
        from security.eval_harness import render_matrix_text

        matrix = run_security_matrix(frameworks)
        print(render_matrix_text(matrix))
        with open(args.matrix, "w") as f:
            json.dump(matrix, f, indent=2)
        print(f"\nWrote security matrix -> {args.matrix}")
        return

    traces: list[RunTrace] = []
    for fw in frameworks:
        trace = run_one(fw, args.scenario)
        traces.append(trace)
        sec = [e for e in trace.events if e.kind == "alert"]
        print(f"[{fw}] {args.scenario}: {len(trace.tool_calls)} tool calls, "
              f"{len(sec)} security verdicts")
        for e in sec:
            print("   ", e.detail)

    if args.out and len(traces) == 1:
        with open(args.out, "w") as f:
            json.dump(traces[0].model_dump(mode="json"), f, indent=2, default=str)
        print(f"Wrote trace -> {args.out}")


if __name__ == "__main__":
    main()
