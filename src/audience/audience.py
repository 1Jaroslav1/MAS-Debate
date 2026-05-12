from src.audience.state import AudienceState
from src.model.model import AudienceMember
from typing_extensions import List
from src.audience.audience_member import create_member
from langgraph.graph import StateGraph, START, END


def create_audience(step: str, members: List[AudienceMember]):
    workflow = StateGraph(AudienceState)

    for member in members:
        workflow.add_node(member["name"], create_member(step, member))
        workflow.add_edge(START, member["name"])
        workflow.add_edge(member["name"], END)

    return workflow
