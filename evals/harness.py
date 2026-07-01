"""Shared eval harness: run each golden item through the pipeline and judge it."""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from agents import Runner

from research_agents.pipeline import build_pipeline, make_mcp_server
from research_agents.reviewer import ensure_report
from evals.judge import score_answer

GOLDEN_PATH = Path(__file__).resolve().parent / "golden.json"
METRICS = ("accuracy", "groundedness", "hallucination")


def load_golden() -> list[dict]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


async def _answer_one(planner, query: str) -> str:
    """Run the pipeline non-streamed and return the final answer text."""
    result = await Runner.run(planner, query)
    while result.interruptions:
        state = result.to_state()
        for interruption in result.interruptions:
            state.reject(interruption)
        result = await Runner.run(planner, state)
    report = await ensure_report(result.final_output)
    return report.answer


async def evaluate(items: list[dict] | None = None) -> dict:
    """Run + judge every item. Returns {rows: [...], averages: {...}}."""
    items = items or load_golden()
    rows: list[dict] = []

    async with make_mcp_server() as server:
        planner = build_pipeline(server)
        for item in items:
            try:
                actual = await _answer_one(planner, item["query"])
                scores = await score_answer(item["query"], item["expected"], actual)
                row = {
                    "id": item["id"],
                    "query": item["query"],
                    "actual": actual,
                    "accuracy": scores.accuracy,
                    "groundedness": scores.groundedness,
                    "hallucination": scores.hallucination,
                    "rationale": scores.rationale,
                }
            except Exception as e:  # a failed run scores zero rather than crashing the suite
                row = {
                    "id": item["id"],
                    "query": item["query"],
                    "actual": f"ERROR: {e}",
                    "accuracy": 0.0,
                    "groundedness": 0.0,
                    "hallucination": 0.0,
                    "rationale": "run failed",
                }
            rows.append(row)

    averages = {m: round(mean(r[m] for r in rows), 3) for m in METRICS}
    return {"rows": rows, "averages": averages}
