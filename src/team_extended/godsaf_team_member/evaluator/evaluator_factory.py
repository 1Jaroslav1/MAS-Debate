"""Evaluator factory for GoDsAF team members"""

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
from src.team_extended.common.evaluator.godsaf import (
    GoDsAFArgumentEvaluator,
    GoDsAFEvaluatorAdapter,
)
from src.reasoning.godsaf.godsaf_service import GoDsAFService


class GoDsAFEvaluatorFactory:
    @staticmethod
    def create_quality_evaluator(llm, config: EvaluationConfig) -> ArgumentEvaluatorInterface:
        quality_evaluator = ArgumentQualityEvaluator(llm, **config.quality_config_type)
        return QualityEvaluatorAdapter(
            quality_evaluator, config.quality_evaluator_weight
        )

    @staticmethod
    def create_godsaf_evaluator(
        godsaf_service: GoDsAFService, config: EvaluationConfig
    ) -> ArgumentEvaluatorInterface:
        godsaf_evaluator = GoDsAFArgumentEvaluator(godsaf_service)
        return GoDsAFEvaluatorAdapter(godsaf_evaluator, config.godsaf_evaluator_weight)

    @staticmethod
    def create_evaluators(
        llm,
        godsaf_service: GoDsAFService,
        config: EvaluationConfig,
    ) -> List[ArgumentEvaluatorInterface]:
        evaluators = [
            # GoDsAFEvaluatorFactory.create_quality_evaluator(llm, config),
            GoDsAFEvaluatorFactory.create_godsaf_evaluator(godsaf_service, config),
        ]
        return evaluators

    @staticmethod
    def create_multi_evaluator(
        llm,
        godsaf_service: GoDsAFService,
        config: EvaluationConfig,
    ) -> MultiEvaluatorRunner:
        evaluators = GoDsAFEvaluatorFactory.create_evaluators(llm, godsaf_service, config)
        return MultiEvaluatorRunner(evaluators)


# Convenience function for backward compatibility
def create_godsaf_evaluator(llm, godsaf_service: GoDsAFService, config: EvaluationConfig):
    """Convenience function to create GoDsAF evaluator"""
    return GoDsAFEvaluatorFactory.create_multi_evaluator(llm, godsaf_service, config)

