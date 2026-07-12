# Post 4 — Claude / OpenAI Agent SDK: lowest overhead, least free safety

**Pitch.** Closest to raw model + tool-calling. An explicit orchestrator hands off to sub-agents.
You pay almost no framework overhead — but you also get almost no safety scaffolding for free;
every guardrail is something you add as a handoff or a tool wrapper.

## Setup friction (fill in on live run)
- `pip install openai-agents` (or the Claude Agent SDK). Open-source models likely need a
  **LiteLLM shim** — this is the one adapter most likely to need a provider swap (EngDesign §12).
  Document that friction; it's blog-worthy on its own.

## Code shape
- Orchestrator `Agent` with sub-agents as handoffs. See `agents/agent_sdk/adapter.py::build_orchestrator`.

## Security row (from the matrix)
- Expected: 5/5, but the *defense* column shows the trade-off. ASI01/ASI02 contained via the
  explicit approval handoff (**framework**); ASI04 and ASI06 lean on the **rest_gate** because no
  provenance/KB-consistency wrapper is added by default. Lesson: low overhead ⇒ you must add the
  guardrails yourself; the infra gate is your safety net when you forget.

## Predict-then-verify
> Prediction: ______  ·  Reality: ______  ·  Gap insight: ______

## Verdict
Strengths: minimal overhead; closest to the model; easy to reason about cost.
Weaknesses: safety is DIY; open-source model wiring needs a shim.
Reach for it when: you want a thin, explicit loop and will own the guardrails.
