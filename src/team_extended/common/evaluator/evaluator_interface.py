from typing import Dict, Union, Any
from abc import ABC, abstractmethod
from src.team_extended.common.evaluator.model import Argument


class ArgumentEvaluatorInterface(ABC):
    """Common interface for all argument evaluators"""

    @property
    @abstractmethod
    def evaluator_name(self) -> str:
        """Name of the evaluator"""
        pass

    @property
    @abstractmethod
    def weight(self) -> float:
        """Weight of this evaluator in final scoring (0.0-1.0)"""
        pass

    @abstractmethod
    def evaluate(self, argument: Argument, **kwargs) -> Dict[str, Any]:
        """
        Evaluate an argument and return results

        Returns:
            Dict containing:
            - overall_score: float (0-100)
            - dimensions: List[EvaluationScore]
            - metadata: Dict with evaluator-specific data
            - feedback: Dict with positive/negative feedback
        """
        pass

    def normalize_score(
        self, raw_score: Union[int, float], max_score: Union[int, float]
    ) -> float:
        """Normalize raw score to 0-100 scale"""
        return min(100.0, max(0.0, (raw_score / max_score) * 100))
