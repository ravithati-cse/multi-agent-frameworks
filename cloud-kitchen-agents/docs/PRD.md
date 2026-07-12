# PRD: AI-Native Cloud Kitchen Dispatch Simulator
**A multi-framework, security-aware agentic AI benchmark**

| | |
|---|---|
| Owner | Ravi |
| Status | Draft v1 |
| Last updated | June 19, 2026 |
| Related docs | `USER_STORIES.md`, `ENGINEERING_DESIGN.md` |

---

## 1. Background

This project originates from a real take-home engineering challenge (real-time courier
dispatch simulation: orders arrive at 2/sec, each has a `prepTime`, couriers arrive
uniformly 3-15s after dispatch, two strategies — **Matched** and **FIFO** — must be
implemented and benchmarked on food-wait and courier-wait time).

That challenge is, by design, deterministic application code — there's no ambiguity for
an LLM to resolve. The opportunity is to use it as the **ground-truth simulation engine**
for a much bigger goal: building the same full cloud-kitchen operation (orders → kitchen →
delivery → payments → customer support) as an **agentic system**, implemented five times
across five different agent frameworks, and then deliberately attacked to see how each
framework's primitives hold up against the new OWASP Top 10 for Agentic Applications
(2025/2026) risk taxonomy.

The end products are: (1) a working multi-agent simulator, (2) a framework comparison
matrix grounded in one real system instead of toy demos, (3) a security comparison
grounded in the same system, and (4) a blog series documenting all of it for personal
learning, team education, and the author's professional network.

## 1a. Working Mode (this governs everything below)

The primary deliverable of this project is **Ravi's own hands-on framework fluency** —
not 5 working implementations someone else generated. Every phase should be structured so
the act of building teaches the framework, not just the finished code. This applies in
Claude Cowork and any other session, regardless of how far in the future:

- **Boilerplate vs. core logic split.** Claude scaffolds the parts that aren't where the
  learning is — engine code, REST/MCP plumbing, shared contracts, repo setup. The actual
  orchestration logic per framework (LangGraph nodes/edges, CrewAI task delegation,
  AutoGen conversation design, Strands tool loop, Agent SDK handoffs) is written by Ravi.
  Claude reviews and explains; Claude does not author the orchestration logic itself.
- **Predict-then-verify.** Before running a scenario against a new framework, Ravi writes
  down what he expects it to do. Then it runs. The gap between prediction and reality is
  where the real per-framework insight usually is — Claude should prompt for the
  prediction rather than skipping straight to the run.
- **Deliberate debugging.** Periodically, Claude introduces a small misconfiguration
  (wrong tool scope, missing approval gate, bad event ordering) instead of pointing it
  out. Ravi diagnoses it using that framework's own tracing/observability tools. Claude
  should not pre-empt this by explaining the bug when it sets one up.
- **Build-journal entries.** A short "what surprised me" note after each phase, written
  by Ravi while it's fresh. This becomes blog draft material directly, instead of a
  separate writing task bolted on at the end — Claude can prompt for this at phase
  boundaries but should not write it.

If a future session (including this one resumed later) defaults to "Claude generates the
implementation, Ravi reviews it," that's a deviation from this PRD and should be flagged
and corrected, not treated as a reasonable shortcut.

## 2. Problem Statement

Most public framework comparisons (LangGraph vs. CrewAI vs. AutoGen vs. ...) are shallow —
single-tool demos that don't expose real differences in planning, concurrency, state
management, or security posture. There is no widely available, reproducible reference
implementation that:

- Uses **one non-trivial, concurrent, real-time domain** across multiple frameworks
- Separates deterministic "engine" code from genuinely agentic "reasoning" code, so the
  comparison measures framework strengths, not business logic
- Includes a **security red-team dimension** mapped to a recognized taxonomy (OWASP ASI),
  rather than only developer-experience opinions
- Is portable from local/open-source inference (Ollama, vLLM on AMD GPUs) to a managed
  cloud platform (Bedrock AgentCore), which is the actual production path most teams face

## 3. Goals

1. Build a deterministic, real-time **simulation engine** (orders, kitchen prep, courier
   dispatch) satisfying the original challenge's functional requirements and rubric.
