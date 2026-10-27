"""Adversarial guardrail evaluation. Deterministic, no API calls.

Runs crafted PII inputs and low-quality outputs through the guardrail logic and
reports the catch rate on adversarial cases and the false-positive rate on benign
controls.

    python -m evals.adversarial
"""
from __future__ import annotations

import json
from pathlib import Path

from guardrails.detectors import pii_reason, quality_reason

DATA = Path(__file__).resolve().parent / "adversarial.json"


def run() -> list[dict]:
    """Return one result row per case: id, kind, should_trip, tripped, reason, note."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    rows: list[dict] = []

    for c in data["input_cases"]:
        text = c["text"] * c.get("repeat", 1)
        reason = pii_reason(text)
        rows.append(
            {"id": c["id"], "kind": "input", "should_trip": c["should_trip"],
             "tripped": bool(reason), "reason": reason, "note": c["note"]}
        )

    for c in data["output_cases"]:
        reason = quality_reason(c["answer"], c["sources"])
        rows.append(
            {"id": c["id"], "kind": "output", "should_trip": c["should_trip"],
             "tripped": bool(reason), "reason": reason, "note": c["note"]}
        )
    return rows


def main() -> None:
    rows = run()
    adversarial = [r for r in rows if r["should_trip"]]
    controls = [r for r in rows if not r["should_trip"]]
    caught = [r for r in adversarial if r["tripped"]]
    missed = [r for r in adversarial if not r["tripped"]]
    false_pos = [r for r in controls if r["tripped"]]

    print(f"\n{'id':<13}{'kind':<8}{'expect':<8}{'result':<8}reason")
    print("-" * 72)
    for r in rows:
        expect = "block" if r["should_trip"] else "pass"
        result = "block" if r["tripped"] else "pass"
        ok = "ok" if r["should_trip"] == r["tripped"] else "MISS"
        print(f"{r['id']:<13}{r['kind']:<8}{expect:<8}{result:<8}{ok}  {r['reason']}")

    print(f"\nadversarial caught : {len(caught)}/{len(adversarial)}")
    print(f"false positives    : {len(false_pos)}/{len(controls)}")
    if missed:
        print("MISSED (adversarial not blocked):", [m["id"] for m in missed])
    if false_pos:
        print("FALSE POSITIVES (controls blocked):", [f["id"] for f in false_pos])


if __name__ == "__main__":
    main()
