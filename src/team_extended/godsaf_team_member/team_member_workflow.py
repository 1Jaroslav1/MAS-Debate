from src.team_extended.godsaf_team_member.analyser.analyser_node import analyser_node
from src.team_extended.godsaf_team_member.knowledge.knowledge_retrieval_node import knowledge_retrieval_node
from src.team_extended.godsaf_team_member.argument_creator.argument_creator_node import argument_creator_node
from src.team_extended.godsaf_team_member.evaluator.evaluator_node import evaluator_node
from src.team_extended.common.workflow.workflow_factory import create_team_member_workflow
from src.team_extended.common.workflow.workflow_utils import (
    ensure_session_id,
    execute_workflow_with_error_handling
)
from src.team_extended.common.state import TeamMemberState
from langgraph.graph import StateGraph


def create_godsaf_team_member_workflow() -> StateGraph:
    return create_team_member_workflow(
        analyser_node=analyser_node,
        knowledge_retrieval_node=knowledge_retrieval_node,
        argument_creator_node=argument_creator_node,
        evaluator_node=evaluator_node,
    )


def run_godsaf_team_member_workflow(initial_state: TeamMemberState) -> TeamMemberState:
    workflow = create_godsaf_team_member_workflow()
    ensure_session_id(initial_state)
    return execute_workflow_with_error_handling(
        workflow,
        initial_state,
        workflow_name="GoDsAF"
    )