2. Build an **agentic decision layer** of 8 agent roles on top of the engine, implemented
   identically across **5 frameworks**: LangGraph, CrewAI, AutoGen/AG2, Claude/OpenAI
   Agent SDK, and Strands Agents.
3. Implement and compare **3 dispatch strategies**: Matched (baseline), FIFO (baseline),
   and Agentic (LLM-driven, load-aware).
4. Inject realistic **operational exceptions** ("messiness") not present in the original
   spec: courier no-shows, mid-prep order changes, stockouts, rush-hour contention.
5. Build a production-style **tool layer**: every mocked service (menu, inventory,
   kitchen, courier pool, payment, ticketing) exposed as a **REST API**, wrapped by an
   **MCP server**, so all 5 frameworks call tools through one shared protocol instead of
   bespoke per-framework bindings. The RAG knowledge base is seeded directly from a small
   policy doc set for v1 — a full ETL ingestion pipeline is deferred (see Section 10).
6. Implement a **security red-team harness** covering 5 OWASP ASI categories (Goal
   Hijack, Tool Misuse, Memory/Data Poisoning, Rogue Agent drift, and **MCP Supply Chain
   compromise**) and measure each framework's containment behavior.
7. Run the full stack on **open-source models via Ollama (dev) and vLLM on AMD GPU cloud
   (production-style serving)**, then migrate the Strands implementation to **Bedrock
   AgentCore** as a later phase.
8. Build a real-time **operations dashboard** as the primary observability surface —
   live order/kitchen/courier state, dispatch-strategy comparison, and a security-alert
   feed — replacing console output as the default way the system is observed.
9. Produce a public **blog series** documenting build experience, the comparison matrix,
   and the security findings.

## 4. Non-Goals

- Not building a real production food-delivery platform (no real payments, couriers,
  restaurants, or customers — everything is simulated).
- Not a rigorous academic security audit — this is an educational red-team exercise, not
  a certification.
- Not optimizing for lowest cost/latency in v1 — optimizing for clarity of comparison.
- Not covering all 10 OWASP ASI categories in v1 (4 selected; rest noted as future work).
- Not building a customer-facing production UI or a marketing site — the dashboard is an
  **internal ops view** (you, your team, blog readers watching a recording), not a
  polished consumer product.

## 5. Target Users / Audience

- **Primary:** Ravi — hands-on framework literacy, portfolio piece, conference/blog content.
- **Secondary:** Ravi's engineering team — onboarding material for evaluating agent
  frameworks for internal use.
- **Tertiary:** Public/professional network via blog — practitioners evaluating the same
  framework decisions.

## 6. Success Metrics

- Engine: meets 100% of the original challenge's functional + rubric requirements
  (runnable, documented, tested, real-time console output, correct avg wait-time stats).
- Agent layer: all 8 roles implemented and functionally equivalent across all 5 frameworks
  (same scenario inputs → comparable outcomes).
- Dispatch comparison: quantified delta between Matched, FIFO, and Agentic strategies
  under at least 3 load conditions (steady, rush, degraded/exception).
- Security: pass/fail result captured per framework × per ASI scenario (25 data points:
  5 frameworks × 5 scenarios), with root-cause notes for each failure.
- Dashboard: live view of order lifecycle, kitchen/courier state, dispatch-strategy
  comparison, and the security-alert feed, all updating in real time during a run.
- Output: 1 design doc set (this one), ≥1 published blog post per framework, 1 final
  synthesis post with the comparison matrix and security findings.

## 7. Scope & Phases

| Phase | Description |
|---|---|
| 0 | Deterministic simulation engine (orders, kitchen, couriers, Matched/FIFO baselines, metrics) |
| 0.5 | Tool & data layer: REST services for Menu/Inventory/Kitchen/Courier/Payment/Ticketing, each wrapped by an MCP server; RAG knowledge base seeded directly from a small policy doc set; dashboard skeleton wired to the EventBus |
| 1 | Agent layer v1 on **one** framework (LangGraph), single kitchen, full order lifecycle, calling tools via MCP |
| 2 | Add concurrency (multi-order, multi-kitchen) + operational exception scenarios |
| 3 | Port identical agent layer to the remaining 4 frameworks (CrewAI, AutoGen/AG2, Claude/OpenAI Agent SDK, Strands) |
| 4 | Security red-team harness: 5 ASI scenarios (including MCP supply-chain compromise) run against all 5 frameworks |
| 5 | Run full stack on AMD GPU cloud via vLLM (open-source models), replacing local Ollama dev loop |
| 6 | Migrate Strands implementation to Bedrock AgentCore; document migration delta |
| 7 | Blog series: per-framework build notes, comparison matrix, security findings, final synthesis |

