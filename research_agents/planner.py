"""Planner agent: decomposes the query and hands off to the Executor."""
from __future__ import annotations

import sys

from agents import Agent, RunContextWrapper, handoff

from research_agents.schemas import PlanHandoff
from config import PLANNER_MODEL
from guardrails.guards import input_pii_guardrail

PLANNER_INSTRUCTIONS = """You are the Planner for a system that answers questions
about the OpenAI Agents SDK using an INTERNAL knowledge base only:
- an internal docs set (topics: agents, handoffs, guardrails, tools, tracing, mcp,
  streaming), searchable via docs_lookup / list_docs.
- a small internal snippet knowledge base, searchable via web_search.
Do NOT plan to use the public web, external vendors, or academic sources, the answer
lives in the internal docs. Break the question into 2-4 concrete, ordered steps that
name which internal doc/topic to look up and what to search for, then immediately hand
off to the Executor with those steps. Do NOT answer the question yourself and do NOT
call research tools, your only job is to plan and delegate."""


async def _on_handoff(ctx: RunContextWrapper, plan: PlanHandoff) -> None:
    """Log the structured plan as control transfers to the Executor."""
    print("\n[planner] plan:", file=sys.stderr)
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step}", file=sys.stderr)


def build_planner(executor: Agent) -> Agent:
    return Agent(
        name="Planner",
        model=PLANNER_MODEL,
        instructions=PLANNER_INSTRUCTIONS,
        handoffs=[
            handoff(executor, on_handoff=_on_handoff, input_type=PlanHandoff),
        ],
        input_guardrails=[input_pii_guardrail],
    )
