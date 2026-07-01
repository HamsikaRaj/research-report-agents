"""Reviewer agent, the last hop. Its output_type makes the pipeline return a
typed ReportResult instead of free text, and its output guardrail rejects
ungrounded answers.
"""
from __future__ import annotations

from agents import Agent, Runner

from research_agents.schemas import ReportResult
from config import REVIEWER_MODEL
from guardrails.guards import output_quality_guardrail

REVIEWER_INSTRUCTIONS = """You are the Reviewer, the final checkpoint.
Read the Executor's findings already in the conversation. Produce a ReportResult:
- answer: a concise, accurate answer grounded ONLY in the gathered evidence.
- sources: the tool/doc names the evidence came from (e.g. "docs_lookup:handoffs",
  "web_search"). Never leave this empty if any evidence was used.
- confidence: 0.0-1.0. Lower it when evidence is thin or missing.
- reviewer_notes: one sentence on what you verified.
Do not invent facts. If the evidence does not support an answer, say so and set a
low confidence."""


def build_reviewer() -> Agent:
    return Agent(
        name="Reviewer",
        model=REVIEWER_MODEL,
        instructions=REVIEWER_INSTRUCTIONS,
        output_type=ReportResult,
        output_guardrails=[output_quality_guardrail],
    )


async def ensure_report(final_output) -> ReportResult:
    """Guarantee a validated, structured ReportResult.

    If the Executor already handed off to the Reviewer, `final_output` is already a
    ReportResult and we return it as-is (no extra model call). If the Executor
    skipped the handoff and answered in prose, we run the Reviewer here so the
    structured schema and the output guardrail always apply, validation is never
    optional.
    """
    if isinstance(final_output, ReportResult):
        return final_output
    reviewer = build_reviewer()
    prompt = (
        "The Executor produced the research answer below but skipped the handoff. "
        "Validate it and return a ReportResult, extracting the tool/doc names it "
        f"cites as sources.\n\n{final_output}"
    )
    result = await Runner.run(reviewer, prompt)
    return result.final_output
