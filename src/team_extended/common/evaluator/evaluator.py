from typing import Dict, List, Any
import asyncio
import logging
from src.team_extended.common.evaluator.evaluator_interface import ArgumentEvaluatorInterface
from src.team_extended.common.evaluator.model import (
    Argument,
    UnifiedArgumentEvaluation,
    EvaluationResult,
    EvaluationScore,
    EvaluatorResultRecord,
)
from src.team_extended.common.evaluator.mas_quality.quality_evaluator import (
    EvaluatorConfig,
)
from src.team_extended.common.evaluator.mas_quality.model import EvaluatorConfig
from src.hub import gpt_4o_mini
from src.reasoning.godsaf.godsaf_service import GoDsAFService

logger = logging.getLogger(__name__)


class MultiEvaluatorRunner:
    """Runs multiple evaluators and combines results"""

    def __init__(self, evaluators: List[ArgumentEvaluatorInterface]):
        self.evaluators = evaluators

        total_weight = sum(e.weight for e in evaluators)
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Evaluator weights sum to {total_weight}, not 1.0")

    def evaluate_argument(self, argument: Argument, **kwargs) -> UnifiedArgumentEvaluation:
        """Run all evaluators and combine results"""

        logger.info(f"Starting evaluation with {len(self.evaluators)} evaluators")

        # Run all evaluators
        evaluator_results = {}
        evaluator_records = []
        all_dimension_scores = []
        all_feedback = {
            "positive": [],
            "negative": [],
            "improvements": [],
            "strategic": [],
        }

        weighted_score_sum = 0.0
        total_weight = 0.0

        for evaluator in self.evaluators:
            try:
                logger.info(f"Running {evaluator.evaluator_name}")

                # Run evaluation
                result = evaluator.evaluate(argument, **kwargs)

                # Store results
                evaluator_results[evaluator.evaluator_name] = result
                all_dimension_scores.extend(result["dimensions"])

                evaluator_record = EvaluatorResultRecord(
                    evaluator_name=evaluator.evaluator_name,
                    overall_score=result["overall_score"],
                    dimensions=result["dimensions"],
                    feedback=result["feedback"],
                    metadata=result.get("metadata", {})
                )
                evaluator_records.append(evaluator_record)

                # Accumulate feedback
                for key in all_feedback.keys():
                    all_feedback[key].extend(result["feedback"].get(key, []))

                # Calculate weighted score
                weighted_score_sum += result["overall_score"] * evaluator.weight
                total_weight += evaluator.weight

                logger.info(
                    f"{evaluator.evaluator_name} completed: {result['overall_score']:.1f}"
                )

            except Exception as e:
                logger.error(f"Error in {evaluator.evaluator_name}: {str(e)}")
                # Continue with other evaluators
                continue

        # Calculate final score
        final_score = weighted_score_sum / total_weight if total_weight > 0 else 0.0

        # Determine final result
        final_result = self._determine_final_result(final_score, evaluator_results)

        # Generate consolidated feedback
        consolidated_feedback = self._consolidate_feedback(
            all_feedback, evaluator_results
        )

        # Generate acceptance/rejection factors
        acceptance_factors, rejection_factors = self._analyze_decision_factors(
            final_score, evaluator_results, all_dimension_scores
        )

        # Create unified evaluation
        unified_eval = UnifiedArgumentEvaluation(
            argument_text=argument.text,
            topic=argument.topic,
            final_result=final_result,
            overall_score=final_score,
            evaluator_results=evaluator_results,
            evaluator_records=evaluator_records,
            individual_scores=all_dimension_scores,
            strengths=consolidated_feedback["strengths"],
            weaknesses=consolidated_feedback["weaknesses"],
            improvement_suggestions=consolidated_feedback["improvements"],
            strategic_recommendations=consolidated_feedback["strategic"],
            acceptance_factors=acceptance_factors,
            rejection_factors=rejection_factors,
            evaluators_used=[e.evaluator_name for e in self.evaluators],
            evaluation_summary=self._generate_summary(
                final_result, final_score, consolidated_feedback
            ),
        )

        logger.info(f"Evaluation completed: {final_result.value} ({final_score:.1f})")
        return unified_eval

    def _determine_final_result(
        self, score: float, evaluator_results: Dict
    ) -> EvaluationResult:
        """Determine final result based on score and individual evaluator results"""

        # Check for any critical failures
        for _, result in evaluator_results.items():
            if result["overall_score"] < 20:  # Critical failure threshold
                return EvaluationResult.REJECT

        # Score-based determination with some flexibility
        if score >= 85:
            return EvaluationResult.EXCELLENT
        elif score >= 70:
            return EvaluationResult.GOOD
        elif score >= 55:
            return EvaluationResult.FAIR
        elif score >= 40:
            return EvaluationResult.POOR
        else:
            return EvaluationResult.REJECT

    def _consolidate_feedback(
        self, all_feedback: Dict, evaluator_results: Dict
    ) -> Dict[str, List[str]]:
        """Consolidate feedback from all evaluators"""

        # Remove duplicates and prioritize
        strengths = list(set(all_feedback["positive"]))
        weaknesses = list(set(all_feedback["negative"]))
        improvements = list(set(all_feedback["improvements"]))
        strategic = list(set(all_feedback["strategic"]))

        # Sort by importance (this could be more sophisticated)
        strengths.sort(key=len, reverse=True)  # Longer descriptions often more detailed
        improvements.sort(key=len, reverse=True)

        return {
            "strengths": strengths[:5],  # Top 5
            "weaknesses": weaknesses[:5],
            "improvements": improvements[:7],
            "strategic": strategic[:3],
        }

    def _analyze_decision_factors(
        self,
        score: float,
        evaluator_results: Dict,
        dimension_scores: List[EvaluationScore],
    ) -> tuple[List[str], List[str]]:
        """Analyze factors supporting acceptance vs rejection"""

        acceptance_factors = []
        rejection_factors = []

        # Score-based factors
        if score >= 80:
            acceptance_factors.append(f"High overall score ({score:.1f}/100)")
        elif score <= 40:
            rejection_factors.append(f"Low overall score ({score:.1f}/100)")

        # Evaluator agreement
        scores = [result["overall_score"] for result in evaluator_results.values()]
        if len(scores) > 1:
            score_variance = max(scores) - min(scores)
            if score_variance < 20:
                acceptance_factors.append("Strong evaluator agreement")
            elif score_variance > 40:
                rejection_factors.append("High evaluator disagreement")

        # Dimension analysis
        high_scores = [s for s in dimension_scores if s.score >= 80]
        low_scores = [s for s in dimension_scores if s.score <= 40]

        if len(high_scores) >= 3:
            acceptance_factors.append(
                f"Multiple strong dimensions ({len(high_scores)})"
            )

        if len(low_scores) >= 3:
            rejection_factors.append(f"Multiple weak dimensions ({len(low_scores)})")

        # Strategic factors (if GoDsAF present)
        godsaf_result = evaluator_results.get("GoDsAF_Strategic_Evaluator")
        if godsaf_result:
            metadata = godsaf_result["metadata"]
            if metadata.get("addresses_primary_ugn"):
                acceptance_factors.append("Addresses primary strategic need")
            if not metadata.get("addresses_primary_ugn") and not metadata.get(
                "addresses_secondary_ugn"
            ):
                rejection_factors.append("Does not address strategic priorities")

        return acceptance_factors, rejection_factors

    def _generate_summary(
        self, result: EvaluationResult, score: float, feedback: Dict[str, List[str]]
    ) -> str:
        """Generate evaluation summary"""

        summary_parts = []
        summary_parts.append(
            f"EVALUATION RESULT: {result.value.upper()} ({score:.1f}/100)"
        )
        summary_parts.append("")

        if feedback["strengths"]:
            summary_parts.append("KEY STRENGTHS:")
            for strength in feedback["strengths"][:3]:
                summary_parts.append(f"  ✓ {strength}")
            summary_parts.append("")

        if feedback["improvements"]:
            summary_parts.append("IMPROVEMENT PRIORITIES:")
            for improvement in feedback["improvements"][:3]:
                summary_parts.append(f"  → {improvement}")
            summary_parts.append("")

        if feedback["strategic"]:
            summary_parts.append("STRATEGIC RECOMMENDATIONS:")
            for rec in feedback["strategic"][:2]:
                summary_parts.append(f"  ⚡ {rec}")

        return "\n".join(summary_parts)


