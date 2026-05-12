import logging
from dataclasses import dataclass
from typing import Dict, List, Set

from src.reasoning.godsaf.godsaf_service import Domain, GoDsAFService, CandidateArgument, Goal
from src.reasoning.miner.argument_miner import (
    argument_parser_node,
)
from src.team_extended.common.evaluator.godsaf.model import ArgumentEvaluation
from src.team_extended.common.evaluator.model import EvaluationResult
from src.team_extended.common.team_member import StrategyRecommendation

logger = logging.getLogger(__name__)

@dataclass
class AttackRecommendation:
    """Represents a recommended attack relationship"""
    target_argument: str
    confidence: float
    reason: str
    strategic_value: float


class GoDsAFArgumentEvaluator:
    """
    Enhanced evaluator with automatic attack detection capabilities.
    """

    def __init__(self, godsaf_service: GoDsAFService):
        self.service = godsaf_service
        self.parser = argument_parser_node()
        
        # Evaluation thresholds
        self.thresholds = {
            EvaluationResult.EXCELLENT: 85,
            EvaluationResult.GOOD: 70,
            EvaluationResult.FAIR: 55,
            EvaluationResult.POOR: 40,
            EvaluationResult.REJECT: 0,
        }

    def evaluate_argument_with_attacks(
        self,
        strategy_recommendation: StrategyRecommendation,
        candidate_id: str = "current_candidate_id",
    ) -> ArgumentEvaluation:
        """
        Evaluate argument and store as candidate in service.
        
        Args:
            argument_text: Natural language argument to evaluate
            team_name: Team the argument belongs to
            topic: Debate topic for context
            strategy_recommendation: Pre-computed team strategy
            existing_argument_names: Names of existing arguments
            candidate_id: ID for storing candidate in service
            auto_detect_attacks: Whether to automatically detect attacks
            attack_confidence_threshold: Minimum confidence for including attacks
            
        Returns:
            ArgumentEvaluation with detailed scores and feedback
        """
        try:
            candidate: CandidateArgument = self.service.get_current_candidate_argument();

            godsaf_eval = self.service.evaluate_candidate_argument(candidate_id)
            alignment_scores = self._calculate_strategic_alignment(candidate, strategy_recommendation)

            ugn_coverage = self._assess_ugn_coverage(candidate, strategy_recommendation)

            evaluation = self._compile_evaluation(
                candidate,
                strategy_recommendation,
                godsaf_eval,
                alignment_scores,
                ugn_coverage
            )

            return evaluation

        except Exception as e:
            logger.error("GoDsAF Evaluator exception: ", e)
            # Return error evaluation
            return ArgumentEvaluation(
                result=EvaluationResult.REJECT,
                overall_score=0.0,
                strategic_alignment_score=0.0,
                ugn_coverage_score=0.0,
                domain_relevance_score=0.0,
                goal_effectiveness_score=0.0,
                estimated_aps=0.0,
                addresses_primary_ugn=False,
                addresses_secondary_ugn=False,
                strategic_gaps=["Argument parsing failed"],
                competitive_advantages=[],
                positive_feedback=[],
                improvement_suggestions=[f"Fix argument structure: {str(e)}"],
                strategic_recommendations=["Ensure argument follows proper format"],
                parsed_argument=None,
                ugn_analysis="Analysis failed due to parsing error",
                evaluation_summary=f"Evaluation failed: {str(e)}",
            )

    def _calculate_strategic_alignment(self, candidate: CandidateArgument, strategy_rec: StrategyRecommendation) -> Dict[str, float]:
        """Calculate how well the argument aligns with recommended strategy using domain-goal connections"""
        scores = {
            "domain_alignment": 0.0,
            "goal_alignment": 0.0,
            "connection_alignment": 0.0,
            "focus_precision": 0.0,
        }
        
        arg_domains = set(candidate.domains)
        arg_goals = set(candidate.goals.keys())
        
        # Get all UGNs (primary + secondary)
        all_ugns = strategy_rec.primary_ugns + strategy_rec.secondary_ugns
        
        if not all_ugns:
            # Fallback to legacy properties if no UGNs
            rec_domains = [domain.name for domain in strategy_rec.recommended_domains]
            rec_goals = [goal.name for goal in strategy_rec.recommended_goals]

            if rec_domains:
                domain_overlap = arg_domains.intersection(rec_domains)
                overlap_ratio = len(domain_overlap) / len(rec_domains)
                # FIX: Non-linear scaling for legacy fallback too
                scores["domain_alignment"] = (overlap_ratio ** 1.5) * 100
            else:
                # FIX: Lower fallback from 50 to 30
                scores["domain_alignment"] = 30.0

            if rec_goals:
                goal_overlap = arg_goals.intersection(rec_goals)
                overlap_ratio = len(goal_overlap) / len(rec_goals)
                # FIX: Non-linear scaling for legacy fallback too
                scores["goal_alignment"] = (overlap_ratio ** 1.5) * 100
            else:
                # FIX: Lower fallback from 50 to 30
                scores["goal_alignment"] = 30.0

            # FIX: Lower fallback from 50 to 25
            scores["connection_alignment"] = 25.0
        else:
            # Extract domains and goals from UGNs
            rec_domains = [ugn.domain.name for ugn in all_ugns]
            rec_goals = [ugn.goal.name for ugn in all_ugns]
            
            # Calculate domain alignment
            domain_overlap = arg_domains.intersection(rec_domains)
            if rec_domains:
                overlap_ratio = len(domain_overlap) / len(set(rec_domains))
                # FIX: Non-linear scaling (^1.5) to reward complete alignment more strongly
                scores["domain_alignment"] = (overlap_ratio ** 1.5) * 100
            else:
                # FIX: Lower fallback from 50 to 30 to penalize missing recommendations
                scores["domain_alignment"] = 30.0

            # Calculate goal alignment
            goal_overlap = arg_goals.intersection(rec_goals)
            if rec_goals:
                overlap_ratio = len(goal_overlap) / len(set(rec_goals))
                # FIX: Non-linear scaling (^1.5) to reward complete alignment more strongly
                scores["goal_alignment"] = (overlap_ratio ** 1.5) * 100
            else:
                # FIX: Lower fallback from 50 to 30 to penalize missing recommendations
                scores["goal_alignment"] = 30.0
            
            # Calculate connection alignment - how well the argument addresses specific domain-goal pairs
            connection_matches = 0
            total_connections = len(all_ugns)

            for ugn in all_ugns:
                if ugn.goal.name in candidate.goals and ugn.domain.name in candidate.goals[ugn.goal.name]:
                    connection_matches += 1

            # FIX: Lower fallback from 50 to 25 for connection alignment
            scores["connection_alignment"] = (connection_matches / total_connections) * 100 if total_connections > 0 else 25.0
        
        # Calculate focus precision
        total_elements = len(arg_domains) + len(arg_goals)
        optimal_elements = len(set(rec_domains)) + len(set(rec_goals))
        
        if optimal_elements > 0:
            if total_elements <= optimal_elements:
                scores["focus_precision"] = 100.0
            else:
                # FIX: Stronger penalty (30 instead of 20) for unfocused arguments
                scores["focus_precision"] = max(0, 100 - (total_elements - optimal_elements) * 30)
        else:
            # FIX: Lower fallback from 70 to 50
            scores["focus_precision"] = 50.0
        
        return scores

    def _assess_ugn_coverage(self, candidate: CandidateArgument, strategy_rec: StrategyRecommendation) -> Dict[str, any]:
        """Assess how well the argument addresses UGN priorities"""
        coverage = {
            "addresses_primary": False,
            "addresses_secondary": False,
            "primary_coverage_strength": 0.0,
            "secondary_coverage_strength": 0.0,
        }

        for ugn in strategy_rec.primary_ugns:
            if ugn.goal.name in candidate.goals and ugn.domain.name in candidate.goals[ugn.goal.name]:
                coverage["addresses_primary"] = True
                # FIX: Use proportional coverage (1.2x instead of 2x) to reduce score inflation
                coverage["primary_coverage_strength"] = min(100.0, ugn.value * 1.2)
                break

        for ugn in strategy_rec.secondary_ugns:
            if ugn.goal.name in candidate.goals and ugn.domain.name in candidate.goals[ugn.goal.name]:
                coverage["addresses_secondary"] = True
                # FIX: Use proportional coverage (1.2x instead of 2x) to reduce score inflation
                coverage["secondary_coverage_strength"] = min(100.0, ugn.value * 1.2)
                break

        return coverage

    def _compile_evaluation(
        self,
        candidate: CandidateArgument,
        strategy_rec: StrategyRecommendation,
        godsaf_eval: Dict,
        alignment_scores: Dict[str, float],
        ugn_coverage: Dict[str, any]
    ) -> ArgumentEvaluation:
        """Compile all evaluation components into final assessment"""
        
        # FIX: Adjusted weights - reduced connection, increased focus precision
        strategic_alignment_score = (
            alignment_scores["domain_alignment"] * 0.3
            + alignment_scores["goal_alignment"] * 0.3
            + alignment_scores["connection_alignment"] * 0.2  # Reduced from 0.3
            + alignment_scores["focus_precision"] * 0.2      # Increased from 0.1
        )
        
        ugn_coverage_score = (ugn_coverage["primary_coverage_strength"] * 0.7) + (
            ugn_coverage["secondary_coverage_strength"] * 0.3
        )
        
        # FIX: Keep these for backward compatibility in return value
        domain_relevance_score = alignment_scores["domain_alignment"]
        goal_effectiveness_score = alignment_scores["goal_alignment"]

        estimated_aps = godsaf_eval.get("estimated_aps", 0)
        # FIX: Boost APS impact (2x multiplier) since it's a critical ASP solver metric
        aps_normalized = min(100.0, estimated_aps * 2)

        # FIX: Simplified overall score calculation - removed redundant components
        # Old formula double-counted domain/goal alignment through strategic_alignment AND separate scores
        # New formula: strategic (35%) + ugn_coverage (40%) + aps (25%)
        overall_score = (
            strategic_alignment_score * 0.35  # Increased from 0.15 (absorbed redundant 0.15+0.15)
            + ugn_coverage_score * 0.40       # Unchanged - most important metric
            + aps_normalized * 0.25           # Increased from 0.10 - critical for argument strength
        )
        
        result = self._determine_result_category(overall_score)
        feedback = self._generate_feedback(candidate, alignment_scores, ugn_coverage, godsaf_eval)
        
        return ArgumentEvaluation(
            result=result,
            overall_score=overall_score,
            strategic_alignment_score=strategic_alignment_score,
            ugn_coverage_score=ugn_coverage_score,
            domain_relevance_score=domain_relevance_score,
            goal_effectiveness_score=goal_effectiveness_score,
            estimated_aps=estimated_aps,
            addresses_primary_ugn=ugn_coverage["addresses_primary"],
            addresses_secondary_ugn=ugn_coverage["addresses_secondary"],
            strategic_gaps=feedback["gaps"],
            competitive_advantages=feedback["advantages"],
            positive_feedback=feedback["positive"],
            improvement_suggestions=feedback["improvements"],
            strategic_recommendations=feedback["strategic"],
            parsed_argument=candidate,
            ugn_analysis=self._generate_ugn_analysis(strategy_rec, ugn_coverage),
            evaluation_summary=self._generate_summary(result, overall_score, feedback),
        )

    def _determine_result_category(self, score: float) -> EvaluationResult:
        """Determine evaluation result category based on score"""
        for result, threshold in self.thresholds.items():
            if score >= threshold:
                return result
        return EvaluationResult.REJECT

    def _generate_feedback(
        self,
        candidate: CandidateArgument,
        alignment_scores: Dict[str, float],
        ugn_coverage: Dict[str, any],
        godsaf_eval: Dict,
    ) -> Dict[str, List[str]]:
        """Generate detailed feedback including attack recommendations"""
        
        feedback = {
            "positive": [],
            "improvements": [],
            "strategic": [],
            "gaps": [],
            "advantages": [],
        }
        
        attack_recommendations = candidate.attacks
        if attack_recommendations:
            high_confidence_attacks = [
                rec for rec in attack_recommendations if rec.confidence >= 0.7
            ]
            if high_confidence_attacks:
                targets = [rec.target_argument for rec in high_confidence_attacks]
                feedback["advantages"].append(
                    f"Strong attack opportunities against: {', '.join(targets)}"
                )
            
            medium_confidence_attacks = [
                rec for rec in attack_recommendations 
                if 0.4 <= rec.confidence < 0.7
            ]
            if medium_confidence_attacks:
                targets = [rec.target_argument for rec in medium_confidence_attacks]
                feedback["strategic"].append(
                    f"Consider attacking: {', '.join(targets)}"
                )
        
        # Rest of the original feedback generation logic...
        if alignment_scores["domain_alignment"] > 80:
            feedback["positive"].append("Excellent domain alignment with strategic priorities")
        if alignment_scores["goal_alignment"] > 80:
            feedback["positive"].append("Strong goal alignment with team needs")
        if ugn_coverage["addresses_primary"]:
            feedback["positive"].append("Addresses primary unmet goal need")
        if godsaf_eval.get("estimated_aps", 0) > 50:
            feedback["positive"].append("High estimated argument strength (APS)")
        
        return feedback

    def _generate_ugn_analysis(self, strategy_rec: StrategyRecommendation, ugn_coverage: Dict[str, any]) -> str:
        """Generate UGN analysis summary"""
        analysis_parts = ["UGN Coverage Analysis:"]
        
        if strategy_rec.primary_ugns:
            for ugn in strategy_rec.primary_ugns:
                status = "✓ ADDRESSED" if ugn_coverage["addresses_primary"] else "✗ NOT ADDRESSED"
                analysis_parts.append(f"  Primary: {ugn.goal} in {ugn.domain} (UGN: {ugn.value}) - {status}")
        
        if strategy_rec.secondary_ugns:
            for ugn in strategy_rec.secondary_ugns:
                status = "✓ ADDRESSED" if ugn_coverage["addresses_secondary"] else "✗ NOT ADDRESSED"
                analysis_parts.append(f"  Secondary: {ugn.goal} in {ugn.domain} (UGN: {ugn.value}) - {status}")
        
        coverage_strength = ugn_coverage["primary_coverage_strength"]
        analysis_parts.append(f"  Coverage Strength: {coverage_strength:.1f}%")
        
        return "\n".join(analysis_parts)

    def _generate_summary(self, result: EvaluationResult, score: float, feedback: Dict[str, List[str]]) -> str:
        """Generate evaluation summary"""
        summary_parts = [f"Evaluation Result: {result.value.upper()} ({score:.1f}/100)", ""]
        
        if feedback["positive"]:
            summary_parts.append("Strengths:")
            for strength in feedback["positive"]:
                summary_parts.append(f"  + {strength}")
            summary_parts.append("")
        
        if feedback["improvements"]:
            summary_parts.append("Areas for Improvement:")
            for improvement in feedback["improvements"]:
                summary_parts.append(f"  - {improvement}")
            summary_parts.append("")
        
        if feedback["strategic"]:
            summary_parts.append("Strategic Recommendations:")
            for rec in feedback["strategic"]:
                summary_parts.append(f"  → {rec}")
        
        return "\n".join(summary_parts)

