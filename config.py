"""Models, pricing, and paths. Secrets are read from the environment (.env)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PLANNER_MODEL = os.getenv("PLANNER_MODEL", "gpt-4o")
EXECUTOR_MODEL = os.getenv("EXECUTOR_MODEL", "gpt-4o-mini")
REVIEWER_MODEL = os.getenv("REVIEWER_MODEL", "gpt-4o")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o")

# USD per 1M tokens. Verify against https://openai.com/api/pricing/ before quoting.
PRICES: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "mcp_server" / "docs"
RUNS_LOG = ROOT / "runs.jsonl"
REPORTS_DIR = ROOT / "reports"


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for one step, matching versioned model names by prefix."""
    price = PRICES.get(model)
    if price is None:
        for key in sorted(PRICES, key=len, reverse=True):
            if model.startswith(key):
                price = PRICES[key]
                break
    if price is None:
        return 0.0
    return (input_tokens / 1_000_000) * price["input"] + (
        output_tokens / 1_000_000
    ) * price["output"]