class EvaluationConfig:
    """Configuration class for evaluation settings"""

    def __init__(self):
        # Quality evaluator settings
        self.quality_evaluator_weight = 0.6
        self.quality_config_type = EvaluatorConfig.MODERATE

        # GoDsAF evaluator settings
        self.godsaf_evaluator_weight = 0.4

        # Scoring thresholds
        self.excellent_threshold = 85
        self.good_threshold = 70
        self.fair_threshold = 55
        self.poor_threshold = 40

        # Feedback limits
        self.max_strengths = 5
        self.max_improvements = 7
        self.max_strategic_recommendations = 3

        # Error handling
        self.continue_on_evaluator_error = True
        self.min_evaluators_required = 1


class EvaluationAnalyzer:
    """Analyzer for detailed evaluation insights"""

    @staticmethod
    def analyze_dimension_patterns(
        evaluation: UnifiedArgumentEvaluation,
    ) -> Dict[str, Any]:
        """Analyze patterns in dimension scores"""

        scores_by_evaluator = {}
        scores_by_dimension = {}

        for score in evaluation.individual_scores:
            # Group by evaluator
            if score.evaluator_name not in scores_by_evaluator:
                scores_by_evaluator[score.evaluator_name] = []
            scores_by_evaluator[score.evaluator_name].append(score.score)

            # Group by dimension
            if score.dimension not in scores_by_dimension:
                scores_by_dimension[score.dimension] = []
            scores_by_dimension[score.dimension].append(score.score)

        # Calculate statistics
        analysis = {
            "evaluator_averages": {
                name: sum(scores) / len(scores)
                for name, scores in scores_by_evaluator.items()
            },
            "dimension_averages": {
                dim: sum(scores) / len(scores)
                for dim, scores in scores_by_dimension.items()
            },
            "strongest_dimensions": [],
            "weakest_dimensions": [],
            "evaluator_agreement": 0.0,
        }

        # Find strongest and weakest dimensions
        dim_avgs = analysis["dimension_averages"]
        if dim_avgs:
            sorted_dims = sorted(dim_avgs.items(), key=lambda x: x[1], reverse=True)
            analysis["strongest_dimensions"] = sorted_dims[:3]
            analysis["weakest_dimensions"] = sorted_dims[-3:]

        # Calculate evaluator agreement (inverse of variance)
        eval_avgs = list(analysis["evaluator_averages"].values())
        if len(eval_avgs) > 1:
            variance = sum(
                (x - sum(eval_avgs) / len(eval_avgs)) ** 2 for x in eval_avgs
            ) / len(eval_avgs)
            analysis["evaluator_agreement"] = max(0, 100 - variance)

        return analysis

    @staticmethod
    def generate_detailed_report(evaluation: UnifiedArgumentEvaluation) -> str:
        """Generate comprehensive evaluation report"""

        analysis = EvaluationAnalyzer.analyze_dimension_patterns(evaluation)

        report_parts = []
        report_parts.append("DETAILED EVALUATION REPORT")
        report_parts.append("=" * 50)
        report_parts.append(f"Argument: {evaluation.argument_text[:100]}...")
        report_parts.append(f"Topic: {evaluation.topic}")
        report_parts.append(f"Stance: {evaluation.stance}")
        report_parts.append(f"Evaluation Time: {evaluation.evaluation_timestamp}")
        report_parts.append("")

        # Overall results
        report_parts.append("OVERALL RESULTS")
        report_parts.append("-" * 20)
        report_parts.append(f"Final Result: {evaluation.final_result.value.upper()}")
        report_parts.append(f"Overall Score: {evaluation.overall_score:.1f}/100")
        report_parts.append(f"Evaluators Used: {', '.join(evaluation.evaluators_used)}")
        report_parts.append("")

        report_parts.append("INDIVIDUAL SCORES")
        report_parts.append("-" * 20)
        report_parts.append(evaluation.individual_scores)
        report_parts.append(evaluation.evaluator_results)

        # Evaluator breakdown
        report_parts.append("EVALUATOR BREAKDOWN")
        report_parts.append("-" * 20)
        for eval_name, avg_score in analysis["evaluator_averages"].items():
            report_parts.append(f"{eval_name}: {avg_score:.1f}/100")
        report_parts.append(
            f"Evaluator Agreement: {analysis['evaluator_agreement']:.1f}%"
        )
        report_parts.append("")

        # Dimension analysis
        report_parts.append("DIMENSION ANALYSIS")
        report_parts.append("-" * 20)

        if analysis["strongest_dimensions"]:
            report_parts.append("Strongest Dimensions:")
            for dim, score in analysis["strongest_dimensions"]:
                report_parts.append(f"  ✓ {dim}: {score:.1f}/100")

        if analysis["weakest_dimensions"]:
            report_parts.append("Weakest Dimensions:")
            for dim, score in analysis["weakest_dimensions"]:
                report_parts.append(f"  ✗ {dim}: {score:.1f}/100")
        report_parts.append("")

        # Decision factors
        report_parts.append("DECISION ANALYSIS")
        report_parts.append("-" * 20)

        if evaluation.acceptance_factors:
            report_parts.append("Acceptance Factors:")
            for factor in evaluation.acceptance_factors:
                report_parts.append(f"  + {factor}")

        if evaluation.rejection_factors:
            report_parts.append("Rejection Factors:")
            for factor in evaluation.rejection_factors:
                report_parts.append(f"  - {factor}")
        report_parts.append("")

        # Recommendations
        report_parts.append("RECOMMENDATIONS")
        report_parts.append("-" * 20)

        if evaluation.improvement_suggestions:
            report_parts.append("Improvements:")
            for suggestion in evaluation.improvement_suggestions:
                report_parts.append(f"  → {suggestion}")

        if evaluation.strategic_recommendations:
            report_parts.append("Strategic:")
            for rec in evaluation.strategic_recommendations:
                report_parts.append(f"  ⚡ {rec}")

        print(report_parts)
        return "\n".join(report_parts)


