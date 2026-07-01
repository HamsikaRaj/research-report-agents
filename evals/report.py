"""Run the whole golden set and print per-item scores and per-metric averages.

    python -m evals.report
"""
from __future__ import annotations

import asyncio

from evals.harness import METRICS, evaluate


async def main() -> None:
    result = await evaluate()
    rows, averages = result["rows"], result["averages"]

    print(f"\n{'id':<5} {'acc':>5} {'grnd':>5} {'hall':>5}  query")
    print("-" * 70)
    for r in rows:
        print(
            f"{r['id']:<5} {r['accuracy']:>5.2f} {r['groundedness']:>5.2f} "
            f"{r['hallucination']:>5.2f}  {r['query'][:44]}"
        )

    print("\n=== per-metric averages (n={}) ===".format(len(rows)))
    for m in METRICS:
        print(f"  {m:<13} {averages[m]:.3f}")
    overall = round(sum(averages.values()) / len(METRICS), 3)
    print(f"  {'OVERALL':<13} {overall:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
