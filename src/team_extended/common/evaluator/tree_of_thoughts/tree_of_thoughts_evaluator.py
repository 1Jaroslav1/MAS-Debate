"""
Tree of Thoughts Evaluator

Combines fast heuristic scoring with deep evaluation for ToT architecture.
Provides both quick scoring for pruning and comprehensive evaluation for final selection.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel

from src.team_extended.common.evaluator.evaluator_interface import ArgumentEvaluatorInterface
from src.team_extended.common.evaluator.model import Argument, EvaluationScore
from src.team_extended.common.evaluator.tree_of_thoughts.branch_scorer import BranchScorer
from src.team_extended.common.evaluator.chain_of_thought_evaluator import ChainOfThoughtEvaluatorAdapter

logger = logging.getLogger(__name__)


class TreeOfThoughtsEvaluator(ArgumentEvaluatorInterface):
    """
    Tree of Thoughts evaluator that provides:
    1. Fast heuristic scoring for branch pruning
    2. Deep evaluation using CoT-style analysis for final branches
    """

    def __init__(
        self,
        llm: BaseChatModel,
        weight: float = 0.7,
        enable_fast_scoring: bool = True,
        use_llm_for_quick_score: bool = False,
        godsaf_service = None
    ):
        """
        Initialize ToT evaluator

        Args:
            llm: Language model for evaluation
            weight: Weight of this evaluator in multi-evaluator setup
            enable_fast_scoring: Whether to use fast scoring (for pruning)
            use_llm_for_quick_score: Whether to use LLM for quick scoring (slower but better)
            godsaf_service: Optional GoDsAF service for argument storage
        """
        super().__init__(evaluator_name="TreeOfThoughts", weight=weight)
        self.llm = llm
        self.enable_fast_scoring = enable_fast_scoring
        self.use_llm_for_quick_score = use_llm_for_quick_score

        # Fast scorer for pruning
        self.branch_scorer = BranchScorer(llm)

        # Deep evaluator (uses CoT-style evaluation adapter)
        self.deep_evaluator = ChainOfThoughtEvaluatorAdapter(llm, weight=1.0, godsaf_service=godsaf_service)

    def evaluate(self, argument: Argument, **kwargs) -> Dict[str, Any]:
        """
        Perform full ToT evaluation

        This is used for final evaluation of selected arguments.
        Uses deep CoT-style evaluation.

        Args:
            argument: Argument to evaluate
            **kwargs: Additional context (team_name, member_profile, etc.)

        Returns:
            Evaluation result dictionary
        """
        logger.info(f"[ToT Evaluator] Deep evaluation of argument")

        # Use the deep CoT evaluator for comprehensive analysis
        result = self.deep_evaluator.evaluate(argument, **kwargs)

        # Add ToT-specific metadata
        if "metadata" not in result:
            result["metadata"] = {}
        result["metadata"]["evaluator_type"] = "tree_of_thoughts"
        result["metadata"]["used_deep_evaluation"] = True

        return result

    def quick_evaluate(
        self,
        argument: Argument,
        topic: str,
        team_name: str,
        domain_goal_pairs: List[tuple] = None
    ) -> float:
        """
        Perform quick heuristic evaluation for branch pruning

        Args:
            argument: Argument to evaluate
            topic: Debate topic
            team_name: Team name
            domain_goal_pairs: Target domain-goal pairs

        Returns:
            Quick score (0-100)
        """
        if not self.enable_fast_scoring:
            logger.warning("Fast scoring disabled, returning default score")
            return 50.0

        score = self.branch_scorer.quick_score(
            argument=argument,
            topic=topic,
            team_name=team_name,
            domain_goal_pairs=domain_goal_pairs,
            use_llm=self.use_llm_for_quick_score
        )

        logger.debug(f"[ToT Evaluator] Quick score: {score:.1f}")
        return score

    def batch_quick_evaluate(
        self,
        arguments: List[Argument],
        topic: str,
        team_name: str,
        domain_goal_pairs: List[tuple] = None
    ) -> List[float]:
        """
        Quick evaluate multiple arguments (for efficient batch pruning)

        Args:
            arguments: List of arguments
            topic: Debate topic
            team_name: Team name
            domain_goal_pairs: Target domain-goal pairs

        Returns:
            List of quick scores
        """
        return self.branch_scorer.batch_quick_score(
            arguments=arguments,
            topic=topic,
            team_name=team_name,
            domain_goal_pairs=domain_goal_pairs,
            use_llm=self.use_llm_for_quick_score
        )

    def compare_branches(
        self,
        argument1: Argument,
        argument2: Argument,
        topic: str,
        team_name: str
    ) -> Dict[str, Any]:
        """
        Compare two argument branches to determine which is better

        Args:
            argument1: First argument
            argument2: Second argument
            topic: Debate topic
            team_name: Team name

        Returns:
            Comparison result with winner and reasoning
        """
        score1 = self.quick_evaluate(argument1, topic, team_name)
        score2 = self.quick_evaluate(argument2, topic, team_name)

        winner = "argument1" if score1 > score2 else "argument2"
        margin = abs(score1 - score2)

        return {
            "winner": winner,
            "score1": score1,
            "score2": score2,
            "margin": margin,
            "is_close": margin < 10.0
        }
