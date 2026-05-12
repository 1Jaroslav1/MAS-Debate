"""
Multi-Agent Argumentation Quality Evaluator
Based on Wachsmuth et al. (2017) taxonomy with 15 quality dimensions

Key Features:
- 15 specialized agents working in parallel (with configurable concurrency)
- One-shot prompting with high/low quality examples for each dimension
- Structured output with scores, justifications, and confidence levels
- Weighted aggregation based on empirical correlations
- Built-in rate limiting and retry logic for API constraints

Rate Limiting Features:
- Configurable maximum concurrent agents (default: 5)
- Automatic retry with exponential backoff for rate limit errors
- Batch processing with delays to avoid overwhelming APIs
- Configuration presets for different rate limit scenarios
- Sequential evaluation option for very strict limits

One-Shot Learning Benefits:
- Each agent sees concrete examples of high (score 3) and low (score 1) quality
- Examples are tailored to each specific dimension's focus
- Improves consistency and reduces evaluation ambiguity
- Grounds abstract quality concepts in real argument instances

Usage:
    # For limited rate limits (e.g., GPT-4 with 10k TPM)
    evaluator = ArgumentQualityEvaluator(llm, **EvaluatorConfig.CONSERVATIVE)
    
    # For higher rate limits or GPT-3.5
    evaluator = ArgumentQualityEvaluator(llm, **EvaluatorConfig.AGGRESSIVE)
    
    # For sequential processing
    evaluator = SequentialArgumentEvaluator(llm, delay_between_calls=1.0)
"""

import asyncio
from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import logging

from src.team_extended.common.evaluator.mas_quality.quality_dimensions import (
    QUALITY_DIMENSIONS,
)
from src.team_extended.common.evaluator.mas_quality.model import (
    QualityScore,
    ArgumentEvaluation,
)
from src.team_extended.common.evaluator.model import Argument
from src.team_extended.common.evaluator.mas_quality.model import EvaluatorConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Data Models


# Quality Dimension Definitions with Examples (from Wachsmuth et al.)
# One-shot examples enable agents to:
# 1. Better understand what constitutes high vs low quality for each dimension
# 2. Maintain consistency across evaluations
# 3. Ground abstract definitions in concrete instances
# 4. Reduce ambiguity in subjective assessments


