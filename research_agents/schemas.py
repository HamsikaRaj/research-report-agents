"""Pydantic models shared across agents and tools.

Two roles for Pydantic here:
  1. Tool argument validation, function tools take typed/validated inputs so the
     model can't pass garbage (function/tool calling + structured inputs).
  2. Structured final output, the Reviewer's `output_type` is `ReportResult`, so
     the pipeline returns a typed object, not free-form text (structured outputs).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# --- Tool argument models ----------------------------------------------------
class SearchQuery(BaseModel):
    """Validated args for the web_search tool."""

    query: str = Field(..., min_length=3, description="What to search for.")
    max_results: int = Field(
        3, ge=1, le=5, description="How many snippets to return (1-5)."
    )


class Operation(str, Enum):
    sum = "sum"
    mean = "mean"
    percent_change = "percent_change"


class MetricRequest(BaseModel):
    """Validated args for the compute_metric tool."""

    operation: Operation
    values: list[float] = Field(..., min_length=1, description="Numbers to operate on.")


class SaveReportRequest(BaseModel):
    """Validated args for the gated save_report write action."""

    title: str = Field(..., min_length=3, max_length=120)
    body: str = Field(..., min_length=10)


# --- Handoff payloads --------------------------------------------------------
class PlanHandoff(BaseModel):
    """Structured payload the Planner attaches when handing off to the Executor.

    Surfaced as the handoff tool's arguments, so the model must produce a real
    plan before control transfers (and we log it via on_handoff).
    """

    steps: list[str] = Field(..., min_length=1, description="Ordered research steps.")


# --- Final structured output -------------------------------------------------
class ReportResult(BaseModel):
    """The pipeline's typed final answer (Reviewer's output_type)."""

    answer: str = Field(..., description="The final, validated answer.")
    sources: list[str] = Field(
        default_factory=list, description="Tools/docs the answer is grounded in."
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    reviewer_notes: str = Field(..., description="Why the reviewer accepted the answer.")
