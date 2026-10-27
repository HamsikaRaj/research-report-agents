"""Pure guardrail detection logic. Imports only the standard library, so it can be
unit-tested and run in CI without the Agents SDK or any API call.
"""
from __future__ import annotations

import re

# SSN (dash, space, or no separator), 13-16 digit card-like numbers, and emails.
# These are deliberately broad: a 9-digit or 13-16 digit run is treated as PII even
# if it is some other identifier, since over-blocking is the safer default here.
_SSN = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")
_CARD = re.compile(r"\b(?:\d[-\s.]?){13,16}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_MAX_QUERY_LEN = 2000


def pii_reason(text: str) -> str:
    """Return a reason string if the text should be blocked, else an empty string."""
    if not text.strip():
        return "empty query"
    if len(text) > _MAX_QUERY_LEN:
        return f"query exceeds {_MAX_QUERY_LEN} chars"
    if _SSN.search(text):
        return "looks like it contains an SSN"
    if _CARD.search(text):
        return "looks like it contains a card number"
    if _EMAIL.search(text):
        return "looks like it contains an email address"
    return ""


def quality_reason(answer: str, sources: list[str]) -> str:
    """Return a reason string if the answer is empty or ungrounded, else empty."""
    if not answer.strip():
        return "empty answer"
    if not sources:
        return "answer cites no sources (possible hallucination)"
    return ""
