"""
Tree of Thoughts Argument Creator Node

Creates multiple argument variations for each analysis branch.
Uses different rhetorical strategies to generate diverse arguments.
"""

import logging
import time
import uuid
from typing import List, Dict, Any
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from src.team_extended.common.knowledge.argument_creation_knowledge_retrieval import ArgumentCreationKnowledgeRetriever
from src.team_extended.common.argument_creator.model import ArgumentCreatorState
from src.team_extended.common.argument_creator.argument_creation_workflow import create_argument_creator_workflow
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.metrics.execution_metrics import MetricsCollector
from src.team_extended.common.metrics.token_tracking import create_node_tracker, WorkflowNode

logger = logging.getLogger(__name__)


class ArgumentVariation(BaseModel):
    """A single argument variation with metadata"""
    variation_id: str = Field(description="Unique ID for this variation")
    strategy: str = Field(description="Rhetorical strategy used (e.g., 'evidence-heavy', 'emotional', 'logical')")
    argument_text: str = Field(description="The generated argument text")
    branch_id: str = Field(description="Parent analysis branch ID")


def argument_creator_node(state: TeamMemberState) -> TeamMemberState:
    """
    Create multiple argument variations for ToT architecture.

    For each analysis branch, generates multiple argument variations
    using different rhetorical strategies.
    """
    member_name = state["team_member_name"]
    team_name = state["team_name"]
    round_num = state.get("round", 0)

    logger.info(f"[ToT ARGUMENT CREATOR NODE] Starting for member: {member_name}")

    # Get ToT configuration (with defaults)
    tot_config = state.get("tot_config") or {}
    num_variations = tot_config.get("num_argument_variations", 3)

    # Get analysis branches from analyser
    analysis_branches = state.get("tot_analysis_branches", [])

    if not analysis_branches:
        logger.warning("No analysis branches found, falling back to default behavior")
        return _create_single_argument(state)

    token_tracker = create_node_tracker(WorkflowNode.ARGUMENT_CREATOR)

    # Configuration
    use_personalization = state["argument_creation_context"].member_profile.use_personalization
    use_context_analysis = state["argument_creation_context"].member_profile.use_context_analysis

    logger.info(f"[ToT ARGUMENT CREATOR] Generating {num_variations} variations per branch for {len(analysis_branches)} branches")

    # Create knowledge retriever
    knowledge_retriever = ArgumentCreationKnowledgeRetriever(
        llm=state["argument_creation_llm"],
        vector_db=state["vector_db"],
        tavily_tool=state["tavily_tool"],
        store=state["store"],
        use_personalization=use_personalization,
    )

    def retrieve_knowledge_node(arg_state: ArgumentCreatorState, config: RunnableConfig) -> ArgumentCreatorState:
        return knowledge_retriever.retrieve_knowledge_for_argument(arg_state, config)

    # Create workflow
    workflow = create_argument_creator_workflow(
        llm=state["argument_creation_llm"],
        retrieve_knowledge_node=retrieve_knowledge_node,
        knowledge_node_config=state.get("knowledge_node_config"),
        use_personalization=use_personalization,
        use_context_analysis=use_context_analysis,
        token_tracker=token_tracker,
    )

    # Store all argument variations
    all_variations: List[Dict[str, Any]] = []

    # Define rhetorical strategies for variations
    strategies = [
        {
            "name": "evidence-heavy",
            "instruction": "Focus heavily on empirical evidence, data, and research findings. Use concrete facts and statistics."
        },
        {
            "name": "emotional-appeal",
            "instruction": "Appeal to emotions and values. Use compelling narratives and relatable examples."
        },
        {
            "name": "logical-reasoning",
            "instruction": "Emphasize logical structure and deductive reasoning. Build a clear chain of argumentation."
        },
        {
            "name": "counter-focused",
            "instruction": "Focus on countering opponent arguments and exposing weaknesses in opposing views."
        },
        {
            "name": "balanced-comprehensive",
            "instruction": "Provide a balanced, comprehensive argument that combines evidence, logic, and persuasion."
        }
    ]

    # For each analysis branch, create argument variations
    for branch_idx, branch in enumerate(analysis_branches):
        branch_id = branch["branch_id"]
        strategy_name = branch["strategy_name"]
        domain_goal_pairs = branch["domain_goal_pairs"]

        logger.info(f"  Creating variations for branch: {strategy_name} ({len(domain_goal_pairs)} domain-goal pairs)")

        # Get domain and goal lists
        domains = [d for d, _ in domain_goal_pairs]
        goals = [g for _, g in domain_goal_pairs]

        # Get previous arguments
        try:
            previous_arguments = state["af"].get_argument_test_by_team(team_name, domains, goals)
        except:
            previous_arguments = []

        # Create variations with different rhetorical strategies
        variations_to_create = min(num_variations, len(strategies))

        for var_idx in range(variations_to_create):
            strategy = strategies[var_idx % len(strategies)]

            # Create variation-specific context
            context = state["argument_creation_context"]
            context.previous_arguments = previous_arguments
            context.domain_goal_connections = domain_goal_pairs
            context.iteration_count = state["iteration_number"]

            # Add strategy instruction to context
            context_with_strategy = f"{context.topic}\n\nRHETORICAL STRATEGY: {strategy['instruction']}"

            # Create initial state
            initial_state = ArgumentCreatorState(
                context=context,
                retrieved_knowledge=state.get("knowledge_retrival_results", {}).get("retrieved_documents", [])
            )

            # Override topic to include strategy
            initial_state.context.topic = context_with_strategy

            # Run workflow
            try:
                final_state = workflow.invoke(
                    initial_state,
                    state["argument_creation_config"]
                )

                variation_id = f"branch_{branch_idx}_var_{var_idx}"
                variation = {
                    "variation_id": variation_id,
                    "branch_id": branch_id,
                    "strategy": strategy["name"],
                    "strategy_name": strategy_name,  # From analysis branch
                    "argument_text": final_state["final_argument"],
                    "domain_goal_pairs": domain_goal_pairs,
                    "full_state": final_state
                }

                all_variations.append(variation)

                logger.info(f"    ✓ Created variation: {strategy['name']}")

            except Exception as e:
                logger.error(f"    ✗ Failed to create variation {strategy['name']}: {e}")
                continue

    # Store all variations in state
    state["tot_argument_variations"] = all_variations

    # For compatibility with downstream nodes, store the first variation as default
    if all_variations:
        default_variation = all_variations[0]
        state["argument_creator_results"] = default_variation["full_state"]

        logger.info(f"[ToT ARGUMENT CREATOR] Generated {len(all_variations)} total argument variations")
    else:
        logger.warning("No variations created, falling back to default")
        return _create_single_argument(state)

    # Finalize metrics
    node_usage = token_tracker.finalize()

    if "node_token_usage" not in state:
        state["node_token_usage"] = {}
    state["node_token_usage"][WorkflowNode.ARGUMENT_CREATOR] = node_usage

    logger.info(f"[ARGUMENT CREATOR NODE] Completed for member: {member_name} - "
               f"Time: {node_usage.elapsed_time_seconds:.2f}s, "
               f"Tokens: {node_usage.total_tokens}")

    return state


