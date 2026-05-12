"""
Quality Evaluation Wrapper

This module provides wrapper functions for the ArgumentQualityEvaluator
to evaluate debate arguments and aggregate results.
"""

import asyncio
import logging
from typing import List, Dict, Any, Tuple
from src.team_extended.common.evaluator.model import Argument
from src.team_extended.common.evaluator.mas_quality.quality_evaluator import ArgumentQualityEvaluator
from src.team_extended.common.evaluator.mas_quality.model import (
    EvaluatorConfig,
    ArgumentEvaluation,
    QualityScore
)
from src.hub.llm_hub import gemini_3_flash

logger = logging.getLogger(__name__)


def initialize_evaluator() -> ArgumentQualityEvaluator:
    """
    Initialize ArgumentQualityEvaluator with gpt-4o-mini and MODERATE config.

    Returns:
        Configured ArgumentQualityEvaluator instance
    """
    logger.info("Initializing ArgumentQualityEvaluator with gpt-4o-mini")

    evaluator = ArgumentQualityEvaluator(
        llm=gemini_3_flash,
        **EvaluatorConfig.MODERATE
    )

    logger.info("Evaluator initialized successfully")
    return evaluator


async def evaluate_single_argument(
    evaluator: ArgumentQualityEvaluator,
    argument: Argument,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate a single argument and combine with metadata.

    Args:
        evaluator: ArgumentQualityEvaluator instance
        argument: Argument object to evaluate
        metadata: Metadata dict with argument details

    Returns:
        Dictionary containing metadata and quality evaluation
    """
    logger.info(f"Evaluating {metadata['argument_id']} from {metadata['team']}")

    try:
        # Evaluate argument
        evaluation: ArgumentEvaluation = await evaluator.evaluate_argument(argument)

        # Convert Pydantic model to dict
        evaluation_dict = evaluation.dict()

        # Combine metadata with evaluation
        result = {
            **metadata,
            'quality_evaluation': {
                'overall_quality': evaluation_dict['overall_quality'],
                'dimensions': [
                    {
                        'dimension': dim['dimension'],
                        'score': dim['score'],
                        'justification': dim['justification'],
                        'confidence': dim['confidence']
                    }
                    for dim in evaluation_dict['dimensions']
                ]
            }
        }

        logger.info(
            f"Evaluation complete for {metadata['argument_id']}: "
            f"overall_quality={evaluation_dict['overall_quality']:.2f}"
        )

        return result

    except Exception as e:
        logger.error(f"Error evaluating {metadata['argument_id']}: {e}")
        raise


async def evaluate_arguments_batch(
    evaluator: ArgumentQualityEvaluator,
    arguments: List[Tuple[Argument, Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Evaluate a batch of arguments with progress tracking.

    Args:
        evaluator: ArgumentQualityEvaluator instance
        arguments: List of (Argument, metadata) tuples

    Returns:
        List of evaluation result dictionaries
    """
    total = len(arguments)
    logger.info(f"Starting batch evaluation of {total} arguments")

    results = []

    for i, (argument, metadata) in enumerate(arguments, 1):
        logger.info(f"Progress: {i}/{total}")

        try:
            result = await evaluate_single_argument(evaluator, argument, metadata)
            results.append(result)

        except Exception as e:
            logger.error(f"Failed to evaluate argument {i}: {e}")
            # Continue with other arguments
            continue

    logger.info(f"Batch evaluation complete: {len(results)}/{total} successful")

    return results


def calculate_aggregate_statistics(
    evaluations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate aggregate statistics across all evaluations.

    Args:
        evaluations: List of evaluation result dictionaries

    Returns:
        Dictionary containing aggregate statistics
    """
    if not evaluations:
        return {
            'total_arguments': 0,
            'average_overall_quality': 0.0,
            'by_team_type': {},
            'by_architecture': {},
            'dimension_averages': {}
        }

    # Overall statistics
    total_arguments = len(evaluations)
    overall_qualities = [
        e['quality_evaluation']['overall_quality']
        for e in evaluations
    ]
    average_overall_quality = sum(overall_qualities) / total_arguments

    # Group by team_type
    by_team_type = {}
    for eval_data in evaluations:
        team_type = eval_data['team_type']

        if team_type not in by_team_type:
            by_team_type[team_type] = []

        by_team_type[team_type].append(
            eval_data['quality_evaluation']['overall_quality']
        )

    team_type_stats = {
        team_type: {
            'count': len(scores),
            'average_quality': sum(scores) / len(scores)
        }
        for team_type, scores in by_team_type.items()
    }

    # Group by architecture
    by_architecture = {}
    for eval_data in evaluations:
        arch = eval_data['architecture']

        if arch not in by_architecture:
            by_architecture[arch] = []

        by_architecture[arch].append(
            eval_data['quality_evaluation']['overall_quality']
        )

    architecture_stats = {
        arch: {
            'count': len(scores),
            'average_quality': sum(scores) / len(scores)
        }
        for arch, scores in by_architecture.items()
    }

    # Dimension averages
    dimension_scores = {}
    for eval_data in evaluations:
        for dim in eval_data['quality_evaluation']['dimensions']:
            dim_name = dim['dimension']

            if dim_name not in dimension_scores:
                dimension_scores[dim_name] = []

            dimension_scores[dim_name].append(dim['score'])

    dimension_averages = {
        dim_name: sum(scores) / len(scores)
        for dim_name, scores in dimension_scores.items()
    }

    return {
        'total_arguments': total_arguments,
        'average_overall_quality': round(average_overall_quality, 3),
        'by_team_type': {
            team_type: {
                'count': stats['count'],
                'average_quality': round(stats['average_quality'], 3)
            }
            for team_type, stats in team_type_stats.items()
        },
        'by_architecture': {
            arch: {
                'count': stats['count'],
                'average_quality': round(stats['average_quality'], 3)
            }
            for arch, stats in architecture_stats.items()
        },
        'dimension_averages': {
            dim: round(avg, 3)
            for dim, avg in dimension_averages.items()
        }
    }
