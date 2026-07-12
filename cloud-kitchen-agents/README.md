# AI-Native Cloud Kitchen Dispatch Simulator

A multi-framework, security-aware agentic AI benchmark built on one real-time domain.
Implements the full roadmap from `docs/PRD.md`, `docs/ENGINEERING_DESIGN.md`, and
`docs/USER_STORIES.md`:

- **Phase 0** — deterministic `asyncio` simulation engine (orders, kitchen, couriers,
  Matched/FIFO baselines, metrics).
- **Phase 0.5** — REST tool layer (FastAPI) with per-role scoped tokens, MCP server wrappers,
  and a directly-seeded RAG knowledge base.
- **Phases 1–3** — 8 agent roles defined once, wired into **5 framework adapters**
  (LangGraph, CrewAI, AutoGen/AG2, Claude/OpenAI Agent SDK, Strands).
- **Phase 4** — security red-team harness: 5 OWASP-ASI scenarios × 5 frameworks = 25-cell matrix.
- **Phases 5–7** — infra runbooks (Ollama, vLLM/AMD, Bedrock AgentCore) + blog series outlines.
- **Cross-cutting** — a real-time ops dashboard (order board, kitchen/courier gauges, dispatch
  comparison chart, security alert feed, framework indicator).

## Quickstart (offline, no GPU, no model)

```bash
pip install -r requirements.txt
python -m mcp_servers.seed_kb                       # seed the RAG knowledge base
pytest -q                                            # 14 tests: engine, auth, security matrix

# 1) Phase 0 engine (standalone, matches the original take-home rubric)
python -m engine --strategy fifo --duration 20 --rate 2 --json-out fifo.json

# 2) Run a framework through a scenario (default provider = mock, fully offline)
python -m agents.run_scenario --framework langgraph --scenario steady

# 3) Build the 5×5 security matrix across all frameworks
python -m agents.run_scenario --framework all --scenario asi01 --matrix matrix.json

# 4) Dashboard
uvicorn dashboard.backend.server:app --port 8080     # open http://localhost:8080/
```

## Going live (real models)

The system ships with `provider="mock"` so it runs and the security matrix is reproducible with
zero GPU. Everything is env-driven (`agents/common/model_config.py`) — no code edit needed.

### LM Studio (Qwen loaded locally)

```bash
# 1. In LM Studio: load your Qwen model and start the local server (Developer tab).
# 2. Confirm the endpoint + model id and that the model drives a decision:
CKA_PROVIDER=lmstudio python -m scripts.check_model
#    (base_url defaults to http://localhost:1234/v1; the model id is auto-detected)

# 3. Run any framework against the live model:
CKA_PROVIDER=lmstudio python -m agents.run_scenario --framework langgraph --scenario steady

# 4. Rebuild the security matrix with the real model deciding:
CKA_PROVIDER=lmstudio python -m agents.run_scenario --framework all --scenario asi01 --matrix matrix.json
```

Env knobs (all optional): `CKA_BASE_URL` (default `http://localhost:1234/v1`), `CKA_MODEL`
(auto-detected from `/v1/models` if unset), `CKA_MODEL_FAST` / `CKA_MODEL_SMART` (per-tier
override), `CKA_TEMPERATURE`.

**What changes when a real model is plugged in.** The agents' decisions now come from the model
via a JSON-action protocol (works even when the server lacks native tool-calling). In the
security scenarios this adds a new outcome to each cell's `defense`: **`model`** = the model's
own resistance contained the attack. So a well-aligned Qwen may contain ASI01/02/04/06 by
itself; if it complies, the framework guardrail + REST scope gate are the next lines of defense.
This is the predict-then-verify moment — write down what you expect Qwen to do, then run it.

**LangGraph runs fully live.** The LangGraph lane is wired to build and invoke real compiled
`StateGraph`s (`agents/langgraph/graph.py`) — the order lifecycle (intake→kitchen→dispatch with
conditional edges and a model-driven dispatch node) and a security decision graph
(decide→guardrail→approval|act, where the refund edge sits behind an approval node). Install it
and run against Qwen:

