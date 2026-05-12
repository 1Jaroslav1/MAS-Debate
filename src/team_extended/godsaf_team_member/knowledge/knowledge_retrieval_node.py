import uuid
import logging
from src.team_extended.common.metrics.token_tracking import WorkflowNode, create_node_tracker
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.knowledge.model import KnowledgeRetrievalState, KnowledgeNodeConfig
from src.team_extended.common.knowledge.knowledge_retrieval_workflow import (
    create_knowledge_retrieval_workflow,
)

logger = logging.getLogger(__name__)

def knowledge_retrieval_node(state: TeamMemberState) -> TeamMemberState:
    member_config: KnowledgeNodeConfig = state.get("knowledge_node_config")
    warnings = member_config.validate_config()
    for warning in warnings:
        print(f"⚠️  Knowledge config warning: {warning}")

    if not member_config.is_effective_active():
        print(f"⏭️  Knowledge retrieval disabled for {state['team_member_name']}, skipping")
        context = state["knowledge_retrival_context"]
        if not context.session_id:
            context.session_id = str(uuid.uuid4())

        state["knowledge_retrival_results"] = KnowledgeRetrievalState(
            context=context,
            session_id=context.session_id,
            search_queries=[],
            retrieved_documents=[],
            current_query_index=0,
            memory_items=[]
        )
        return state

    member_name = state["team_member_name"]
    logger.info(f"[KNOWLEDGE_RETRIEVAL NODE] Starting for member: {member_name}")
    token_tracker = create_node_tracker(WorkflowNode.KNOWLEDGE_RETRIEVAL)

    workflow = create_knowledge_retrieval_workflow(
        llm=state["knowledge_retrival_llm"],
        vector_db=state["vector_db"],
        tavily_tool=state["tavily_tool"],
        store=state["store"],
        use_rag=member_config.use_rag,
        use_web_search=member_config.use_web_search,
        token_tracker=token_tracker,
    )

    # Use GoDsAF strategy recommendation
    strategy_recommendation = state["strategy_recommendation"]

    # Extract domain-goal connections from UGNs
    all_ugns = strategy_recommendation.primary_ugns + strategy_recommendation.secondary_ugns
    domains = [ugn.domain.description for ugn in all_ugns]
    goals = [ugn.goal.description for ugn in all_ugns]

    # Create domain-goal connection pairs for more targeted retrieval
    domain_goal_pairs = [(ugn.domain.description, ugn.goal.description) for ugn in all_ugns]

    # Get previous arguments from GoDsAF service if available
    try:
        previous_arguments = state["af"].get_argument_test_by_team(state["team_name"], domains, goals)
    except:
        previous_arguments = []

    context = state["knowledge_retrival_context"]
    context.previous_arguments = previous_arguments
    context.domains = domains
    context.goals = goals
    context.domain_goal_connections = domain_goal_pairs

    if not context.session_id:
        context.session_id = str(uuid.uuid4())

    initial_state = KnowledgeRetrievalState(
        context=context,
        session_id=context.session_id
    )

    config = state["knowledge_retrival_config"]
    if config is None:
        config = {"configurable": {"session_id": context.session_id}}

    print(f"🔍 Running knowledge retrieval with RAG={member_config.use_rag}, Web={member_config.use_web_search}")
    result = workflow.invoke(initial_state, config)

    state["knowledge_retrival_results"] = result

    node_usage = token_tracker.finalize()
    if "node_token_usage" not in state:
        state["node_token_usage"] = {}
    state["node_token_usage"][WorkflowNode.KNOWLEDGE_RETRIEVAL] = node_usage

    logger.info(f"[KNOWLEDGE_RETRIEVAL] Completed for member: {member_name} - "
               f"Time: {node_usage.elapsed_time_seconds:.2f}s, "
               f"Tokens: {node_usage.total_tokens}")

    return state