class QualityDimensionAgent:
    """Agent specialized in evaluating one quality dimension"""

    def __init__(self, dimension: str, llm, parser: PydanticOutputParser):
        self.dimension = dimension
        self.llm = llm
        self.parser = parser
        self.definition = QUALITY_DIMENSIONS[dimension]

        # Create dimension-specific prompt with examples
        self.prompt = PromptTemplate(
            template="""
                You are an expert in argumentation quality assessment, specialized in evaluating {dimension}.
                Definition: {definition}
                Focus: {focus}

                SCORING GUIDE:
                {scoring_guide}

                EXAMPLES:

                High Quality (Score 3):
                {high_example}

                Medium Quality (Score 2):
                {medium_example}

                Low Quality (Score 1):
                {low_example}

                Now evaluate this argument with team context awareness:
                
                ARGUMENT DETAILS:
                Topic: {topic}
                Team Type: {team_type}
                Team Perspective: {team_perspective}
                Viewpoint Orientation: {viewpoint_orientation}

                ARGUMENT TEXT:
                {argument_text}

                EVALUATION INSTRUCTIONS:
                Consider how this argument serves the {team_type} perspective and {viewpoint_orientation} orientation.
                Evaluate {dimension} while considering:
                - How well the argument represents the {team_type} viewpoint
                - Whether the {viewpoint_orientation} approach is appropriate for this dimension
                - How the team's priorities and concerns are addressed
                - The effectiveness for the intended {team_type} audience

                Compare this argument to the examples provided, but adjust your assessment based on:
                - Team context appropriateness
                - Perspective alignment effectiveness
                - Audience-specific persuasiveness

                {format_instructions}

                Provide your assessment:
            """,
            input_variables=[
                "dimension",
                "definition",
                "focus",
                "scoring_guide",
                "high_example",
                "medium_example",
                "low_example",
                "topic",
                "team_type",
                "team_perspective",
                "viewpoint_orientation",
                "argument_text",
            ],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

    async def evaluate(self, argument: Argument) -> QualityScore:
        """Evaluate the argument on this specific dimension"""

        # Get examples if available
        examples = self.definition.get("examples", {})
        high_example = examples.get("high", "No example available")
        medium_example = examples.get("medium", "No example available")
        low_example = examples.get("low", "No example available")
        scoring_guide = self.definition.get(
            "scoring_guide",
            "Score based on how well the argument meets the dimension criteria.",
        )

        # Prepare input
        eval_input = {
            "dimension": self.dimension,
            "definition": self.definition["definition"],
            "focus": self.definition.get("focus", "general quality"),
            "scoring_guide": scoring_guide,
            "high_example": high_example,
            "medium_example": medium_example,
            "low_example": low_example,
            "topic": argument.topic,
            "team_type": argument.team_type,
            "team_perspective": argument.team_perspective,
            "viewpoint_orientation": argument.viewpoint_orientation,
            "argument_text": argument.text,
        }

        # Run evaluation
        chain = self.prompt | self.llm | self.parser
        result = await chain.ainvoke(eval_input)

        # Ensure dimension is set correctly
        result.dimension = self.dimension

        return result


class ArgumentQualityEvaluator:
    """Orchestrates multiple agents to evaluate argument quality"""

    def __init__(self, llm, max_concurrent_agents=5, retry_attempts=3, batch_delay=1.0):
        """
        Initialize evaluator with rate limiting capabilities

        Args:
            llm: Language model to use
            max_concurrent_agents: Maximum number of agents to run concurrently
            retry_attempts: Number of retry attempts for rate limit errors
            batch_delay: Delay between batches in seconds
        """
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=QualityScore)
        self.max_concurrent_agents = max_concurrent_agents
        self.retry_attempts = retry_attempts
        self.batch_delay = batch_delay

        # Semaphore to limit concurrent API calls
        self.semaphore = asyncio.Semaphore(max_concurrent_agents)

        # Create agents for each dimension
        self.agents = {}
        for dimension in QUALITY_DIMENSIONS.keys():
            self.agents[dimension] = QualityDimensionAgent(dimension, llm, self.parser)

        # Aggregation weights based on Wachsmuth et al. correlations
        self.aggregation_weights = {
            "cogency": 0.15,
            "local_acceptability": 0.08,
            "local_relevance": 0.08,
            "local_sufficiency": 0.08,
            "effectiveness": 0.15,
            "credibility": 0.06,
            "emotional_appeal": 0.04,
            "clarity": 0.06,
            "appropriateness": 0.05,
            "arrangement": 0.05,
            "reasonableness": 0.15,
            "global_acceptability": 0.08,
            "global_relevance": 0.08,
            "global_sufficiency": 0.07,
            "overall_quality": 0.0,  # Not used in aggregation
        }

    async def evaluate_with_retry(
        self, agent: QualityDimensionAgent, argument: Argument
    ) -> QualityScore:
        """Evaluate with retry logic for rate limiting"""
        for attempt in range(self.retry_attempts):
            try:
                async with self.semaphore:  # Limit concurrent calls
                    return await agent.evaluate(argument)
            except Exception as e:
                if "rate_limit_exceeded" in str(e) or "429" in str(e):
                    if attempt < self.retry_attempts - 1:
                        # Exponential backoff with jitter
                        wait_time = (2**attempt) + (0.1 * (attempt + 1))
                        logger.warning(
                            f"Rate limit hit for {agent.dimension}. Waiting {wait_time:.1f}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max retries reached for {agent.dimension}")
                        # Return a default score on final failure
                        return QualityScore(
                            dimension=agent.dimension,
                            score=2,  # Default to medium
                            justification="Evaluation failed due to rate limiting",
                            confidence=0.0,
                        )
                else:
                    raise e

    async def evaluate_argument(
        self, argument: Argument, batch_mode=False
    ) -> ArgumentEvaluation:
        """
        Evaluate argument across all dimensions with rate limiting

        Args:
            argument: Argument to evaluate
            batch_mode: If True, applies additional delays for batch processing
        """
        # Split dimensions into batches
        dimensions_to_evaluate = [
            d for d in self.agents.keys() if d != "overall_quality"
        ]

        # Process in smaller batches if needed
        if len(dimensions_to_evaluate) > self.max_concurrent_agents:
            dimension_scores = []

            for i in range(0, len(dimensions_to_evaluate), self.max_concurrent_agents):
                batch = dimensions_to_evaluate[i : i + self.max_concurrent_agents]

                # Create tasks for this batch
                tasks = [
                    self.evaluate_with_retry(self.agents[dim], argument)
                    for dim in batch
                ]

                # Run batch
                batch_results = await asyncio.gather(*tasks)
                dimension_scores.extend(batch_results)

                # Add delay between batches if not the last batch
                if i + self.max_concurrent_agents < len(dimensions_to_evaluate):
                    if batch_mode:
                        await asyncio.sleep(self.batch_delay * 2)
                    else:
                        await asyncio.sleep(self.batch_delay)
        else:
            # Process all at once if under limit
            tasks = [
                self.evaluate_with_retry(self.agents[dim], argument)
                for dim in dimensions_to_evaluate
            ]
            dimension_scores = await asyncio.gather(*tasks)

        # Calculate aggregated overall quality
        weighted_sum = 0.0
        total_weight = 0.0

        for score in dimension_scores:
            weight = self.aggregation_weights.get(score.dimension, 0.0)
            weighted_sum += score.score * weight * score.confidence
            total_weight += weight * score.confidence

        overall_quality = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Get overall quality assessment from dedicated agent
        overall_agent = self.agents["overall_quality"]
        overall_assessment = await self.evaluate_with_retry(overall_agent, argument)

        # Combine assessments
        all_scores = dimension_scores + [overall_assessment]

        return ArgumentEvaluation(
            argument_text=argument.text,
            dimensions=all_scores,
            overall_quality=overall_quality,
        )

    def evaluate_batch(self, arguments: List[Argument]) -> List[ArgumentEvaluation]:
        """Evaluate multiple arguments with rate limiting"""

        async def run_batch():
            evaluations = []

            # Process arguments one at a time to avoid overwhelming the API
            for i, arg in enumerate(arguments):
                logger.info(f"Evaluating argument {i+1}/{len(arguments)}")
                eval_result = await self.evaluate_argument(arg, batch_mode=True)
                evaluations.append(eval_result)

                # Add delay between arguments in batch
                if i < len(arguments) - 1:
                    await asyncio.sleep(self.batch_delay)

            return evaluations

        # Run async evaluations
        return asyncio.run(run_batch())
