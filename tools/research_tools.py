"""The three function tools the Executor can call."""
from __future__ import annotations

import re

from agents import RunContextWrapper, function_tool

from research_agents.schemas import MetricRequest, Operation, SaveReportRequest, SearchQuery
from config import REPORTS_DIR

# Stands in for a real search backend or vector DB so the repo runs with only an API key.
_CORPUS: dict[str, str] = {
    "responses api": "The Responses API is OpenAI's primary interface for model "
    "calls. It supports streaming events, tool calls, and structured outputs.",
    "agents sdk": "The OpenAI Agents SDK provides Agent, Runner, handoffs, function "
    "tools, guardrails, and tracing for building multi-agent systems.",
    "streaming": "Runner.run_streamed yields events you can render token-by-token, "
    "including raw response deltas and semantic run-item events.",
    "tracing": "Tracing records spans for agents, generations, and tool calls. You "
    "can add custom trace processors to export tokens, latency, and cost.",
}


@function_tool
def web_search(args: SearchQuery) -> str:
    """Search the knowledge base, ranking entries by query-word overlap.

    Args:
        args: The validated search query and result count.
    """
    words = [w for w in re.findall(r"[a-z0-9]+", args.query.lower()) if len(w) > 2]
    scored = []
    for key, text in _CORPUS.items():
        haystack = f"{key} {text}".lower()
        score = sum(haystack.count(w) for w in words)
        if score:
            scored.append((score, text))
    if not scored:
        return "NO_RESULTS: nothing relevant found in the knowledge base."
    scored.sort(key=lambda x: x[0], reverse=True)
    return "\n".join(f"- {t}" for _, t in scored[: args.max_results])


@function_tool
def compute_metric(args: MetricRequest) -> str:
    """Compute a simple aggregate metric over a list of numbers.

    Args:
        args: The operation to run and the values to run it on.
    """
    vals = args.values
    if args.operation is Operation.sum:
        result = sum(vals)
    elif args.operation is Operation.mean:
        result = sum(vals) / len(vals)
    else:
        if vals[0] == 0:
            return "ERROR: percent_change undefined when the first value is 0."
        result = (vals[-1] - vals[0]) / abs(vals[0]) * 100
    return f"{args.operation.value} = {result:.4g}"


@function_tool(needs_approval=True)
def save_report(ctx: RunContextWrapper, args: SaveReportRequest) -> str:
    """Persist the final report to disk. Pauses for human approval before writing.

    Args:
        args: The report title and body to save.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() else "-" for c in args.title.lower()).strip("-")
    path = REPORTS_DIR / f"{slug}.md"
    path.write_text(f"# {args.title}\n\n{args.body}\n", encoding="utf-8")
    return f"Saved report to {path}"
