"""
Chain-of-Thought Team Member Workflow

This workflow uses CoT-specific nodes for:
- Analysis using chain-of-thought reasoning for domain-goal pair recommendation
- Knowledge retrieval based on recommended domain-goal pairs
- Argument creation with recommended domain-goal pairs
- Evaluation using chain-of-thought quality assessment
"""

from src.team_extended.cot_team_member.analyser.analyser_node import analyser_node
from src.team_extended.cot_team_member.knowledge.knowledge_retrieval_node import knowledge_retrieval_node
from src.team_extended.cot_team_member.argument_creator.argument_creator_node import argument_creator_node
from src.team_extended.cot_team_member.evaluator.evaluator_node import evaluator_node
from src.team_extended.common.workflow.workflow_factory import create_team_member_workflow
from src.team_extended.common.workflow.workflow_utils import (
    ensure_session_id,
    execute_workflow_with_error_handling
)
from src.team_extended.common.state import TeamMemberState
from langgraph.graph import StateGraph


def create_cot_team_member_workflow() -> StateGraph:
    """
    Create and configure the Chain-of-Thought team member workflow graph.
    
    Workflow: START -> analyser -> knowledge_retrieval -> argument_creator -> evaluator -> END
    
    All nodes use CoT-specific implementations:
    - analyser: Uses chain-of-thought reasoning to recommend domain-goal pairs
    - knowledge_retrieval: Retrieves knowledge based on recommended domain-goal pairs
    - argument_creator: Creates arguments based on recommended pairs
    - evaluator: Evaluates using chain-of-thought quality metrics
    """
    return create_team_member_workflow(
        analyser_node=analyser_node,
        argument_creator_node=argument_creator_node,
        evaluator_node=evaluator_node,
        knowledge_retrieval_node=knowledge_retrieval_node
    )


def run_cot_team_member_workflow(initial_state: TeamMemberState) -> TeamMemberState:
    """
    Execute the complete Chain-of-Thought team member workflow with error handling.
    
    Args:
        initial_state: The initial state containing all necessary context
        
    Returns:
        The final state after workflow completion
    """
    workflow = create_cot_team_member_workflow()
    ensure_session_id(initial_state)
    return execute_workflow_with_error_handling(
        workflow,
        initial_state,
        workflow_name="CoT"
    )
