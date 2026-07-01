"""Summarize runs.jsonl into the headline numbers for your resume.

    python -m observability.summarize

Reads the per-step log written by JsonlCostProcessor and prints totals/averages:
total tokens, total estimated cost, mean per-step latency, and a per-model breakdown.
"""
from __future__ import annotations

import json
from collections import defaultdict

from config import RUNS_LOG


def main() -> None:
    if not RUNS_LOG.exists():
        print(f"No log at {RUNS_LOG}. Run the pipeline first (python main.py '...').")
        return

    rows = [json.loads(line) for line in RUNS_LOG.read_text().splitlines() if line.strip()]
    if not rows:
        print("runs.jsonl is empty.")
        return

    tot_in = sum(r["input_tokens"] for r in rows)
    tot_out = sum(r["output_tokens"] for r in rows)
    tot_cost = sum(r["est_cost_usd"] for r in rows)
    lats = [r["latency_ms"] for r in rows if r.get("latency_ms") is not None]

    print(f"steps logged        : {len(rows)}")
    print(f"input tokens        : {tot_in}")
    print(f"output tokens       : {tot_out}")
    print(f"total tokens        : {tot_in + tot_out}")
    print(f"estimated cost (USD): ${tot_cost:.4f}")
    if lats:
        print(f"mean step latency   : {sum(lats) / len(lats):.0f} ms")

    by_model: dict[str, list] = defaultdict(list)
    for r in rows:
        by_model[r.get("model") or "unknown"].append(r)
    print("\nper-model:")
    for model, rs in by_model.items():
        c = sum(x["est_cost_usd"] for x in rs)
        t = sum(x["input_tokens"] + x["output_tokens"] for x in rs)
        print(f"  {model:<14} steps={len(rs):<3} tokens={t:<7} cost=${c:.4f}")


if __name__ == "__main__":
    main()
