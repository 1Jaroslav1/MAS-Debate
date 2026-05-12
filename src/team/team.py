from typing_extensions import List
from langgraph.graph import StateGraph, START, END
from src.team.state import TeamState
from src.model.model import TeamMember, Transcript
from src.team.team_memeber import create_team_member_workflow, TeamMemberState


def create_team_member_node(person: TeamMember):
    def team_member_node(state: TeamState):
        team_member_workflow = create_team_member_workflow()
        team_member = team_member_workflow.compile()

        team_member_state: TeamMemberState = {
            "topic": state["topic"],
            "team_role": state["team_role"],
            "person": person,
            "transcript": state["transcript"],
            "audience_profile": state["audience_profile"],
            "team_arguments": [],
            "opponent_arguments": [],
            "analysis": {},
            "retrieved_data": {},
            "argument": {},
            "lexicon_adjustment": {},
            "evaluation": {},
            "iteration_number": 0
        }

        result = team_member.invoke(team_member_state)

        team_member_transcript: Transcript = {
            "speaker": person,
            "team_role": state["team_role"],
            "text": result["lexicon_adjustment"]["refined_argument"]
        }

        state["transcript"] = state["transcript"] + [team_member_transcript]

        return state

    return team_member_node


def create_team_workflow(members: List[TeamMember]) -> StateGraph:
    if len(members) < 1:
        raise ValueError("Not enough members")

    workflow = StateGraph(TeamState)
    i_member = members[0]
    workflow.add_node(i_member["name"], create_team_member_node(i_member))
    workflow.add_edge(START, i_member["name"])

    for i in range(1, len(members) - 1):
        j_member = members[i]
        workflow.add_node(j_member["name"], create_team_member_node(j_member))
        workflow.add_edge(i_member["name"], j_member["name"])
        i_member = j_member

    j_member = members[len(members) - 1]
    if len(members) > 1:
        workflow.add_node(j_member["name"], create_team_member_node(j_member))
        workflow.add_edge(i_member["name"], j_member["name"])

    workflow.add_edge(j_member["name"], END)

    return workflow
