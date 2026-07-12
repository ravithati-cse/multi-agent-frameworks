# Post 2 — CrewAI: clean role delegation, weak mid-flight guardrails

**Pitch.** CrewAI expresses the kitchen as roles (Agents) and jobs (Tasks) delegated through a
Crew process — delightful for role clarity, but a task that *holds* a tool can use it with no
extra scope restriction, which is exactly where the security story gets interesting.

## Setup friction (fill in on live run)
- `pip install crewai`; wire the model via its LiteLLM-backed config to Ollama/vLLM.

## Code shape
- 8 roles → `Agent` + `Task`; lifecycle as a sequential/parallel `Crew`. See
  `agents/crewai/adapter.py::build_crew`.

## Order lifecycle & exceptions
- Test mid-prep change + stockout: expect the weakest fine-grained replanning of the five
  (EngDesign §5.1 flagged this — verify directly).

## Security row (from the matrix)
- **Expected: 4/5 — the documented FAIL is ASI02.** The over-granted refund tool has no
  framework-level scope restriction on the Task, so only the REST gate stands between the agent
  and a sub-threshold unauthorized refund — and the REST gate allows sub-threshold refunds.
  Root cause verbatim: "over-granted refund tool used with no framework scope restriction."

## Predict-then-verify
> Prediction: ______  ·  Reality: ______  ·  Gap insight: ______

## Verdict
Strengths: fastest to express role delegation; readable.
Weaknesses: tool-scope discipline is on you; mid-flight replanning is awkward.
Reach for it when: role structure matters more than fine-grained control-flow safety.
