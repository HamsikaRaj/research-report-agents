"""Executor agent, does the work. It has the three function tools plus the live
MCP server's tools, and hands off to the Reviewer when its research is done.
"""
from __future__ import annotations

from agents import Agent

from research_agents.reviewer import build_reviewer
from config import EXECUTOR_MODEL
from tools.research_tools import compute_metric, save_report, web_search

EXECUTOR_INSTRUCTIONS = """You are the Executor. Carry out the Planner's steps using
your tools:
- list_docs / docs_lookup (internal documentation, via MCP) for SDK concepts.
- web_search for the knowledge base.
- compute_metric for any arithmetic.
Gather concrete evidence and keep track of which tool/doc each fact came from.
If docs_lookup returns NO_DOC, call list_docs to see the available topics and retry
with one of them. Prefer the internal docs over web_search for SDK concepts.
Only if the user explicitly asked to SAVE or PERSIST a report, call save_report
(this pauses for human approval).

CRITICAL RULE: You must NOT answer the user and must NOT write the final report.
Do not produce any prose answer of your own. As soon as you have gathered enough
evidence, your ONLY remaining action is to call the `transfer_to_reviewer` handoff
so the Reviewer can validate and format the final answer. Handing off is mandatory."""


def build_executor(mcp_server) -> Agent:
    """Build the Executor wired to a *connected* MCPServerStdio instance."""
    reviewer = build_reviewer()
    return Agent(
        name="Executor",
        model=EXECUTOR_MODEL,
        instructions=EXECUTOR_INSTRUCTIONS,
        tools=[web_search, compute_metric, save_report],
        mcp_servers=[mcp_server],
        handoffs=[reviewer],
    )