# class EvaluationExporter:
#     """Export evaluation results to different formats"""

#     @staticmethod
#     def to_dict(evaluation: UnifiedArgumentEvaluation) -> Dict[str, Any]:
#         """Convert evaluation to dictionary for JSON export"""
#         return {
#             "argument_text": evaluation.argument_text,
#             "topic": evaluation.topic,
#             "stance": evaluation.stance,
#             "final_result": evaluation.final_result.value,
#             "overall_score": evaluation.overall_score,
#             "evaluators_used": evaluation.evaluators_used,
#             "individual_scores": [
#                 {
#                     "evaluator": score.evaluator_name,
#                     "dimension": score.dimension,
#                     "score": score.score,
#                     "raw_score": score.raw_score,
#                     "justification": score.justification,
#                     "confidence": score.confidence,
#                 }
#                 for score in evaluation.individual_scores
#             ],
#             "feedback": {
#                 "strengths": evaluation.strengths,
#                 "weaknesses": evaluation.weaknesses,
#                 "improvements": evaluation.improvement_suggestions,
#                 "strategic": evaluation.strategic_recommendations,
#             },
#             "decision_factors": {
#                 "acceptance": evaluation.acceptance_factors,
#                 "rejection": evaluation.rejection_factors,
#             },
#             "metadata": {
#                 "timestamp": evaluation.evaluation_timestamp.isoformat(),
#                 "summary": evaluation.evaluation_summary,
#             },
#         }

