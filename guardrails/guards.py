"""Input and output guardrails. The detection logic lives in detectors.py (pure,
SDK-free). These wrappers adapt it to the Agents SDK interface.
"""
from __future__ import annotations

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
)

from guardrails.detectors import pii_reason, quality_reason
from research_agents.schemas import ReportResult


@input_guardrail
async def input_pii_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    user_input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Trip if the input is empty, too long, or contains obvious PII."""
    text = user_input if isinstance(user_input, str) else str(user_input)
    reason = pii_reason(text)
    return GuardrailFunctionOutput(
        output_info={"reason": reason or "ok"},
        tripwire_triggered=bool(reason),
    )


@output_guardrail
async def output_quality_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: ReportResult,
) -> GuardrailFunctionOutput:
    """Trip if the final report is empty or cites no sources."""
    reason = quality_reason(output.answer, output.sources)
    return GuardrailFunctionOutput(
        output_info={"reason": reason or "ok"},
        tripwire_triggered=bool(reason),
    )
