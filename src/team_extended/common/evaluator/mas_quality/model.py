from pydantic import BaseModel, Field
from typing import List


class QualityScore(BaseModel):
    """Individual quality dimension score"""

    dimension: str = Field(description="Quality dimension name")
    score: int = Field(description="Score from 1-3", ge=1, le=3)
    justification: str = Field(description="Reasoning for the score")
    confidence: float = Field(description="Confidence in assessment", ge=0.0, le=1.0)


class ArgumentEvaluation(BaseModel):
    """Complete evaluation across all dimensions"""

    argument_text: str
    dimensions: List[QualityScore]
    overall_quality: float = Field(description="Aggregated quality score")


class EvaluatorConfig:
    """Configuration presets for different API rate limits"""

    CONSERVATIVE = {"max_concurrent_agents": 3, "retry_attempts": 3, "batch_delay": 2.0}
    MODERATE = {"max_concurrent_agents": 5, "retry_attempts": 3, "batch_delay": 1.0}
    AGGRESSIVE = {"max_concurrent_agents": 10, "retry_attempts": 2, "batch_delay": 0.5}
    UNLIMITED = {"max_concurrent_agents": 15, "retry_attempts": 1, "batch_delay": 0.1}