#     @staticmethod
#     def to_csv_row(evaluation: UnifiedArgumentEvaluation) -> List[str]:
#         """Convert evaluation to CSV row format"""
#         return [
#             (
#                 evaluation.argument_text[:100] + "..."
#                 if len(evaluation.argument_text) > 100
#                 else evaluation.argument_text
#             ),
#             evaluation.topic,
#             evaluation.stance,
#             evaluation.final_result.value,
#             str(evaluation.overall_score),
#             ";".join(evaluation.evaluators_used),
#             str(len(evaluation.acceptance_factors)),
#             str(len(evaluation.rejection_factors)),
#             ";".join(evaluation.strengths[:3]),
#             ";".join(evaluation.improvement_suggestions[:3]),
#             evaluation.evaluation_timestamp.isoformat(),
#         ]

#     @staticmethod
#     def get_csv_headers() -> List[str]:
#         """Get CSV headers for evaluation export"""
#         return [
#             "argument_text",
#             "topic",
#             "stance",
#             "result",
#             "overall_score",
#             "evaluators",
#             "acceptance_factors_count",
#             "rejection_factors_count",
#             "top_strengths",
#             "top_improvements",
#             "timestamp",
#         ]


# class BatchEvaluationRunner:
#     """Run evaluations on multiple arguments in batch"""

