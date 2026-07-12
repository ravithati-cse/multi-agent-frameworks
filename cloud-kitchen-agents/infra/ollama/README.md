# Local dev inference — Ollama (Phase 0–4)

Dev loop uses Ollama's OpenAI-compatible endpoint so framework adapters only change a
`base_url` + `provider` in `ModelConfig` (no code change, EngDesign §12).

## Setup

```bash
# install ollama (macOS/Linux): https://ollama.com/download
ollama serve                      # starts the API on :11434
ollama pull llama3.1:8b
ollama pull qwen2.5:14b
```

## Point the agents at Ollama

Edit `agents/common/roles.py` (or override via env in your run script):

```python
_FAST  = ModelConfig(provider="ollama", model="llama3.1:8b",
                     base_url="http://localhost:11434/v1", temperature=0.0)
_SMART = ModelConfig(provider="ollama", model="qwen2.5:14b",
                     base_url="http://localhost:11434/v1", temperature=0.1)
```

Then run any framework against a live model:

```bash
python -m agents.run_scenario --framework strands --scenario security_all
```

`models.yaml` in this folder is the pinned per-role assignment — keep it identical across
all 5 framework runs so the comparison isolates framework effects from model effects.

## Note on `provider: mock`

The repo ships with `provider="mock"` so the whole system runs offline and the security
matrix is reproducible with zero GPU. The mock is deliberately naive about injected
instructions, so containment depends on framework guardrails + the REST/MCP scope gate —
which is the axis the comparison measures. Switch to `ollama` to test the model's *own*
resistance (predict-then-verify: write down what you expect each model to do first).
