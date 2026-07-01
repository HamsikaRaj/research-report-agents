"""Command-line entry point: run the pipeline with streaming, approval, and retries.

    python main.py "How do handoffs work in the Agents SDK?"
    python main.py "Summarize tracing and SAVE a report on it"
"""
from __future__ import annotations

import asyncio
import os
import sys

from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    add_trace_processor,
)
from openai.types.responses import ResponseTextDeltaEvent

from research_agents.pipeline import build_pipeline, make_mcp_server
from research_agents.reviewer import ensure_report
from research_agents.schemas import ReportResult
from observability.tracing import JsonlCostProcessor

MAX_RETRIES = 2
# Failures where retrying cannot help, so we stop immediately.
NON_RETRYABLE = ("insufficient_quota", "invalid_api_key", "quota", "billing", "permission")


async def _consume_stream(result) -> None:
    """Render a streaming run to the console until the iterator is exhausted."""
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            print(event.data.delta, end="", flush=True)
        elif event.type == "agent_updated_stream_event":
            print(f"\n\n[handoff] active agent -> {event.new_agent.name}")
        elif event.type == "run_item_stream_event":
            item = event.item
            if item.type == "tool_call_item":
                name = getattr(item.raw_item, "name", "tool")
                print(f"\n[tool] calling {name}")
            elif item.type == "tool_call_output_item":
                print(f"\n[tool] -> {str(item.output)[:120]}")


def _prompt_approval(interruption) -> bool:
    """Ask the human to approve a paused tool call."""
    name = getattr(interruption, "name", None) or getattr(
        getattr(interruption, "raw_item", None), "name", "tool"
    )
    args = getattr(interruption, "arguments", "")
    print(f"\n\n[approval] '{name}' wants to run with args: {args}")
    answer = input("[approval] approve this write action? [y/N] ").strip().lower()
    return answer in ("y", "yes")


async def _run_once(planner, query: str):
    """Stream the pipeline, then resolve any approval interruptions and resume."""
    result = Runner.run_streamed(planner, query)
    await _consume_stream(result)

    while result.interruptions:
        state = result.to_state()
        for interruption in result.interruptions:
            if _prompt_approval(interruption):
                state.approve(interruption)
            else:
                state.reject(interruption)
        result = Runner.run_streamed(planner, state)
        await _consume_stream(result)

    return result


async def run_with_retries(planner, query: str):
    """Retry transient failures with backoff. Fail fast on guardrails and quota/auth."""
    attempt = 0
    while True:
        try:
            return await _run_once(planner, query)
        except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered) as e:
            kind = "input" if isinstance(e, InputGuardrailTripwireTriggered) else "output"
            info = e.guardrail_result.output.output_info
            print(f"\n\n[guardrail] {kind} guardrail blocked the run: {info}")
            return None
        except Exception as e:
            if any(s in str(e).lower() for s in NON_RETRYABLE):
                print(f"\n\n[error] non-retryable failure (check billing/API key): {e}")
                raise
            attempt += 1
            if attempt > MAX_RETRIES:
                print(f"\n\n[error] giving up after {MAX_RETRIES} retries: {e}")
                raise
            wait = 2**attempt
            print(f"\n\n[retry] attempt {attempt} failed ({e}). Retrying in {wait}s")
            await asyncio.sleep(wait)


async def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("Set OPENAI_API_KEY in your environment or .env file first.")

    query = " ".join(sys.argv[1:]) or "How do handoffs work in the Agents SDK?"

    add_trace_processor(JsonlCostProcessor())

    print(f"[query] {query}\n")
    async with make_mcp_server() as server:
        planner = build_pipeline(server)
        result = await run_with_retries(planner, query)

    if result is None:
        return

    reviewed_via_handoff = isinstance(result.final_output, ReportResult)
    report = await ensure_report(result.final_output)
    tag = "handoff" if reviewed_via_handoff else "deterministic fallback"
    print(f"\n\n=== FINAL (structured ReportResult, reviewer via {tag}) ===")
    print(report.model_dump_json(indent=2))

    usage = result.context_wrapper.usage
    print(
        f"\n[usage] requests={usage.requests} "
        f"input_tokens={usage.input_tokens} output_tokens={usage.output_tokens} "
        f"total_tokens={usage.total_tokens}"
    )
    print("[usage] per-step token/latency/cost written to runs.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
