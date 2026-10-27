"""Deterministic guardrail gate: no API key needed, safe to run in CI.

Requires the adversarial set to be fully caught with no false positives.

    pytest evals/test_guardrails.py -v
"""
from __future__ import annotations

from evals.adversarial import run


def test_catches_all_adversarial():
    missed = [r["id"] for r in run() if r["should_trip"] and not r["tripped"]]
    assert not missed, f"adversarial inputs slipped past the guardrails: {missed}"


def test_no_false_positives_on_controls():
    false_pos = [r["id"] for r in run() if not r["should_trip"] and r["tripped"]]
    assert not false_pos, f"benign controls were wrongly blocked: {false_pos}"
