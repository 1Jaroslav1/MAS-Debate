"""Evaluator factory for ToT (Tree of Thoughts) team members"""

import logging
from typing import List, Optional
from langchain_core.language_models.chat_models import BaseChatModel

from src.team_extended.common.evaluator import (
    MultiEvaluatorRunner,
    EvaluationConfig,
    ArgumentEvaluatorInterface,
)
from src.team_extended.common.evaluator.mas_quality import (
    ArgumentQualityEvaluator,
    QualityEvaluatorAdapter,
)
from src.team_extended.common.evaluator.tree_of_thoughts.tree_of_thoughts_evaluator import TreeOfThoughtsEvaluator
from src.reasoning.godsaf.godsaf_service import GoDsAFService

logger = logging.getLogger(__name__)


class ToTEvaluatorFactory:
    """Factory for creating evaluators for ToT team members"""

    @staticmethod
    def create_quality_evaluator(llm, config: EvaluationConfig) -> ArgumentEvaluatorInterface:
        """Create quality evaluator with specified configuration"""
        quality_evaluator = ArgumentQualityEvaluator(llm, **config.quality_config_type)
        return QualityEvaluatorAdapter(
            quality_evaluator, config.quality_evaluator_weight
        )

    @staticmethod
    def create_tree_of_thoughts_evaluator(
        llm,
        config: EvaluationConfig,
        godsaf_service: Optional[GoDsAFService] = None,
        enable_fast_scoring: bool = True,
        use_llm_for_quick_score: bool = False
    ) -> TreeOfThoughtsEvaluator:
        """
        Create Tree of Thoughts evaluator

        Args:
            llm: Language model for evaluation
            config: Evaluation configuration
            godsaf_service: Optional GoDsAF service for argument storage
            enable_fast_scoring: Enable fast heuristic scoring
            use_llm_for_quick_score: Use LLM for quick scoring (slower but better)

        Returns:
            TreeOfThoughtsEvaluator instance
        """
        return TreeOfThoughtsEvaluator(
            llm=llm,
            weight=config.godsaf_evaluator_weight,
            enable_fast_scoring=enable_fast_scoring,
            use_llm_for_quick_score=use_llm_for_quick_score,
            godsaf_service=godsaf_service
        )

    @staticmethod
    def create_evaluators(
        llm,
        config: EvaluationConfig,
        godsaf_service: Optional[GoDsAFService] = None,
        enable_fast_scoring: bool = True,
        use_llm_for_quick_score: bool = False
    ) -> List[ArgumentEvaluatorInterface]:
        """
        Create all evaluators for ToT team members.

        Default configuration:
        - Quality Evaluator (Wachsmuth): Evaluates argument quality dimensions
        - Tree of Thoughts Evaluator: Fast + deep evaluation with branch exploration

        Args:
            llm: Language model for evaluation
            config: Evaluation configuration
            godsaf_service: Optional GoDsAF service for argument storage
            enable_fast_scoring: Enable fast heuristic scoring
            use_llm_for_quick_score: Use LLM for quick scoring

        Returns:
            List of configured evaluator instances
        """
        evaluators = [
            ToTEvaluatorFactory.create_quality_evaluator(llm, config),
            ToTEvaluatorFactory.create_tree_of_thoughts_evaluator(
                llm, config, godsaf_service, enable_fast_scoring, use_llm_for_quick_score
            ),
        ]
        return evaluators

    @staticmethod
    def create_multi_evaluator(
        llm,
        config: EvaluationConfig,
        godsaf_service: Optional[GoDsAFService] = None,
        enable_fast_scoring: bool = True,
        use_llm_for_quick_score: bool = False
    ) -> MultiEvaluatorRunner:
        """
        Create a multi-evaluator runner for ToT team members.

        This combines all ToT evaluators into a single runner that:
        - Runs evaluators in parallel
        - Combines results with weighted scoring
        - Generates consolidated feedback
        - Provides fast scoring for branch pruning

        Args:
            llm: Language model for evaluation
            config: Evaluation configuration
            godsaf_service: Optional GoDsAF service for argument storage
            enable_fast_scoring: Enable fast heuristic scoring
            use_llm_for_quick_score: Use LLM for quick scoring (slower but better)

        Returns:
            Configured MultiEvaluatorRunner instance
        """
        evaluators = ToTEvaluatorFactory.create_evaluators(
            llm, config, godsaf_service, enable_fast_scoring, use_llm_for_quick_score
        )
        return MultiEvaluatorRunner(evaluators)

    @staticmethod
    def get_tot_evaluator(
        multi_evaluator: MultiEvaluatorRunner
    ) -> Optional[TreeOfThoughtsEvaluator]:
        """
        Extract the ToT evaluator from a multi-evaluator runner.

        Useful for accessing ToT-specific methods like quick_evaluate.

        Args:
            multi_evaluator: MultiEvaluatorRunner instance

        Returns:
            TreeOfThoughtsEvaluator if found, None otherwise
        """
        for evaluator in multi_evaluator.evaluators:
            if isinstance(evaluator, TreeOfThoughtsEvaluator):
                return evaluator
        return None


# Convenience function for backward compatibility
def create_tot_evaluator(
    llm,
    config: EvaluationConfig,
    godsaf_service: Optional[GoDsAFService] = None,
    enable_fast_scoring: bool = True,
    use_llm_for_quick_score: bool = False
):
    """Convenience function to create ToT evaluator"""
    return ToTEvaluatorFactory.create_multi_evaluator(
        llm, config, godsaf_service, enable_fast_scoring, use_llm_for_quick_score
    )
