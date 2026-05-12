from langgraph.graph import StateGraph, START, END
from src.team.team_memeber.state import TeamMemberState
from src.team.team_memeber.analysis_node import analysis_node
from src.team.team_memeber.data_retrieval_node import data_retrieval_node
from src.team.team_memeber.argumentation_node import argumentation_node
from src.team.team_memeber.lexicon_manager_node import lexicon_manager_node
from src.team.team_memeber.evaluator_node import evaluator_node


MAX_ITERATIONS = 3


def should_rerun_argumentation(state: TeamMemberState):
    if state["evaluation"]["reprocess"] and state["iteration_number"] < MAX_ITERATIONS:
        return "analysis_node"
    else:
        return END


def create_team_member_workflow() -> StateGraph:
    workflow = StateGraph(TeamMemberState)

    workflow.add_node("analysis_node", analysis_node)
    workflow.add_node("data_retrieval_node", data_retrieval_node)
    workflow.add_node("argumentation_node", argumentation_node)
    workflow.add_node("lexicon_manager_node", lexicon_manager_node)
    workflow.add_node("evaluator_node", evaluator_node)

    workflow.add_edge(START, "analysis_node")
    workflow.add_edge("analysis_node", "data_retrieval_node")
    workflow.add_edge("data_retrieval_node", "argumentation_node")
    workflow.add_edge("argumentation_node", "lexicon_manager_node")
    workflow.add_edge("lexicon_manager_node", "evaluator_node")
    workflow.add_conditional_edges("evaluator_node", should_rerun_argumentation, ["analysis_node", END])

    return workflow