#     def __init__(
#         self, multi_evaluator: MultiEvaluatorRunner, config: EvaluationConfig = None
#     ):
#         self.multi_evaluator = multi_evaluator
#         self.config = config or EvaluationConfig()
#         self.results = []

#     async def evaluate_batch(
#         self, arguments: List[Argument], batch_params: Dict[str, Any] = None
#     ) -> List[UnifiedArgumentEvaluation]:
#         """Evaluate multiple arguments"""

#         batch_params = batch_params or {}
#         results = []

#         for i, argument in enumerate(arguments):
#             print(
#                 f"Evaluating argument {i+1}/{len(arguments)}: {argument.text[:50]}..."
#             )

#             try:
#                 evaluation = await self.multi_evaluator.evaluate_argument(
#                     argument, **batch_params
#                 )
#                 results.append(evaluation)

#                 print(
#                     f"  Result: {evaluation.final_result.value} ({evaluation.overall_score:.1f})"
#                 )

#             except Exception as e:
#                 print(f"  Error: {str(e)}")
#                 if not self.config.continue_on_evaluator_error:
#                     raise

#         self.results = results
#         return results

#     def generate_batch_summary(self) -> str:
#         """Generate summary of batch evaluation results"""

#         if not self.results:
#             return "No evaluation results available"

#         # Count results by category
#         result_counts = {}
#         score_sum = 0

#         for result in self.results:
#             category = result.final_result.value
#             result_counts[category] = result_counts.get(category, 0) + 1
#             score_sum += result.overall_score

#         avg_score = score_sum / len(self.results)

#         summary_parts = []
#         summary_parts.append(f"BATCH EVALUATION SUMMARY")
#         summary_parts.append(f"Total Arguments: {len(self.results)}")
#         summary_parts.append(f"Average Score: {avg_score:.1f}/100")
#         summary_parts.append("")
#         summary_parts.append("Results Distribution:")

#         for category, count in result_counts.items():
#             percentage = (count / len(self.results)) * 100
#             summary_parts.append(f"  {category.upper()}: {count} ({percentage:.1f}%)")

#         return "\n".join(summary_parts)

#     # def export_results(self, format_type: str = "dict") -> Any:
#     #     """Export batch results in specified format"""

#     #     if format_type == "dict":
#     #         return [EvaluationExporter.to_dict(result) for result in self.results]
#     #     elif format_type == "csv":
#     #         csv_data = [EvaluationExporter.get_csv_headers()]
#     #         csv_data.extend(
#     #             [EvaluationExporter.to_csv_row(result) for result in self.results]
#     #         )
#     #         return csv_data
#     #     else:
#     #         raise ValueError(f"Unsupported format: {format_type}")


