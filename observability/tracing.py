"""Custom trace processor that logs per-step tokens, latency, and cost to JSONL.

Runs alongside the SDK's built-in tracer via add_trace_processor, so the default
exporter stays on.
"""
from __future__ import annotations

import json
import threading
import time
from typing import Any

from agents.tracing import TracingProcessor

from config import RUNS_LOG, estimate_cost


def _usage_tokens(usage: Any) -> tuple[int, int]:
    """Read (input, output) token counts from a usage dict or ResponseUsage object."""
    if usage is None:
        return 0, 0

    def get(key: str):
        if isinstance(usage, dict):
            return usage.get(key)
        return getattr(usage, key, None)

    in_tok = get("input_tokens") or get("prompt_tokens") or 0
    out_tok = get("output_tokens") or get("completion_tokens") or 0
    return int(in_tok or 0), int(out_tok or 0)


class JsonlCostProcessor(TracingProcessor):
    def __init__(self, path=RUNS_LOG) -> None:
        self.path = path
        self._starts: dict[str, float] = {}
        self._lock = threading.Lock()

    def on_trace_start(self, trace) -> None:
        pass

    def on_trace_end(self, trace) -> None:
        pass

    def on_span_start(self, span) -> None:
        if span.span_id:
            self._starts[span.span_id] = time.monotonic()

    def on_span_end(self, span) -> None:
        start = self._starts.pop(span.span_id, None)
        latency_ms = round((time.monotonic() - start) * 1000, 1) if start else None

        # Responses API keeps usage/model on span_data.response. Chat Completions
        # keeps them on span_data directly.
        data = span.span_data
        response = getattr(data, "response", None)
        usage = getattr(response, "usage", None) if response is not None else None
        model = getattr(response, "model", None) if response is not None else None
        if usage is None:
            usage = getattr(data, "usage", None)
        if model is None:
            model = getattr(data, "model", None)

        # Skip spans with no model: non-model spans and usage-only duplicates. This
        # keeps one record per real model call so token and cost totals stay exact.
        if not model:
            return

        in_tok, out_tok = _usage_tokens(usage)
        record = {
            "ts": time.time(),
            "trace_id": getattr(span, "trace_id", None),
            "span": type(data).__name__,
            "model": model,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "latency_ms": latency_ms,
            "est_cost_usd": round(estimate_cost(model, in_tok, out_tok), 6),
        }
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

    def shutdown(self) -> None:
        pass

    def force_flush(self) -> None:
        pass
