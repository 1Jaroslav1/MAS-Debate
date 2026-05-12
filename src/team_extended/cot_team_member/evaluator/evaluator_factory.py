"""Evaluator factory for CoT (Chain of Thought) team members"""

from typing import List
from src.team_extended.common.evaluator import (
    MultiEvaluatorRunner,
    EvaluationConfig,
    ArgumentEvaluatorInterface,
)
from src.team_extended.common.evaluator.mas_quality import (
    ArgumentQualityEvaluator,
    QualityEvaluatorAdapter,
)
from src.team_extended.common.evaluator.chain_of_thought_evaluator import (
    ChainOfThoughtEvaluatorAdapter,
)


class CoTEvaluatorFactory:
    """Factory for creating evaluators for CoT team members"""

    @staticmethod
    def create_quality_evaluator(llm, config: EvaluationConfig) -> ArgumentEvaluatorInterface:
        """Create quality evaluator with specified configuration"""
        quality_evaluator = ArgumentQualityEvaluator(llm, **config.quality_config_type)
        return QualityEvaluatorAdapter(
            quality_evaluator, config.quality_evaluator_weight
        )

    @staticmethod
    def create_chain_of_thought_evaluator(
        llm, config: EvaluationConfig, godsaf_service=None
    ) -> ArgumentEvaluatorInterface:
        """Create chain-of-thought evaluator adapter"""
        return ChainOfThoughtEvaluatorAdapter(
            llm, config.godsaf_evaluator_weight, godsaf_service
        )

    @staticmethod
    def create_evaluators(
        llm,
        config: EvaluationConfig,
        godsaf_service=None,
    ) -> List[ArgumentEvaluatorInterface]:
        """
        Create all evaluators for CoT team members.
        
        Default configuration:
        - Quality Evaluator (Wachsmuth): Evaluates argument quality dimensions
        - Chain-of-Thought Evaluator: 7-step LLM-based strategic analysis
        
        Returns:
            List of configured evaluator instances
        """
        evaluators = [
            CoTEvaluatorFactory.create_quality_evaluator(llm, config),
            CoTEvaluatorFactory.create_chain_of_thought_evaluator(
                llm, config, godsaf_service
            ),
        ]
        return evaluators

    @staticmethod
    def create_multi_evaluator(
        llm,
        config: EvaluationConfig,
        godsaf_service=None,
    ) -> MultiEvaluatorRunner:
        """
        Create a multi-evaluator runner for CoT team members.
        
        This combines all CoT evaluators into a single runner that:
        - Runs evaluators in parallel
        - Combines results with weighted scoring
        - Generates consolidated feedback
        
        Args:
            llm: Language model for evaluation
            config: Evaluation configuration
            godsaf_service: Optional GoDsAF service (for argument storage)
            
        Returns:
            Configured MultiEvaluatorRunner instance
        """
        evaluators = CoTEvaluatorFactory.create_evaluators(llm, config, godsaf_service)
        return MultiEvaluatorRunner(evaluators)


# Convenience function for backward compatibility
def create_cot_evaluator(llm, config: EvaluationConfig, godsaf_service=None):
    """Convenience function to create CoT evaluator"""
    return CoTEvaluatorFactory.create_multi_evaluator(llm, config, godsaf_service)

