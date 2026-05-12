"""
Tree of Thoughts Team Member Workflow

This workflow implements the ToT architecture with:
- Multi-branch analysis generation
- Multiple argument variations per branch
- Fast scoring and pruning
- Deep evaluation of surviving branches
- Tree search for best argument selection
"""

from src.team_extended.tot_team_member.analyser.analyser_node import analyser_node
from src.team_extended.tot_team_member.knowledge.knowledge_retrieval_node import knowledge_retrieval_node
from src.team_extended.tot_team_member.argument_creator.argument_creator_node import argument_creator_node
from src.team_extended.tot_team_member.candidate_creator.candidate_creator_node import candidate_creator_node
from src.team_extended.tot_team_member.evaluator.evaluator_node import evaluator_node
from src.team_extended.common.workflow.workflow_factory import create_team_member_workflow
from src.team_extended.common.workflow.workflow_utils import (
    ensure_session_id,
    execute_workflow_with_error_handling
)
from src.team_extended.common.state import TeamMemberState
from langgraph.graph import StateGraph


def create_tot_team_member_workflow() -> StateGraph:
    """
    Create and configure the Tree of Thoughts team member workflow graph.

    Workflow: START -> analyser -> knowledge_retrieval -> argument_creator -> evaluator -> END

    All nodes use ToT-specific implementations:
    - analyser: Generates multiple diverse analysis branches
    - knowledge_retrieval: Retrieves knowledge (shared across branches)
    - argument_creator: Creates multiple argument variations per branch
    - candidate_creator: Creates candidate AFTER evaluator selects best variation
    - evaluator: Quick scores, prunes, deep evaluates, and selects best via tree search
    """
    return create_team_member_workflow(
        analyser_node=analyser_node,
        argument_creator_node=argument_creator_node,
        candidate_creator_node=candidate_creator_node,
        evaluator_node=evaluator_node,
        knowledge_retrieval_node=knowledge_retrieval_node
    )


def run_tot_team_member_workflow(initial_state: TeamMemberState) -> TeamMemberState:
    """
    Execute the complete Tree of Thoughts team member workflow with error handling.

    Args:
        initial_state: The initial state containing all necessary context

    Returns:
        The final state after workflow completion with best argument selected
    """
    workflow = create_tot_team_member_workflow()
    ensure_session_id(initial_state)
    return execute_workflow_with_error_handling(
        workflow,
        initial_state,
        workflow_name="ToT"
    )