```bash
pip install langgraph
CKA_PROVIDER=lmstudio python -m agents.run_scenario --framework langgraph --scenario security_all
```

With a resistant model the attacks are contained at the model layer (`defense=model`); with a
compliant one they fall to LangGraph's own guardrail nodes (`defense=framework`). The other four
lanes still run via the shared path; port them to live one at a time the same way.

Other providers use the same pattern: `CKA_PROVIDER=ollama` (see `infra/ollama/`), `vllm`
(see `infra/vllm_amd/`), or `anthropic`. Each of the 5 adapters also has a live-construction
function (`build_graph` / `build_crew` / `build_groupchat` / `build_orchestrator` /
`build_agent`) that builds the real framework objects — the code to run to learn each framework
hands-on. Install only the lane you're running (see `requirements.txt`).

## How the comparison stays fair

Everything except orchestration is shared by construction:
- `contracts/` — one set of pydantic schemas (Order, Event, Metrics, AgentRoleSpec, RunTrace).
- `agents/common/roles.py` — the 8 role specs (prompt + tools + scoped token + model) defined once.
- `mcp_servers/registry.py` + `agents/common/tool_client.py` — one tool-call path for all 5
  frameworks; no per-framework tool bindings.
- `scenarios/library.py` — identical scripted scenarios for every framework.
- `security/eval_harness.py` — inspects only the shared `RunTrace`, so zero framework-specific
  eval code.

Only the per-framework `run_scenario` orchestration and guardrail **posture** differ — which is
exactly what the benchmark measures.

## Security model (two lines of defense)

1. **Framework-independent infra gate** (`services/app.py` + `services/auth.py`): scoped bearer
   tokens (403 on out-of-scope calls) and a refund-approval gate (428 without prior approval).
2. **Framework-level guardrails** (each adapter's `posture` + `agents/common/guardrails.py`):
   approval routing, provenance checks, KB-consistency checks, objective guardrails.

The 25-cell matrix records, per cell, PASS/FAIL **and** the `defense` that contained it
(`framework` = robust / `rest_gate` = fragile / `none` = failed). See `docs/blog/06_synthesis.md`.

> Reproducible offline result: LangGraph/AutoGen/AgentSDK/Strands = 5/5; **CrewAI = 4/5**
> (fails ASI02 — an over-granted refund tool with no framework-level scope restriction).

## Repo layout

```
engine/        Phase 0 deterministic sim (asyncio), CLI: python -m engine
contracts/     shared pydantic schemas (single source of truth)
services/      FastAPI REST tool layer + scoped-token auth
mcp_servers/   MCP tool registry + FastMCP servers, rogue server (ASI04), KB seed + vector store
agents/
  common/      role specs, model client (mock/ollama/vllm/anthropic), tool client, guardrails, attacks
  langgraph/ crewai/ autogen/ agent_sdk/ strands/   the 5 adapters
  run_scenario.py   scenario runner CLI (--framework, --scenario, --matrix)
scenarios/     load profiles, operational exceptions (Epic C), ASI security scenarios (Epic E)
security/      EvalHarness + 5×5 matrix builder
dashboard/     FastAPI WebSocket backend + single-file React frontend
infra/         ollama/ vllm_amd/ bedrock_agentcore/  (Phases 5–6 runbooks)
docs/          PRD, ENGINEERING_DESIGN, USER_STORIES, blog/ (Epic G outlines)
tests/         engine, services/auth, security matrix
```

## Note on build mode

`docs/PRD.md` §1a describes a hands-on "Ravi writes the orchestration logic" working mode. This
build was explicitly requested as a full generation (all 5 adapters authored) — flagged here per
that section. To reclaim the learning path, treat each adapter's live-construction function as a
reference and re-derive it yourself against a running model, using the predict-then-verify boxes
in `docs/blog/*`.
