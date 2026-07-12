# Post 5 — Strands: model-driven loop, and the bridge to managed

**Pitch.** The LLM plans its own steps; tools are `@tool`-decorated functions. Native Ollama /
LiteLLM support makes it the easiest to point at the AMD vLLM stack, and it's the direct path to
Bedrock AgentCore (Phase 6).

## Setup friction (fill in on live run)
- `pip install strands-agents`; `OllamaModel(host=..., model_id=...)`. Expect the smoothest
  open-source wiring of the five.

## Code shape
- One model-driven `Agent` with registered tools + guardrail hooks. See
  `agents/strands/adapter.py::build_agent`.

## Security row (from the matrix)
- Expected: 5/5. Approval + provenance + objective hooks give **framework** defense on
  ASI01/02/04/10; ASI06 leans on the **rest_gate** because a model-driven loop tends to trust
  retrieved KB text — worth stress-testing with a real model.

## Migration angle (Phase 6)
- This is the only adapter that ports to Bedrock AgentCore with minimal change. The
  "self-hosted vs. managed" delta post (Epic G) comes from diffing this adapter's AMD/vLLM
  matrix against its AgentCore matrix. See `infra/bedrock_agentcore/MIGRATION.md`.

## Predict-then-verify
> Prediction: ______  ·  Reality: ______  ·  Gap insight: ______

## Verdict
Strengths: least-friction open-source serving; autonomy; clean migration path.
Weaknesses: model-driven autonomy makes guardrail hooks essential; trusts retrieved text.
Reach for it when: you want autonomy now and a managed runtime later.
