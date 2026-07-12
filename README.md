# multi-agent-frameworks

A multi-framework, security-aware agentic AI benchmark. A cloud-kitchen order dispatch
simulation (orders → kitchen → courier → pickup) is implemented once as a deterministic engine
and shared tool layer, then orchestrated by five different agent frameworks so their behavior —
and their resistance to prompt-injection-style attacks — can be compared directly.

## Where the code lives

**[`cloud-kitchen-agents/`](cloud-kitchen-agents/)** — the actual implementation. Start there;
it has its own [README](cloud-kitchen-agents/README.md) with quickstart, live-model setup, and
repo layout.

- **Engine** — `asyncio` dispatch simulation (Matched/FIFO baselines, metrics).
- **Tool layer** — FastAPI REST + MCP servers with scoped per-role tokens and a RAG knowledge base.
- **Agents** — one set of role specs wired into 5 framework adapters: **LangGraph**, **CrewAI**,
  **AutoGen/AG2**, **Claude/OpenAI Agent SDK**, **Strands**.
- **Security** — a 5×5 OWASP-ASI attack scenario × framework matrix, scored by a shared eval
  harness.
- **Dashboard** — real-time ops view (order board, dispatch comparison, security alert feed).

## Docs

`PRD.md`, `ENGINEERING_DESIGN.md`, and `USER_STORIES.md` at the repo root are the canonical
planning docs (mirrored under `cloud-kitchen-agents/docs/` for in-project reference). A blog
series walking through each framework lives in `cloud-kitchen-agents/docs/blog/`.

## History

An earlier take on this domain, `cloud-kitchens/` (Postgres/SQLAlchemy REST API, Docker,
Alembic migrations), was superseded by the from-scratch rewrite in `cloud-kitchen-agents/` and
removed from version control.
