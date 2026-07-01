"""Pipeline assembly and a shared MCP server factory."""
from __future__ import annotations

import sys

from agents import Agent
from agents.mcp import MCPServerStdio

from research_agents.executor import build_executor
from research_agents.planner import build_planner
from config import ROOT


def make_mcp_server() -> MCPServerStdio:
    """Return an MCPServerStdio that launches our docs server as a subprocess."""
    return MCPServerStdio(
        name="docs-server",
        params={
            "command": sys.executable,
            "args": ["-m", "mcp_server.server"],
            "cwd": str(ROOT),
        },
        cache_tools_list=True,
    )


def build_pipeline(mcp_server: MCPServerStdio) -> Agent:
    """Wire Planner to Executor to Reviewer and return the entry agent."""
    executor = build_executor(mcp_server)
    return build_planner(executor)
