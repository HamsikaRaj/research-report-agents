"""Pytest gate: fail if judged averages fall below thresholds.

Skips when OPENAI_API_KEY is unset so a keyless CI does not fail.

    pytest evals/test_regression.py -v
"""
from __future__ import annotations

import os

import pytest

from evals.harness import evaluate

THRESHOLDS = {
    # Set ~0.10 below observed averages (acc/grnd/faith ~0.95) so real regressions
    # fail the gate but normal LLM-judge variance does not.
    "accuracy": 0.85,
    "groundedness": 0.85,
    "hallucination": 0.85,  # faithfulness: higher = less hallucination
}

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set. Skipping live eval regression.",
)


@pytest.fixture(scope="module")
def averages():
    """Run the eval harness once and share the averages across assertions."""
    result = __import__("asyncio").run(evaluate())
    return result["averages"]


@pytest.mark.parametrize("metric", list(THRESHOLDS))
def test_metric_above_threshold(averages, metric):
    got = averages[metric]
    floor = THRESHOLDS[metric]
    assert got >= floor, f"{metric}={got:.3f} fell below threshold {floor:.2f}"
