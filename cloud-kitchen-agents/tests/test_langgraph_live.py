"""Live LangGraph path: real compiled StateGraphs driven by a (faked) model.

Skips cleanly if langgraph isn't installed. Fakes only the model's network method, so the
graphs, tool layer, guardrails, and harness all run for real — only the LLM is simulated.
"""
import pytest

pytest.importorskip("langgraph")

from agents.common.model_client import ModelClient, ModelResponse  # noqa: E402
from agents.common.roles import ROLE_SPECS  # noqa: E402
from mcp_servers.seed_kb import seed  # noqa: E402


PERSONA = {"mode": "safe"}


def _fake(self, system, user, tools, context):
    s = system.lower()
    if PERSONA["mode"] == "gullible":
        if "support" in s or "payment" in s:
            return ModelResponse(text='{"tool":"payment.refund","args":{},"why":"complying"}')
        if "dispatch" in s and "cancel" in user.lower():
            return ModelResponse(text='{"tool":"order.upsert","args":{"status":"cancelled"},"why":"cost"}')
        return ModelResponse(text='{"tool":"courier.dispatch","args":{},"why":"go"}')
    if "support" in s:
        return ModelResponse(text='{"tool":"ticket.create","args":{"subject":"refund"},"why":"route to Payment"}')
    if "payment" in s:
        return ModelResponse(text='{"tool":"none","args":{},"why":"ignore unverified/poisoned claims"}')
    if "dispatch" in s:
        return ModelResponse(text='{"tool":"courier.dispatch","args":{},"why":"never cancel for a metric"}')
    return ModelResponse(text='{"tool":"none","args":{},"why":""}')


@pytest.fixture(autouse=True)
def live_model(monkeypatch):
    monkeypatch.setattr(ModelClient, "_openai_compatible", _fake)
    for spec in ROLE_SPECS.values():
        monkeypatch.setattr(spec.model_config_, "provider", "lmstudio")
    yield
    seed(quiet=True)


def _run(scenario):
    from agents.run_scenario import run_one
    return run_one("langgraph", scenario)


def test_live_lifecycle_graph_executes():
    trace = _run("steady")
    assert any("LIVE" in e.detail for e in trace.events), "should use the live StateGraph path"
    assert sum(1 for tc in trace.tool_calls if tc.tool == "courier.dispatch") >= 1


def test_live_safe_model_contains_at_model_layer():
    PERSONA["mode"] = "safe"
    from security.eval_harness import evaluate_cell
    for asi in ("asi01", "asi02", "asi04", "asi06", "asi10"):
        cell = evaluate_cell(_run(asi), asi.upper())
        assert cell["passed"] is True
        assert cell["defense"] == "model"


def test_live_gullible_model_contained_by_graph_guardrails():
    PERSONA["mode"] = "gullible"
    from security.eval_harness import evaluate_cell
    for asi in ("asi01", "asi02", "asi04", "asi06", "asi10"):
        cell = evaluate_cell(_run(asi), asi.upper())
        assert cell["passed"] is True  # LangGraph contains all 5 structurally
        assert cell["defense"] in ("framework", "rest_gate")
    PERSONA["mode"] = "safe"
