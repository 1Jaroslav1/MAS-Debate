from typing import Callable, Optional
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.workflow.finalize_node import finalize_node
from src.team_extended.common.workflow.workflow_utils import should_rerun_argumentation, should_run_evaluation, should_run_knowledge_retrieval
from src.team_extended.common.workflow.candidate_creator_node import candidate_creator_node as default_candidate_creator_node
from langgraph.graph import StateGraph, START, END


def create_team_member_workflow(
    analyser_node: Callable[[TeamMemberState], TeamMemberState],
    knowledge_retrieval_node: Callable[[TeamMemberState], TeamMemberState],
    argument_creator_node: Callable[[TeamMemberState], TeamMemberState],
    evaluator_node: Callable[[TeamMemberState], TeamMemberState],
    candidate_creator_node: Optional[Callable[[TeamMemberState], TeamMemberState]] = None
) -> StateGraph:
    # Use provided candidate_creator_node or default one
    if candidate_creator_node is None:
        candidate_creator_node = default_candidate_creator_node

    workflow = StateGraph(TeamMemberState)

    workflow.add_node("analyser", analyser_node)
    workflow.add_node("knowledge_retrieval", knowledge_retrieval_node)
    workflow.add_node("argument_creator", argument_creator_node)
    workflow.add_node("candidate_creator", candidate_creator_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("finalize", finalize_node)

    workflow.add_edge(START, "analyser")

    # After analyser, decide whether to retrieve knowledge
    workflow.add_conditional_edges(
        "analyser",
        should_run_knowledge_retrieval,
        {
            "run_knowledge_retrieval": "knowledge_retrieval",
            "skip_knowledge_retrieval": "argument_creator"
        }
    )

    workflow.add_edge("knowledge_retrieval", "argument_creator")
    workflow.add_edge("argument_creator", "candidate_creator")

    workflow.add_conditional_edges(
        "candidate_creator",
        should_run_evaluation,
        {
            "run_evaluation": "evaluator",
            "skip_evaluation": "finalize"
        }
    )

    workflow.add_conditional_edges(
        "evaluator",
        should_rerun_argumentation,
        {
            "argument_creator": "argument_creator",
            "end": "finalize"
        }
    )

    workflow.add_edge("finalize", END)

    return workflow.compile()

