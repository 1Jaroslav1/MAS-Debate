"""
Fast Heuristic Branch Scorer for Tree of Thoughts

Provides lightweight scoring for quick branch evaluation and pruning,
before deep evaluation is performed on surviving branches.
"""

import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.language_models.chat_models import BaseChatModel

from src.team_extended.common.evaluator.model import Argument

logger = logging.getLogger(__name__)


class QuickScoreOutput(BaseModel):
    """Structured output for quick scoring"""
    alignment_score: int = Field(description="Domain-goal alignment score (0-100)", ge=0, le=100)
    evidence_score: int = Field(description="Evidence presence and quality score (0-100)", ge=0, le=100)
    structure_score: int = Field(description="Argument structure and completeness score (0-100)", ge=0, le=100)
    relevance_score: int = Field(description="Topic relevance score (0-100)", ge=0, le=100)
    overall_score: int = Field(description="Overall quick score (0-100)", ge=0, le=100)
    brief_rationale: str = Field(description="Brief 1-sentence rationale for the score")


class BranchScorer:
    """
    Fast heuristic scorer for quick branch evaluation.

    Uses lightweight LLM calls or rule-based scoring to quickly assess
    argument quality before deep evaluation.
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def quick_score(
        self,
        argument: Argument,
        topic: str,
        team_name: str,
        domain_goal_pairs: List[tuple] = None,
        use_llm: bool = True
    ) -> float:
        """
        Perform quick scoring of an argument

        Args:
            argument: The argument to score
            topic: The debate topic
            team_name: The team name
            domain_goal_pairs: Optional list of target domain-goal pairs
            use_llm: If True, use LLM for scoring; if False, use rule-based

        Returns:
            Score between 0.0 and 100.0
        """
        if use_llm:
            return self._quick_score_llm(argument, topic, team_name, domain_goal_pairs)
        else:
            return self._quick_score_rule_based(argument, topic, domain_goal_pairs)

    def _quick_score_llm(
        self,
        argument: Argument,
        topic: str,
        team_name: str,
        domain_goal_pairs: List[tuple] = None
    ) -> float:
        """Use LLM for quick scoring with structured output"""

        domain_goal_text = ""
        if domain_goal_pairs:
            pairs_text = ", ".join([f"{d}+{g}" for d, g in domain_goal_pairs])
            domain_goal_text = f"\nTarget domain-goal pairs: {pairs_text}"

        prompt = f"""
You are a quick argument evaluator. Rapidly assess this argument's quality.

CONTEXT:
- Topic: {topic}
- Team: {team_name}{domain_goal_text}

ARGUMENT TEXT:
{argument.text}

INSTRUCTIONS:
Quickly evaluate the argument on these dimensions (0-100 each):
1. Alignment: Does it address relevant domains and goals?
2. Evidence: Does it contain evidence and support?
3. Structure: Is it well-structured and complete?
4. Relevance: Is it on-topic and coherent?

Provide scores and a brief overall assessment. Be quick but fair.
"""

        try:
            result = self.llm.with_structured_output(QuickScoreOutput, include_raw=True).invoke(prompt)
            output = result["parsed"]

            logger.debug(
                f"Quick LLM score: {output.overall_score} "
                f"(align={output.alignment_score}, evid={output.evidence_score}, "
                f"struct={output.structure_score}, relev={output.relevance_score})"
            )

            return float(output.overall_score)

        except Exception as e:
            logger.warning(f"LLM quick scoring failed: {e}, falling back to rule-based")
            return self._quick_score_rule_based(argument, topic, domain_goal_pairs)

    def _quick_score_rule_based(
        self,
        argument: Argument,
        topic: str,
        domain_goal_pairs: List[tuple] = None
    ) -> float:
        """Rule-based quick scoring without LLM"""

        text = argument.text.lower()
        scores = []

        # 1. Length and completeness heuristic (20 points)
        word_count = len(argument.text.split())
        if word_count < 50:
            length_score = 10
        elif word_count < 150:
            length_score = 15
        elif word_count < 300:
            length_score = 20
        else:
            length_score = 18  # Too long might be unfocused

        scores.append(length_score)

        # 2. Evidence keywords (20 points)
        evidence_keywords = [
            'study', 'research', 'data', 'evidence', 'statistics',
            'according to', 'shows that', 'demonstrates', 'indicates',
            'found that', 'reported', 'published', 'survey', 'analysis'
        ]
        evidence_count = sum(1 for kw in evidence_keywords if kw in text)
        evidence_score = min(20, evidence_count * 3)
        scores.append(evidence_score)

        # 3. Structure keywords (20 points)
        structure_keywords = [
            'first', 'second', 'third', 'furthermore', 'moreover',
            'however', 'therefore', 'consequently', 'in conclusion',
            'additionally', 'finally', 'because', 'thus'
        ]
        structure_count = sum(1 for kw in structure_keywords if kw in text)
        structure_score = min(20, structure_count * 3)
        scores.append(structure_score)

        # 4. Topic relevance (20 points)
        topic_words = set(topic.lower().split())
        text_words = set(text.split())
        overlap = len(topic_words & text_words)
        relevance_score = min(20, overlap * 4)
        scores.append(relevance_score)

        # 5. Domain-goal alignment (20 points)
        alignment_score = 10  # Default
        if domain_goal_pairs:
            # Check if domain/goal IDs appear in text
            pair_mentions = 0
            for domain, goal in domain_goal_pairs:
                # Remove prefix and check
                domain_term = domain.replace('d_', '').replace('_', ' ')
                goal_term = goal.replace('g_', '').replace('_', ' ')
                if domain_term in text or goal_term in text:
                    pair_mentions += 1
            alignment_score = min(20, pair_mentions * 10)
        scores.append(alignment_score)

        total_score = sum(scores)

        logger.debug(
            f"Quick rule-based score: {total_score} "
            f"(len={length_score}, evid={evidence_score}, "
            f"struct={structure_score}, relev={relevance_score}, align={alignment_score})"
        )

        return float(total_score)

    def batch_quick_score(
        self,
        arguments: List[Argument],
        topic: str,
        team_name: str,
        domain_goal_pairs: List[tuple] = None,
        use_llm: bool = False  # Default to rule-based for batch
    ) -> List[float]:
        """
        Quick score multiple arguments

        Args:
            arguments: List of arguments to score
            topic: Debate topic
            team_name: Team name
            domain_goal_pairs: Target domain-goal pairs
            use_llm: Whether to use LLM (slower) or rule-based (faster)

        Returns:
            List of scores
        """
        scores = []
        for arg in arguments:
            score = self.quick_score(arg, topic, team_name, domain_goal_pairs, use_llm)
            scores.append(score)

        logger.info(f"Batch scored {len(arguments)} arguments: avg={sum(scores)/len(scores):.1f}")
        return scores