def _create_single_argument(state: TeamMemberState) -> TeamMemberState:
    """Fallback: create a single argument using standard workflow"""
    logger.info("Creating single argument (fallback mode)")

    token_tracker = create_node_tracker(WorkflowNode.ARGUMENT_CREATOR)

    use_personalization = state["argument_creation_context"].member_profile.use_personalization
    use_context_analysis = state["argument_creation_context"].member_profile.use_context_analysis

    knowledge_retriever = ArgumentCreationKnowledgeRetriever(
        llm=state["argument_creation_llm"],
        vector_db=state["vector_db"],
        tavily_tool=state["tavily_tool"],
        store=state["store"],
        use_personalization=use_personalization,
    )

    def retrieve_knowledge_node(arg_state: ArgumentCreatorState, config: RunnableConfig) -> ArgumentCreatorState:
        return knowledge_retriever.retrieve_knowledge_for_argument(arg_state, config)

    workflow = create_argument_creator_workflow(
        llm=state["argument_creation_llm"],
        retrieve_knowledge_node=retrieve_knowledge_node,
        knowledge_node_config=state.get("knowledge_node_config"),
        use_personalization=use_personalization,
        use_context_analysis=use_context_analysis,
        token_tracker=token_tracker,
    )

    # Get domain-goal pairs from analysis_result
    analysis_result = state.get("analysis_result")
    if analysis_result and isinstance(analysis_result, dict) and analysis_result.get("domain_goal_pairs"):
        domain_goal_pairs = analysis_result["domain_goal_pairs"]
        domains = [d for d, _ in domain_goal_pairs]
        goals = [g for _, g in domain_goal_pairs]
    else:
        domains = [state["topic"]]
        goals = [state["topic"]]
        domain_goal_pairs = [(state["topic"], state["topic"])]

    try:
        previous_arguments = state["af"].get_argument_test_by_team(state["team_name"], domains, goals)
    except:
        previous_arguments = []

    context = state["argument_creation_context"]
    context.previous_arguments = previous_arguments
    context.domain_goal_connections = domain_goal_pairs
    context.iteration_count = state["iteration_number"]

    initial_state = ArgumentCreatorState(
        context=context,
        retrieved_knowledge=state.get("knowledge_retrival_results", {}).get("retrieved_documents", [])
    )

    final_state = workflow.invoke(initial_state, state["argument_creation_config"])

    state["argument_creator_results"] = final_state

    state["tot_argument_variations"] = [{
        "variation_id": "fallback_0",
        "branch_id": "fallback",
        "strategy": "default",
        "strategy_name": "Default",
        "argument_text": final_state["final_argument"],
        "domain_goal_pairs": domain_goal_pairs,
        "full_state": final_state
    }]

    state["iteration_number"] += 1

    return state
