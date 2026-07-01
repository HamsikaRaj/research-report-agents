"""Pydantic models for tool arguments and the pipeline's structured output."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=3, description="What to search for.")
    max_results: int = Field(
        3, ge=1, le=5, description="How many snippets to return (1-5)."
    )


class Operation(str, Enum):
    sum = "sum"
    mean = "mean"
    percent_change = "percent_change"


class MetricRequest(BaseModel):
    operation: Operation
    values: list[float] = Field(..., min_length=1, description="Numbers to operate on.")


class SaveReportRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    body: str = Field(..., min_length=10)


class PlanHandoff(BaseModel):
    """Structured payload the Planner sends when handing off to the Executor."""

    steps: list[str] = Field(..., min_length=1, description="Ordered research steps.")


class ReportResult(BaseModel):
    """The pipeline's typed final answer (the Reviewer's output_type)."""

    answer: str = Field(..., description="The final, validated answer.")
    sources: list[str] = Field(
        default_factory=list, description="Tools/docs the answer is grounded in."
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    reviewer_notes: str = Field(..., description="Why the reviewer accepted the answer.")
