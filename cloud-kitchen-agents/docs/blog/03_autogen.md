# Post 3 — AutoGen / AG2: group chat makes manipulation visible

**Pitch.** Modeling Dispatch/Kitchen/Inventory as a group chat gives you a transcript — and a
critic agent that reads it can veto a bad tool call before it fires. Great for social-engineering
attacks; blind to what it can't see in the conversation (external tool provenance).

## Setup friction (fill in on live run)
- Re-check AG2 vs. legacy AutoGen maintenance status first (EngDesign §14). `pip install ag2`.

## Code shape
- 8 roles → `ConversableAgent`s + a `Critic`; coordination is a `GroupChat`. See
  `agents/autogen/adapter.py::build_groupchat`.

## Security row (from the matrix)
- Expected: 5/5, but note the *defense* column. ASI01/ASI02/ASI06 contained at the **framework**
  layer (critic vetoes the refund / flags the poisoned KB claim in-transcript). ASI04 leans on
  the **rest_gate** — a transcript can't see that a third-party tool's data is unverified.
  That asymmetry is the post's key insight.

## Predict-then-verify
> Prediction: ______  ·  Reality: ______  ·  Gap insight: ______

## Verdict
Strengths: transcripts expose inter-agent deception; natural place for a reviewer.
Weaknesses: external-tool provenance invisible in chat; verbosity/latency.
Reach for it when: the threat model is social (agents manipulating agents).
