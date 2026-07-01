"""Central configuration: models, pricing, paths. All secrets come from the
environment (.env), nothing sensitive is hardcoded here.

We use the "right model for the job" pattern:
  - Planner / Reviewer / Judge -> a stronger model (reasoning & validation quality)
  - Executor -> a cheaper/faster model (it mostly routes tool calls)
Both are overridable via environment variables so you can A/B models without
touching code.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env once, on import, so every module sees the same environment.
load_dotenv()

# --- Models (overridable via env) -------------------------------------------
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "gpt-4o")
EXECUTOR_MODEL = os.getenv("EXECUTOR_MODEL", "gpt-4o-mini")
REVIEWER_MODEL = os.getenv("REVIEWER_MODEL", "gpt-4o")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o")

# --- Pricing (USD per 1M tokens) --------------------------------------------
# Used only for *estimated* cost in the observability layer. Verify against
# https://openai.com/api/pricing/ before quoting numbers anywhere official.
PRICES: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

# --- Paths ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "mcp_server" / "docs"
RUNS_LOG = ROOT / "runs.jsonl"          # per-step token/latency/cost log
REPORTS_DIR = ROOT / "reports"          # where the gated save_report writes


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for a single generation step.

    The API returns versioned model names (e.g. "gpt-4o-2024-08-06"), so we match
    by longest known prefix, checking "gpt-4o-mini" before "gpt-4o".
    """
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
