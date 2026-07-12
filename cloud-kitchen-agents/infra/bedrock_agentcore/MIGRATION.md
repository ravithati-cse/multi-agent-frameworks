# Migration to Bedrock AgentCore — Phase 6 (Strands only)

Strands is the deliberate bridge (EngDesign §13): AWS Bedrock AgentCore is designed to
assemble Strands agents from declarative configuration, so the Strands adapter is the one
that ports with minimal change. The other 4 frameworks stay on the self-hosted AMD/vLLM stack
as the comparison baseline — porting them is explicitly out of scope for v1.

## Plan

1. Freeze the Strands implementation (Phase 3) and its security results (Phase 4).
2. Port its `AgentRoleSpec` set to AgentCore's declarative agent config.
3. Document the delta — what changes vs. what stays identical.
4. Re-run the same `ScenarioScript` set (exceptions + security) on AgentCore and diff results
   against the AMD/vLLM Strands run.

## What changes vs. stays identical

| Concern | Self-hosted Strands (Phase 3–5) | Bedrock AgentCore (Phase 6) |
|---|---|---|
| Role specs (`AgentRoleSpec`) | shared module | **identical** (declarative import) |
| Tool contracts (MCP registry) | local MCP servers over REST | AgentCore Gateway targets / MCP; same tool names |
| Model provider | vLLM/Ollama via `base_url` | Bedrock-hosted model (provider swap in `ModelConfig`) |
| Identity / scoped creds | static per-role bearer tokens (services/auth.py) | AgentCore Identity + IAM-scoped access |
| Guardrails | framework hooks + REST approval gate | Bedrock Guardrails config + same REST gate |
| Observability | RunTrace + dashboard | AgentCore traces exported into the same RunTrace schema |
| Scenario scripts | `scenarios/library.py` | **identical** |

## Identity note (EngDesign §14 open question)

v1 uses static per-role bearer tokens. AgentCore has its own identity model (AgentCore Identity
+ IAM). The scoped-token boundary in `services/auth.py` maps conceptually to per-agent IAM
scopes; document the exact mapping here once the AgentCore workspace is provisioned.

## Deliverable

The "what do you gain/lose moving to managed" blog post (Epic G) = the diff between the
AMD/vLLM Strands result matrix and the AgentCore result matrix, plus the migration-effort notes
captured above.

> Status: notes/runbook only. Requires an AWS account with Bedrock AgentCore access to execute;
> not runnable from the local dev loop.
