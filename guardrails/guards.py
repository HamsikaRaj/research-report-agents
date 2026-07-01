"""Deterministic input and output guardrails."""
from __future__ import annotations

import re

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
)

from research_agents.schemas import ReportResult

# US SSN and 13-16 digit card-like numbers.
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
_MAX_QUERY_LEN = 2000


@input_guardrail
async def input_pii_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    user_input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Trip if the input is empty, too long, or contains obvious PII."""
    text = user_input if isinstance(user_input, str) else str(user_input)
    reason = ""
    if not text.strip():
        reason = "empty query"
    elif len(text) > _MAX_QUERY_LEN:
        reason = f"query exceeds {_MAX_QUERY_LEN} chars"
    elif _SSN.search(text):
        reason = "looks like it contains an SSN"
    elif _CARD.search(text):
        reason = "looks like it contains a card number"

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
    reason = ""
    if not output.answer.strip():
        reason = "empty answer"
    elif not output.sources:
        reason = "answer cites no sources (possible hallucination)"

    return GuardrailFunctionOutput(
        output_info={"reason": reason or "ok"},
        tripwire_triggered=bool(reason),
    )
