import logging
from langchain_core.runnables import RunnableConfig

from src.team_extended.common.knowledge.argument_creation_knowledge_retrieval import ArgumentCreationKnowledgeRetriever
from src.team_extended.common.argument_creator.model import (
    ArgumentCreatorState,
)
from src.team_extended.common.argument_creator.argument_creation_workflow import (
    create_argument_creator_workflow,
)
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.metrics.execution_metrics import MetricsCollector
from src.team_extended.common.metrics.token_tracking import create_node_tracker, WorkflowNode

logger = logging.getLogger(__name__)


def argument_creator_node(state: TeamMemberState) -> TeamMemberState:
    member_name = state["team_member_name"]
    team_name = state["team_name"]
    round_num = state.get("round", 0)

    logger.info(f"[ARGUMENT CREATOR NODE] Starting for member: {member_name}")

    token_tracker = create_node_tracker(WorkflowNode.ARGUMENT_CREATOR)

    # Get flags from member profile
    use_personalization = state["argument_creation_context"].member_profile.use_personalization
    use_context_analysis = state["argument_creation_context"].member_profile.use_context_analysis

    logger.info(f"[ARGUMENT CREATOR NODE] Configuration - use_personalization: {use_personalization}, use_context_analysis: {use_context_analysis}")

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
    
    analysis_result = state.get("analysis_result")
    if analysis_result and isinstance(analysis_result, dict) and analysis_result.get("domain_goal_pairs"):
        domain_goal_pairs = analysis_result["domain_goal_pairs"]
        domains = [d for d, _ in domain_goal_pairs]
        goals = [g for _, g in domain_goal_pairs]
    else:
        print("No domain-goal pairs found in analysis result")
        try:
            af_service = state.get("af")
            if af_service:
                domain_objs = af_service.list_domains()
                goal_objs = af_service.list_goals()
                domains = [d.name for d in domain_objs] if domain_objs else [state["topic"]]
                goals = [g.name for g in goal_objs] if goal_objs else [state["topic"]]
                domain_goal_pairs = [(d, g) for d in domains for g in goals]
            else:
                domains = [state["topic"]]
                goals = [state["topic"]]
                domain_goal_pairs = [(state["topic"], state["topic"])]
        except Exception:
            domains = [state["topic"]]
            goals = [state["topic"]]
            domain_goal_pairs = [(state["topic"], state["topic"])]

    # Get previous arguments from GoDsAF service if available
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
        retrieved_knowledge = state.get("knowledge_retrival_results", {}).get("retrieved_documents", [])
    )

    config = state["argument_creation_config"]

    if config is None:
        config = RunnableConfig(configurable={"session_id": context.session_id})

    logger.info(f"[ARGUMENT CREATOR NODE] Invoking workflow for member: {member_name}")

    result = workflow.invoke(initial_state, config)

    state["argument_creator_results"] = result

    # Finalize token tracker
    node_usage = token_tracker.finalize()

    # Store node token usage
    if "node_token_usage" not in state:
        state["node_token_usage"] = {}
    state["node_token_usage"][WorkflowNode.ARGUMENT_CREATOR] = node_usage

    logger.info(f"[ARGUMENT CREATOR NODE] Completed for member: {member_name} - "
               f"Time: {node_usage.elapsed_time_seconds:.2f}s, "
               f"Tokens: {node_usage.total_tokens}")

    state["iteration_number"] += 1
    
    return state
