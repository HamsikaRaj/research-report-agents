"""Three function tools exposed to the Executor agent.

Each is a plain Python function wrapped with @function_tool. The decorator reads
the type hints + docstring to build the JSON schema the model sees, and validates
the model's arguments against our Pydantic models before our code runs.

  1. web_search    - stand-in retrieval over a tiny in-memory corpus.
  2. compute_metric- deterministic math (real, fully auditable).
  3. save_report   - the only "write" action. Gated with needs_approval=True
                     so a human must approve before anything hits disk.
"""
from __future__ import annotations

import re

from agents import RunContextWrapper, function_tool

from research_agents.schemas import MetricRequest, Operation, SaveReportRequest, SearchQuery
from config import REPORTS_DIR

# A tiny, deterministic "search index". In a real system this is a web search or
# vector DB. We keep it local so the portfolio repo runs with zero extra keys.
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
    """Search the knowledge base for snippets relevant to a query.

    Ranks every entry by how many query words appear in its key+text, so it matches
    on meaning rather than requiring an exact key.

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
    else:  # percent_change: first -> last
        if vals[0] == 0:
            return "ERROR: percent_change undefined when the first value is 0."
        result = (vals[-1] - vals[0]) / abs(vals[0]) * 100
    return f"{args.operation.value} = {result:.4g}"


# needs_approval=True turns every call into a run "interruption": the Runner pauses
# and the host application (CLI) must approve or reject before the function runs.
@function_tool(needs_approval=True)
def save_report(ctx: RunContextWrapper, args: SaveReportRequest) -> str:
    """Persist the final report to disk. Requires human approval before writing.

    Args:
        args: The report title and body to save.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() else "-" for c in args.title.lower()).strip("-")
    path = REPORTS_DIR / f"{slug}.md"
    path.write_text(f"# {args.title}\n\n{args.body}\n", encoding="utf-8")
    return f"Saved report to {path}"
