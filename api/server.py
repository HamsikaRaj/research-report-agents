"""FastAPI app that streams the pipeline over Server-Sent Events (SSE).

    uvicorn api.server:app --reload
    curl -N -X POST localhost:8000/stream -H 'content-type: application/json' \
         -d '{"query":"How do handoffs work?"}'

This is the "Responses API streaming over an HTTP endpoint" requirement: each token
delta and lifecycle event is forwarded to the client as a `data:` SSE frame. The
endpoint is non-interactive, so a paused write action is surfaced as an
`approval_required` event and then auto-rejected (the CLI is where a human approves).
"""
from __future__ import annotations

import json

from agents import Runner, add_trace_processor
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel

from research_agents.pipeline import build_pipeline, make_mcp_server
from research_agents.reviewer import ensure_report
from observability.tracing import JsonlCostProcessor

app = FastAPI(title="Research-and-Report Agents")

# Register the custom cost/latency processor once for the API process.
add_trace_processor(JsonlCostProcessor())


class Query(BaseModel):
    query: str


def _sse(event_type: str, payload: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **payload})}\n\n"


async def _emit(result):
    """Yield SSE frames for one streaming run."""
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            yield _sse("token", {"delta": event.data.delta})
        elif event.type == "agent_updated_stream_event":
            yield _sse("handoff", {"agent": event.new_agent.name})
        elif event.type == "run_item_stream_event" and event.item.type == "tool_call_item":
            name = getattr(event.item.raw_item, "name", "tool")
            yield _sse("tool", {"name": name})


async def event_stream(query: str):
    async with make_mcp_server() as server:
        planner = build_pipeline(server)
        result = Runner.run_streamed(planner, query)
        async for frame in _emit(result):
            yield frame

        # Non-interactive: surface and auto-reject any write approval.
        while result.interruptions:
            state = result.to_state()
            for interruption in result.interruptions:
                name = getattr(interruption, "name", "tool")
                yield _sse("approval_required", {"tool": name, "decision": "auto-rejected"})
                state.reject(interruption)
            result = Runner.run_streamed(planner, state)
            async for frame in _emit(result):
                yield frame

        report = await ensure_report(result.final_output)
        yield _sse("final", {"report": report.model_dump()})


@app.post("/stream")
async def stream(q: Query) -> StreamingResponse:
    return StreamingResponse(event_stream(q.query), media_type="text/event-stream")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
