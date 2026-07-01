"""LLM-as-judge scoring an answer on accuracy, groundedness, and faithfulness.

Each metric is 0.0-1.0, higher is better. Faithfulness is 1.0 when the answer has no
fabricated or contradictory claims. output_type=JudgeScores returns typed numbers we
can threshold in tests instead of prose.
"""
from __future__ import annotations

from agents import Agent, Runner
from pydantic import BaseModel, Field

from config import JUDGE_MODEL


class JudgeScores(BaseModel):
    accuracy: float = Field(..., ge=0.0, le=1.0)
    groundedness: float = Field(..., ge=0.0, le=1.0)
    hallucination: float = Field(
        ..., ge=0.0, le=1.0, description="Faithfulness: 1.0 = no hallucination."
    )
    rationale: str = Field(..., description="One sentence explaining the scores.")


JUDGE_INSTRUCTIONS = """You are a calibrated evaluation judge. You are given a
QUESTION, a REFERENCE answer, and a CANDIDATE answer produced by a system.

IMPORTANT: The REFERENCE is a MINIMAL correct answer, not an exhaustive one. The
candidate may include additional detail that is correct and on-topic. Do NOT penalize
the candidate for being more detailed or more specific than the reference. Only
penalize claims that CONTRADICT the reference or are clearly FABRICATED.

Score the CANDIDATE on three metrics, each 0.0-1.0 (higher is better):
- accuracy: does the candidate correctly answer the question and agree with the
  reference's meaning? Extra correct detail does not lower this.
- groundedness: are the candidate's claims consistent with the reference/domain?
  Additional correct, relevant detail is fine and must NOT lower this score.
- hallucination: faithfulness, 1.0 when the candidate contains no claims that
  contradict the reference or are fabricated. Lower only for contradictions or
  invented facts (never for merely adding true, relevant detail).

Be calibrated: a correct, grounded answer (even if more detailed than the reference)
should score near 1.0. A wrong or fabricated answer near 0.0. Give a one-sentence
rationale."""


def build_judge() -> Agent:
    return Agent(
        name="Judge",
        model=JUDGE_MODEL,
        instructions=JUDGE_INSTRUCTIONS,
        output_type=JudgeScores,
    )


async def score_answer(query: str, expected: str, actual: str) -> JudgeScores:
    """Judge a single candidate answer against the reference."""
    judge = build_judge()
    prompt = (
        f"QUESTION:\n{query}\n\n"
        f"REFERENCE answer:\n{expected}\n\n"
        f"CANDIDATE answer:\n{actual}"
    )
    result = await Runner.run(judge, prompt)
    return result.final_output
