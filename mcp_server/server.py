"""A self-built MCP server exposing two doc tools over stdio (FastMCP).

Consumed by the Agents SDK via MCPServerStdio, which runs this file as a subprocess.
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

    Tries exact stem, then stem substring, then a content search that ranks docs by
    topic-word overlap so callers don't need exact filenames (e.g. "Runner" -> agents).

    Args:
        topic: A concept such as "Runner", "needs_approval", "tripwire", or "mcp".
    """
    topic_norm = topic.lower().strip().replace(" ", "_")
    docs = list(DOCS_DIR.glob("*.md"))

    for p in docs:
        if p.stem == topic_norm:
            return p.read_text(encoding="utf-8")
    for p in docs:
        if topic_norm in p.stem or p.stem in topic_norm:
            return p.read_text(encoding="utf-8")

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
    mcp.run()
