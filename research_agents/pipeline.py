"""Pipeline assembly + a shared MCP server factory.

`make_mcp_server()` returns an (unconnected) MCPServerStdio that launches our own
`mcp_server/server.py` as a subprocess. Callers use it as an async context manager
so the process is spawned and torn down cleanly:

    async with make_mcp_server() as server:
        planner = build_pipeline(server)
        ...
"""
from __future__ import annotations

import sys

from agents import Agent
from agents.mcp import MCPServerStdio

from research_agents.executor import build_executor
from research_agents.planner import build_planner
from config import ROOT


def make_mcp_server() -> MCPServerStdio:
    """Spawn our self-built docs MCP server over stdio (same interpreter, repo cwd)."""
    return MCPServerStdio(
        name="docs-server",
        params={
            "command": sys.executable,
            "args": ["-m", "mcp_server.server"],
            "cwd": str(ROOT),
        },
        # Cache the tool list so we don't re-list on every agent turn.
        cache_tools_list=True,
    )


def build_pipeline(mcp_server: MCPServerStdio) -> Agent:
    """Wire Planner -> Executor -> Reviewer and return the entry agent (Planner)."""
    executor = build_executor(mcp_server)
    return build_planner(executor)
