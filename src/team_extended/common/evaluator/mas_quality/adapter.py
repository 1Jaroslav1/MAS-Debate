import asyncio
from typing import Dict, Any
from src.team_extended.common.evaluator.evaluator_interface import (
    ArgumentEvaluatorInterface,
)
from src.team_extended.common.evaluator.model import Argument, EvaluationScore


class QualityEvaluatorAdapter(ArgumentEvaluatorInterface):
    """Adapter for the Wachsmuth quality evaluator"""

    def __init__(self, quality_evaluator, weight):
        self.quality_evaluator = quality_evaluator
        self._weight = weight

    @property
    def evaluator_name(self) -> str:
        return "Wachsmuth_Quality_Evaluator"

    @property
    def weight(self) -> float:
        return self._weight

    def evaluate(self, argument: Argument, **kwargs) -> Dict[str, Any]:
        """Evaluate using quality evaluator"""

        # Convert to quality evaluator format
        quality_arg = argument  # Already compatible

        # Run evaluation
        evaluation =  asyncio.run(self.quality_evaluator.evaluate_argument(quality_arg))

        # Convert dimensions to unified format
        dimension_scores = []
        for dim_score in evaluation.dimensions:
            normalized_score = self.normalize_score(dim_score.score, 3)
            eval_score = EvaluationScore(
                evaluator_name=self.evaluator_name,
                dimension=dim_score.dimension,
                score=normalized_score,
                raw_score=dim_score.score,
                justification=dim_score.justification,
                confidence=dim_score.confidence,
            )
            dimension_scores.append(eval_score)

        # Extract feedback
        positive_feedback = []
        negative_feedback = []
        improvements = []

        for score in dimension_scores:
            if score.score >= 80:
                positive_feedback.append(
                    f"Strong {score.dimension}: {score.justification}"
                )
            elif score.score <= 40:
                negative_feedback.append(
                    f"Weak {score.dimension}: {score.justification}"
                )
                improvements.append(
                    f"Improve {score.dimension}: Focus on {score.dimension.replace('_', ' ')}"
                )

        overall_score = self.normalize_score(evaluation.overall_quality, 3)

        return {
            "overall_score": overall_score,
            "dimensions": dimension_scores,
            "metadata": {
                "original_evaluation": evaluation,
                "aggregated_quality": evaluation.overall_quality,
            },
            "feedback": {
                "positive": positive_feedback,
                "negative": negative_feedback,
                "improvements": improvements,
                "strategic": [],
            },
        }
