"""Central model-config resolver — one place to point the whole system at a provider.

Everything is env-driven so no code edit is needed to switch models:

    CKA_PROVIDER     mock | lmstudio | ollama | vllm | openai | anthropic   (default: mock)
    CKA_BASE_URL     OpenAI-compatible endpoint (auto-defaults per provider)
    CKA_MODEL        model id used for BOTH tiers unless the two below are set
    CKA_MODEL_FAST   model id for narrow lookup roles (order intake, kitchen, inventory)
    CKA_MODEL_SMART  model id for reasoning roles (dispatch, payment, support, ops)
    CKA_TEMPERATURE  default temperature (default: 0.1)

LM Studio quickstart (Qwen loaded, server started on the default port):

    export CKA_PROVIDER=lmstudio          # base_url defaults to http://localhost:1234/v1
    python -m agents.run_scenario --framework langgraph --scenario steady

If CKA_MODEL* are unset for a local provider, the resolver auto-detects the first model the
server reports at GET /v1/models, so you usually don't need to type the exact id.
"""
from __future__ import annotations

import os
from functools import lru_cache

from contracts import ModelConfig

_DEFAULT_BASE = {
    "lmstudio": "http://localhost:1234/v1",
    "ollama": "http://localhost:11434/v1",
    "vllm": "http://localhost:8000/v1",
    "openai": "https://api.openai.com/v1",
}


@lru_cache(maxsize=1)
def _detect_model(base_url: str) -> str | None:
    """Return the first model id the OpenAI-compatible server advertises, or None."""
    try:
        import httpx

        with httpx.Client(timeout=4) as c:
            r = c.get(f"{base_url.rstrip('/')}/models")
            r.raise_for_status()
            data = r.json().get("data", [])
            if data:
                return data[0]["id"]
    except Exception:
        return None
    return None


def resolve_configs() -> tuple[ModelConfig, ModelConfig]:
    """Return (fast_config, smart_config) for the current environment."""
    provider = os.environ.get("CKA_PROVIDER", "mock").lower()
    temp = float(os.environ.get("CKA_TEMPERATURE", "0.1"))

    if provider == "mock":
        return (
            ModelConfig(provider="mock", model="llama3.1:8b", temperature=0.0),
            ModelConfig(provider="mock", model="qwen2.5:14b", temperature=0.1),
        )

    base = os.environ.get("CKA_BASE_URL") or _DEFAULT_BASE.get(provider)
    detected = None
    if provider in ("lmstudio", "ollama", "vllm") and not os.environ.get("CKA_MODEL"):
        detected = _detect_model(base) if base else None

    default_model = os.environ.get("CKA_MODEL") or detected or "local-model"
    fast_model = os.environ.get("CKA_MODEL_FAST", default_model)
    smart_model = os.environ.get("CKA_MODEL_SMART", default_model)

    # LM Studio / Ollama / vLLM all speak the OpenAI-compatible surface.
    return (
        ModelConfig(provider=provider, model=fast_model, base_url=base, temperature=temp),
        ModelConfig(provider=provider, model=smart_model, base_url=base, temperature=temp),
    )
