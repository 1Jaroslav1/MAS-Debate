from typing import Dict, Any
from src.team_extended.common.evaluator.evaluator_interface import (
    ArgumentEvaluatorInterface,
)
from src.team_extended.common.evaluator.model import EvaluationScore, Argument


class GoDsAFEvaluatorAdapter(ArgumentEvaluatorInterface):
    """Adapter for the GoDsAF strategic evaluator"""

    def __init__(self, godsaf_evaluator, weight):
        self.godsaf_evaluator = godsaf_evaluator
        self._weight = weight

    @property
    def evaluator_name(self) -> str:
        return "GoDsAF_Strategic_Evaluator"

    @property
    def weight(self) -> float:
        return self._weight

    def evaluate(self, argument: Argument, **kwargs) -> Dict[str, Any]:
        """Evaluate using GoDsAF evaluator"""
        strategy_recommendation = kwargs.get("strategy_recommendation")
        candidate_id = kwargs.get("candidate_id")

        if not strategy_recommendation:
            raise ValueError(
                "GoDsAF evaluator requires strategy_recommendation parameter"
            )

        # Run evaluation
        evaluation = self.godsaf_evaluator.evaluate_argument_with_attacks(
            strategy_recommendation=strategy_recommendation,
            candidate_id=candidate_id
        )

        # Convert to unified format
        dimension_scores = [
            EvaluationScore(
                evaluator_name=self.evaluator_name,
                dimension="strategic_alignment",
                score=evaluation.strategic_alignment_score,
                raw_score=evaluation.strategic_alignment_score,
                justification="Strategic alignment with team goals",
                confidence=0.9,
            ),
            EvaluationScore(
                evaluator_name=self.evaluator_name,
                dimension="ugn_coverage",
                score=evaluation.ugn_coverage_score,
                raw_score=evaluation.ugn_coverage_score,
                justification="Coverage of unmet goal needs",
                confidence=0.8,
            ),
            EvaluationScore(
                evaluator_name=self.evaluator_name,
                dimension="domain_relevance",
                score=evaluation.domain_relevance_score,
                raw_score=evaluation.domain_relevance_score,
                justification="Relevance to strategic domains",
                confidence=0.7,
            ),
            EvaluationScore(
                evaluator_name=self.evaluator_name,
                dimension="goal_effectiveness",
                score=evaluation.goal_effectiveness_score,
                raw_score=evaluation.goal_effectiveness_score,
                justification="Effectiveness in achieving goals",
                confidence=0.8,
            ),
        ]

        return {
            "overall_score": evaluation.overall_score,
            "dimensions": dimension_scores,
            "metadata": {
                "original_evaluation": evaluation,
                "estimated_aps": evaluation.estimated_aps,
                "addresses_primary_ugn": evaluation.addresses_primary_ugn,
                "addresses_secondary_ugn": evaluation.addresses_secondary_ugn,
                "parsed_argument": evaluation.parsed_argument,
            },
            "feedback": {
                "positive": evaluation.positive_feedback,
                "negative": evaluation.strategic_gaps,
                "improvements": evaluation.improvement_suggestions,
                "strategic": evaluation.strategic_recommendations,
            },
        }
