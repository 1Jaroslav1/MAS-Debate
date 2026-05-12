from typing import Dict, List, Optional
from dataclasses import dataclass
from src.team_extended.common.evaluator.model import EvaluationResult


@dataclass
class ArgumentEvaluation:
    result: EvaluationResult
    overall_score: float  # 0-100

    # Detailed scores
    strategic_alignment_score: float  # 0-100
    ugn_coverage_score: float  # 0-100
    domain_relevance_score: float  # 0-100
    goal_effectiveness_score: float  # 0-100
    estimated_aps: float  # From GoDsAF evaluation

    # Strategic analysis
    addresses_primary_ugn: bool
    addresses_secondary_ugn: bool
    strategic_gaps: List[str]
    competitive_advantages: List[str]

    # Feedback
    positive_feedback: List[str]
    improvement_suggestions: List[str]
    strategic_recommendations: List[str]

    # Detailed analysis
    parsed_argument: Optional[Dict]
    ugn_analysis: str
    evaluation_summary: str
