# Post 1 — LangGraph: the order lifecycle as an explicit state machine

**Pitch.** LangGraph makes the order lifecycle *structural*: every status is a node, every
transition an edge, and the refund path is unreachable until a human-approval node has run.

## Status: LIVE-wired
This lane runs against a real model today. `pip install langgraph`, load Qwen in LM Studio, then:
`CKA_PROVIDER=lmstudio python -m agents.run_scenario --framework langgraph --scenario security_all`.
It builds and invokes two real compiled `StateGraph`s (`agents/langgraph/graph.py`): the order
lifecycle (intake→kitchen→dispatch, conditional edges, model-driven dispatch node) and the
security decision graph (decide→guardrail→approval|act). `provider=mock` still runs the offline
deterministic path.

## Setup friction (fill in on live run)
- `pip install langgraph`; the decide nodes reach the model via the shared `ModelClient`
  (LM Studio/Ollama/vLLM). Swap to `ChatOpenAI(base_url=...)` if you want the LangChain surface.
- MCP client maturity: tools are attached via the shared scoped `ToolClient` inside each node.

## Code shape
- 8 roles → nodes in a `StateGraph`; conditional edges encode `received→confirmed→prepping→
  ready→picked_up`. See `agents/langgraph/adapter.py::build_graph`.
- The approval node gating the refund edge is why LangGraph contains ASI01/ASI02 *structurally*.

## Order lifecycle & exceptions
- `steady`, then `courier_no_show` / `stockout` / `rush`. Where do conditional edges make
  replanning clean? (Expect: strong — rollback points are explicit.)

## Security row (from the matrix)
- Expected: 5/5, all **framework**-defense. The refund edge sits behind approval; provenance
  and KB-consistency wired as guard nodes.

## Predict-then-verify
> Prediction: ______  ·  Reality: ______  ·  Gap insight: ______

## Verdict
Strengths: auditable graph, explicit rollback, structural guardrails.
Weaknesses: more upfront wiring; graph rigidity vs. free-form replanning.
Reach for it when: you want the lifecycle and its safety gates to be inspectable.