# Usage Example
async def example_usage():
    """
    Example of how to use the unified evaluation system.
    
    Note: This example is for demonstration purposes.
    In practice, use team-specific factories:
    - CoTEvaluatorFactory for CoT team members
    - GoDsAFEvaluatorFactory for GoDsAF team members
    """

    # Setup (you would have your actual instances)
    llm = gpt_4o_mini
    godsaf_service = GoDsAFService()  # Assume properly configured

    # Create multi-evaluator using team-specific factory
    from src.team_extended.godsaf_team_member.evaluator import GoDsAFEvaluatorFactory
    
    config = EvaluationConfig()
    multi_evaluator = GoDsAFEvaluatorFactory.create_multi_evaluator(
        llm=llm,
        godsaf_service=godsaf_service,
        config=config,
    )

    # Test argument
    test_argument = Argument(
        text="""Climate change poses an existential threat to humanity. Scientific consensus 
                shows global temperatures have risen 1.1°C since pre-industrial times, with 
                catastrophic effects including rising sea levels, extreme weather, and ecosystem 
                collapse. Immediate action through carbon taxation and renewable energy investment 
                is essential to prevent irreversible damage.""",
        topic="climate change policy",
        team_type="pro",
        team_perspective="Environmental advocacy",
        viewpoint_orientation="supporting",
    )

    # Evaluation parameters (for GoDsAF)
    eval_params = {
        "team_name": "environmental_advocates",
        "strategy_recommendation": None,  # Would come from team context in real use
        "existing_argument_names": ["climate_science_consensus", "economic_transition"],
        "candidate_id": "example_candidate_1",
    }

    print("Running unified argument evaluation...")
    print("=" * 60)

    try:
        # Run evaluation
        evaluation = multi_evaluator.evaluate_argument(
            test_argument, **eval_params
        )

        # Display basic results
        print(f"Final Result: {evaluation.final_result.value}")
        print(f"Overall Score: {evaluation.overall_score:.1f}/100")
        print(f"Evaluators Used: {', '.join(evaluation.evaluators_used)}")
        print()

        # Show decision factors
        print("DECISION ANALYSIS:")
        print("Acceptance Factors:")
        for factor in evaluation.acceptance_factors:
            print(f"  ✓ {factor}")
        print("Rejection Factors:")
        for factor in evaluation.rejection_factors:
            print(f"  ✗ {factor}")
        print()

        # Show feedback
        print("FEEDBACK:")
        if evaluation.strengths:
            print("Strengths:")
            for strength in evaluation.strengths[:3]:
                print(f"  + {strength}")

        if evaluation.improvement_suggestions:
            print("Improvements:")
            for suggestion in evaluation.improvement_suggestions[:3]:
                print(f"  → {suggestion}")
        print()

        # Generate detailed analysis
        analysis = EvaluationAnalyzer.analyze_dimension_patterns(evaluation)
        print("DIMENSION ANALYSIS:")
        print(f"Evaluator Agreement: {analysis['evaluator_agreement']:.1f}%")

        if analysis["strongest_dimensions"]:
            print("Strongest Areas:")
            for dim, score in analysis["strongest_dimensions"]:
                print(f"  ✓ {dim}: {score:.1f}/100")

        if analysis["weakest_dimensions"]:
            print("Weakest Areas:")
            for dim, score in analysis["weakest_dimensions"]:
                print(f"  ✗ {dim}: {score:.1f}/100")

        # print("FULL ANALYSIS:")
        # report = EvaluationAnalyzer.generate_detailed_report(evaluation)
        # print(report)

        return evaluation

    except Exception as e:
        print(f"Evaluation failed: {str(e)}")
        return None


# async def batch_evaluation_example():
#     """Example of batch evaluation with multiple arguments"""

