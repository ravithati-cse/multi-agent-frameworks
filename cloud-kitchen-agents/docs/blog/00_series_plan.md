# Blog series plan (Epic G)

Seven posts. Posts 1–5 share one structure (below) so they're directly comparable. Post 6 is
the synthesis. Post 0 (optional intro) frames the project.

## Shared per-framework structure (posts 1–5)

1. **The one-paragraph pitch** — what this framework is best at, in one sentence.
2. **Setup friction** — install, model wiring (Ollama/vLLM base_url or LiteLLM shim), MCP client
   maturity. Concrete: what broke, what the error was, how long to first green run.
3. **Code shape** — how the 8 shared `AgentRoleSpec`s map to this framework's primitives
   (nodes/edges, agents/tasks, conversable agents, handoffs, model-driven loop). Show the
   adapter's `run_scenario` and the live-construction function side by side.
4. **The order lifecycle** — screenshots/trace of a `steady` run on the dashboard.
5. **Exceptions** — how it handled `courier_no_show`, `stockout`, `rush` (Epic C). Where
   mid-flight replanning was easy vs. awkward.
6. **Security** — this framework's row of the ASI matrix, with the root-cause for each cell.
   Was containment *structural* (framework guardrail) or *incidental* (only the REST gate)?
7. **Predict-then-verify box** — what I expected before running vs. what actually happened.
8. **Verdict** — 3 bullet strengths, 3 weaknesses, "reach for it when…".

## Data sources for every post

- `python -m agents.run_scenario --framework <fw> --scenario security_all --out trace.json`
- `python -m agents.run_scenario --framework all --scenario asi01 --matrix matrix.json`
- Dashboard recording (`uvicorn dashboard.backend.server:app --port 8080`)
- Engine baseline: `python -m engine --strategy fifo --json-out fifo.json`
