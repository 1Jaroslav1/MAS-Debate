import logging
from typing import Callable, Optional
from langgraph.graph import StateGraph, START, END

from .model import ArgumentCreatorState
from .argument_creator_manager import ArgumentCreatorManager
from src.team_extended.common.metrics.token_tracking import NodeTokenTracker
from src.team_extended.common.knowledge.model import KnowledgeNodeConfig

logger = logging.getLogger(__name__)


def create_argument_creator_workflow(
    llm,
    retrieve_knowledge_node: Callable[[ArgumentCreatorState], ArgumentCreatorState],
    knowledge_node_config: KnowledgeNodeConfig,
    use_personalization: bool = True,
    use_context_analysis: bool = True,
    token_tracker: Optional[NodeTokenTracker] = None
) -> StateGraph:
    manager = ArgumentCreatorManager(llm, use_personalization=use_personalization, token_tracker=token_tracker)
    workflow = StateGraph(ArgumentCreatorState)

    def context_analysis_node(state: ArgumentCreatorState) -> ArgumentCreatorState:
        logger.info(f"[WORKFLOW - CONTEXT ANALYSIS] Starting context analysis for topic: {state.context.topic}")
        result = manager.analyze_context(state)
        logger.info(f"[WORKFLOW - CONTEXT ANALYSIS] Completed - Strategy approach: {result.strategy.approach if result.strategy else 'N/A'}")
        return result

    def argument_construction_node(state: ArgumentCreatorState) -> ArgumentCreatorState:
        logger.info(f"[WORKFLOW - ARGUMENT CONSTRUCTION] Starting argument construction for topic: {state.context.topic}")
        result = manager.construct_argument(state)
        logger.info(f"[WORKFLOW - ARGUMENT CONSTRUCTION] Completed - Generated {len(result.draft.full_argument) if result.draft else 0} characters")
        return result

    def finalization_node(state: ArgumentCreatorState) -> ArgumentCreatorState:
        logger.info(f"[WORKFLOW - FINALIZATION] Finalizing argument for topic: {state.context.topic}")
        state.final_argument = state.draft.full_argument
        logger.info(f"[WORKFLOW - FINALIZATION] Completed")
        return state
    
    retrieve_knowledge_enabled = knowledge_node_config.is_effective_active()
    if retrieve_knowledge_enabled:
        workflow.add_node("retrieve_knowledge", retrieve_knowledge_node)
    workflow.add_node("argument_construction", argument_construction_node)
    workflow.add_node("finalization", finalization_node)

    if use_context_analysis:
        # Include context_analysis node and connect it between retrieve_knowledge and argument_construction
        logger.info("[WORKFLOW] Building workflow WITH context analysis")
        workflow.add_node("context_analysis", context_analysis_node)
        
        if retrieve_knowledge_enabled:
            workflow.add_edge(START, "retrieve_knowledge")
            workflow.add_edge("retrieve_knowledge", "context_analysis")
  
        else:
            workflow.add_edge(START,"context_analysis")
        workflow.add_edge("context_analysis", "argument_construction")

    else:
        # Skip context_analysis and go directly from retrieve_knowledge to argument_construction
        logger.info("[WORKFLOW] Building workflow WITHOUT context analysis (skipped)")
        if retrieve_knowledge_enabled:
            workflow.add_edge(START, "retrieve_knowledge")
            workflow.add_edge("retrieve_knowledge", "argument_construction")
        else:
            workflow.add_edge(START,"argument_construction")

    workflow.add_edge("argument_construction", "finalization")
    workflow.add_edge("finalization", END)

    return workflow.compile()