#     from agents.hub import gpt_4o_mini
#     from agents.reasoning.godsaf.godsaf_service import GoDsAFService

#     # Setup
#     llm = gpt_4o_mini
#     godsaf_service = GoDsAFService()

#     # Create batch evaluator
#     multi_evaluator = EvaluatorFactory.create_multi_evaluator(llm, godsaf_service)
#     batch_runner = BatchEvaluationRunner(
#         multi_evaluator, EvaluationConfig.conservative()
#     )

#     # Test arguments of varying quality
#     test_arguments = [
#         Argument(
#             text="""Comprehensive studies from WHO show that secondhand smoke causes 1.2 million
#                     deaths annually. Restaurant workers exposed to smoke have 50% higher lung disease
#                     rates. Public smoking bans protect non-smokers while preserving smokers' private
#                     rights, reducing heart attacks by 15% in implementing cities.""",
#             topic="smoking bans",
#             stance="support",
#         ),
#         Argument(
#             text="""Smoking in restaurants bothers people and smells bad. We should ban it
#                     because it's not fair to non-smokers who want to eat.""",
#             topic="smoking bans",
#             stance="support",
#         ),
#         Argument(
#             text="""Ban all smoking everywhere because I hate it and smokers are selfish!""",
#             topic="smoking bans",
#             stance="support",
#         ),
#     ]

#     print("BATCH EVALUATION EXAMPLE")
#     print("=" * 40)

#     # Run batch evaluation
#     results = await batch_runner.evaluate_batch(
#         test_arguments, batch_params={"team_name": "health_advocates"}
#     )

#     # Show batch summary
#     print("\n" + batch_runner.generate_batch_summary())

#     # Show detailed results for each argument
#     print("\nDETAILED RESULTS:")
#     print("-" * 30)

#     for i, result in enumerate(results):
#         print(
#             f"\nArgument {i+1}: {result.final_result.value.upper()} ({result.overall_score:.1f})"
#         )
#         print(f"Text: {result.argument_text[:60]}...")

#         if result.acceptance_factors:
#             print(f"Key Strength: {result.acceptance_factors[0]}")
#         if result.improvement_suggestions:
#             print(f"Main Improvement: {result.improvement_suggestions[0]}")

#     # Export results
#     export_data = batch_runner.export_results("dict")
#     print(f"\nExported {len(export_data)} evaluations to dictionary format")

#     return results


# async def comprehensive_example():
#     """Comprehensive example showing all features"""

#     print("COMPREHENSIVE EVALUATION SYSTEM DEMO")
#     print("=" * 50)

#     # Single argument evaluation
#     print("\n1. SINGLE ARGUMENT EVALUATION")
#     print("-" * 30)
#     evaluation = await example_usage()

#     if evaluation:
#         # Generate detailed report
#         detailed_report = EvaluationAnalyzer.generate_detailed_report(evaluation)
#         print(f"\nDetailed report generated ({len(detailed_report)} characters)")

#         # Export to dictionary
#         export_dict = EvaluationExporter.to_dict(evaluation)
#         print(f"Exported to dict with {len(export_dict)} fields")

#     # Batch evaluation
#     print("\n\n2. BATCH EVALUATION")
#     print("-" * 30)
#     batch_results = await batch_evaluation_example()

#     # Configuration comparison
#     print("\n\n3. CONFIGURATION COMPARISON")
#     print("-" * 30)

#     configs = {
#         "Conservative": EvaluationConfig.conservative(),
#         "Standard": EvaluationConfig(),
#         "Experimental": EvaluationConfig.experimental(),
#     }

#     for name, config in configs.items():
#         print(
#             f"{name}: Quality weight={config.quality_evaluator_weight}, "
#             f"GoDsAF weight={config.godsaf_evaluator_weight}"
#         )

#     print("\nDemo completed successfully!")
#     return evaluation, batch_results


if __name__ == "__main__":
    result = asyncio.run(example_usage())
    if result:
        print("\nSingle evaluation completed successfully!")
