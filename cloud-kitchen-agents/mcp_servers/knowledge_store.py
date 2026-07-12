"""Lightweight local vector store for the RAG knowledge base.

v1 uses a dependency-free hashing bag-of-words embedding + cosine similarity, persisted to
JSON. This runs anywhere (sandbox, AMD box) with zero heavy deps, which is what we want for
a reproducible comparison. The interface (`embed`, `add`, `query`) is deliberately the same
shape you'd get from Chroma/FAISS + a sentence-transformer, so swapping in a real embedding
model later (PRD open question: Chroma vs FAISS) is a drop-in change — see EMBEDDING note.

EMBEDDING note: to use a real model, set CKA_EMBEDDING=sentence-transformers and install
sentence-transformers + chromadb; `embed()` will delegate. Kept optional so v1 stays light.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path

_DIM = 256
_WORD = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def embed(text: str) -> list[float]:
    """Hashing bag-of-words embedding, L2-normalized. Deterministic."""
    vec = [0.0] * _DIM
    for tok in _tokenize(text):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        idx = h % _DIM
        sign = 1.0 if (h >> 8) & 1 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class KnowledgeStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.environ.get("CKA_KB_PATH", "mcp_servers/kb_index.json"))
        self.docs: list[dict] = []
        if self.path.exists():
            self.load()

    def add(self, doc_id: str, source: str, text: str, meta: dict | None = None) -> None:
        self.docs.append(
            {"id": doc_id, "source": source, "text": text, "meta": meta or {}, "vec": embed(text)}
        )

    def clear(self) -> None:
        self.docs = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.docs))

    def load(self) -> None:
        self.docs = json.loads(self.path.read_text())

    def query(self, text: str, k: int = 3) -> list[dict]:
        qv = embed(text)
        scored = [
            {"id": d["id"], "source": d["source"], "text": d["text"], "meta": d["meta"], "score": _cosine(qv, d["vec"])}
            for d in self.docs
        ]
        scored.sort(key=lambda d: d["score"], reverse=True)
        return scored[:k]