## 8. Constraints & Assumptions

- Dev environment: **Claude Cowork**, used as the primary build/agent-orchestration
  assistant across phases.
- Inference: **open-source models** via **Ollama** (local dev) and **vLLM** (AMD developer
  GPU cloud, ROCm backend) for phases 0-5; **Bedrock/AgentCore** is a later, separate
  phase and may reintroduce managed-model dependencies (Strands defaults to Bedrock).
- Assumes Python as the primary implementation language for the engine and all 5 agent
  adapters, for consistency and to maximize framework SDK compatibility.
- No production technologies per the original challenge's constraints for the **engine
  layer** specifically (no DBs, Kafka, microservices, REST) — the agent layer may relax
  this where a framework requires it (e.g., a local message bus), documented per framework.
- This constraint applies **only** to the Phase 0 engine (kept as a standalone,
  independently submittable artifact matching the original challenge exactly). The
  broader agentic system (Phase 0.5+) deliberately uses REST APIs and MCP servers — this
  is an intentional split, not a contradiction: it mirrors real production agent
  architecture and creates realistic attack surfaces (API/tool boundaries, MCP supply
  chain) that an in-process mock can't. A full ETL ingestion pipeline for the knowledge
  base is deferred (v1 uses a direct seed script); revisit once multiple ingestion
  sources are actually needed.
- Assumes single-machine execution is sufficient for all 5 framework comparisons (no
  distributed deployment required for v1) — REST/MCP services run as local processes,
  not a distributed cluster.

## 9. Risks

- **Scope creep**: 5 frameworks × 8 agents × exceptions × security scenarios is a lot of
  surface area. Mitigation: strict phase gating (Section 7); Phase 1 must be fully done
  on one framework before any porting begins.
- **Unfair comparison**: if business logic drifts between framework implementations, the
  comparison becomes meaningless. Mitigation: shared engine + shared tool contracts
  (see Engineering Design Doc §5) are the single source of truth; only orchestration code
  differs.
- **Model variability**: open-source model choice/quality may dominate results more than
  framework choice. Mitigation: pin model + temperature per agent role across all 5
  framework runs; document model config explicitly in each blog post.
- **Security harness false confidence**: a contained attack in simulation doesn't prove
  production safety. Mitigation: explicitly scope the blog's security claims as
  educational/illustrative, not a certification.

## 10. Open Questions

- Which open-source model(s) will be used per agent role (uniform vs. heterogeneous —
  e.g., lightweight model for Inventory/Order Intake, stronger reasoning model for
  Dispatch/Support/Ops Supervisor)?
- Does the Agentic dispatch strategy need to be evaluated only on the original two
  metrics (food wait, courier wait), or also on a cost/efficiency metric?
- What auth/identity model do the REST/MCP services use for per-agent scoped credentials
  (simple API keys per role vs. something closer to OAuth scopes)? This also affects the
  Phase 6 AgentCore migration, which has its own identity model.
- Vector store choice for the RAG knowledge base (Chroma vs. FAISS vs. something else) —
  driven mainly by what runs cleanly on the AMD GPU box alongside vLLM.
- When (if ever) does the static KB seed need to become a real ETL pipeline — e.g., once
  there are multiple genuinely separate ingestion sources, or once ingestion-time
  poisoning (vs. seed-edit poisoning) becomes important enough to justify the build cost?

## 11. Future Experiments (explicitly out of scope for v1)

- **Temporal as a durability substrate** — re-run the exception (Epic C) and security
  (Epic E) scenarios with one framework (likely LangGraph) wrapped in Temporal's durable
  Workflow/Activity model, to measure whether crash-recovery and native retry/signal
  semantics change outcomes versus the framework's own state handling. Candidate Phase 6.5.
- **Hermes Agent (Nous Research) as an MCP component** — not a 6th framework lane; use it
  either as a delegated subagent reachable via MCP, or as the rogue/third-party MCP server
  stand-in for the ASI04 supply-chain scenario, since it can genuinely expose itself as an
  MCP endpoint.
