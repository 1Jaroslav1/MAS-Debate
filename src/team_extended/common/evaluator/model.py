from typing import Dict, List, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class EvaluationResult(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    REJECT = "reject"


@dataclass
class EvaluationScore:
    """Individual evaluation score from any evaluator"""

    evaluator_name: str
    dimension: str
    score: float
    raw_score: Union[int, float]
    justification: str
    confidence: float = 1.0


@dataclass
class UnifiedArgumentEvaluation:
    """Unified evaluation result combining multiple evaluators"""

    argument_text: str
    topic: str

    final_result: EvaluationResult
    overall_score: float

    evaluator_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    evaluator_records: List['EvaluatorResultRecord'] = field(default_factory=list)  # NEW: Per-evaluator records
    individual_scores: List[EvaluationScore] = field(default_factory=list)

    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    strategic_recommendations: List[str] = field(default_factory=list)

    acceptance_factors: List[str] = field(default_factory=list)
    rejection_factors: List[str] = field(default_factory=list)

    evaluation_timestamp: datetime = field(default_factory=datetime.now)
    evaluators_used: List[str] = field(default_factory=list)
    evaluation_summary: str = ""


@dataclass
class EvaluatorResultRecord:
    """Record of a single evaluator's result for an argument"""

    evaluator_name: str
    overall_score: float
    dimensions: List[EvaluationScore] = field(default_factory=list)
    feedback: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ArgumentEvaluationLog:
    """Complete evaluation log for an argument including all evaluator results"""

    argument_name: str
    argument_text: str
    team_name: str
    topic: str

    final_result: EvaluationResult
    overall_score: float
    evaluator_records: List[EvaluatorResultRecord] = field(default_factory=list)

    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Argument:
    """Represents an argument to be evaluated"""

    text: str
    topic: str
    team_type: str
    team_perspective: str
    viewpoint_orientation: str


@dataclass
class EvaluationNodeConfig:
    active: bool = True

    def validate_config(self) -> List[str]:
        warnings = []
        if not self.active:
            warnings.append(
                "evaluation_node_config.active=False: Argument will be committed without "
                "evaluation or iterative refinement."
            )
        return warnings
