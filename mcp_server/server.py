"""A self-built MCP server (the "build your own MCP server" requirement).

It exposes two tools over stdio using FastMCP from the official `mcp` package:

  - list_docs()        -> names of available docs
  - docs_lookup(topic) -> the contents of the matching doc

The Agents SDK consumes this server via MCPServerStdio, which launches this file
as a subprocess (`python -m mcp_server.server`) and talks to it over stdin/stdout.
Run it directly to smoke-test: `python -m mcp_server.server` (it will wait on stdio).
"""
from __future__ import annotations

import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DOCS_DIR = Path(__file__).resolve().parent / "docs"

mcp = FastMCP("docs-server")


@mcp.tool()
def list_docs() -> list[str]:
    """List the available documentation topics (file stems)."""
    return sorted(p.stem for p in DOCS_DIR.glob("*.md"))


@mcp.tool()
def docs_lookup(topic: str) -> str:
    """Return the contents of the doc most relevant to `topic`.

    Matching is layered so callers don't have to know exact filenames:
    exact stem, then stem substring, then a content search that ranks docs by how
    many of the topic's words appear in the doc body (so "Runner" finds agents.md).

    Args:
        topic: A concept such as "Runner", "needs_approval", "tripwire", or "mcp".
    """
    topic_norm = topic.lower().strip().replace(" ", "_")
    docs = list(DOCS_DIR.glob("*.md"))

    # 1) exact stem, then 2) stem substring.
    for p in docs:
        if p.stem == topic_norm:
            return p.read_text(encoding="utf-8")
    for p in docs:
        if topic_norm in p.stem or p.stem in topic_norm:
            return p.read_text(encoding="utf-8")

    # 3) content search: score each doc by topic-word overlap with its body.
    words = [w for w in re.findall(r"[a-z0-9_]+", topic.lower()) if len(w) > 2]
    best, best_score = None, 0
    for p in docs:
        body = p.read_text(encoding="utf-8").lower()
        score = sum(body.count(w) for w in words)
        if score > best_score:
            best, best_score = p, score
    if best is not None:
        return best.read_text(encoding="utf-8")

    available = ", ".join(sorted(p.stem for p in docs))
    return f"NO_DOC: no doc matched '{topic}'. Available: {available}"


if __name__ == "__main__":
    # FastMCP.run() defaults to the stdio transport, which is what MCPServerStdio expects.
    mcp.run()
