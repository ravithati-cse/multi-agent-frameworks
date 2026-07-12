#!/usr/bin/env python
"""
Seed the knowledge base from policy docs in knowledge_seed/.

Run: poetry run python mcp_servers/seed_kb.py
Re-run after editing any .md file to refresh the live KB.
"""
from __future__ import annotations

import sys
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

SEED_DIR = Path(__file__).parent / "knowledge_seed"
CHROMA_PATH = Path(__file__).parent / "chroma_db"
COLLECTION = "kitchen_kb"
CHUNK_SIZE = 400   # characters per chunk (simple fixed-size for v1)
CHUNK_OVERLAP = 80


def chunk(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c]


def seed() -> None:
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    ef = DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(COLLECTION, embedding_function=ef)

    # wipe existing so re-seeding is idempotent
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        print(f"Cleared {len(existing['ids'])} existing entries.")

    docs, ids, metas = [], [], []
    for md_file in sorted(SEED_DIR.glob("*.md")):
        text = md_file.read_text()
        for i, chunk_text in enumerate(chunk(text)):
            doc_id = f"{md_file.stem}__{i}"
            docs.append(chunk_text)
            ids.append(doc_id)
            metas.append({"source": md_file.name, "chunk": i})

    collection.add(documents=docs, ids=ids, metadatas=metas)
    print(f"Seeded {len(docs)} chunks from {len(list(SEED_DIR.glob('*.md')))} documents into '{COLLECTION}'.")


if __name__ == "__main__":
    seed()
