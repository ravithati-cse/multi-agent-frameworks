#!/usr/bin/env python
"""
MCP server — Knowledge Base (RAG over policy docs).

Agents query this to look up refund rules, SLAs, substitution policies, etc.
Seed the KB first: poetry run python mcp_servers/seed_kb.py
"""
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from mcp.server.fastmcp import FastMCP

from mcp_servers.config import CHROMA_PATH, KB_COLLECTION

mcp = FastMCP("knowledge-service")

_client = chromadb.PersistentClient(path=CHROMA_PATH)
_ef = DefaultEmbeddingFunction()
_collection = _client.get_or_create_collection(KB_COLLECTION, embedding_function=_ef)


@mcp.tool()
async def query_knowledge_base(query: str, n_results: int = 3) -> list[dict]:
    """
    Search the policy knowledge base with a natural-language query.
    Returns the top n_results relevant policy excerpts with their source document.
    """
    results = _collection.query(query_texts=[query], n_results=n_results)
    output = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "text": doc,
            "source": meta["source"],
            "relevance_score": round(1 - distance, 3),
        })
    return output


if __name__ == "__main__":
    mcp.run()
