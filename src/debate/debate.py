import random
from src.debate.state import DebateState
from langgraph.graph import StateGraph, START, END
from src.audience.audience import create_audience
from src.team import create_team_workflow, human_argument
from src.model.model import TeamRole, Transcript
from typing_extensions import List
from src.model.model import Decision
from src.tutor.tutor import creat_tutor
from langgraph.errors import GraphInterrupt
from src.hub.llm_hub import gpt_4o_mini
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


def determine_winner(initial_scores: List[Decision], final_scores: List[Decision]) -> str:
    initial_map = {score["name"]: score["value"] for score in initial_scores}

    swing_agree = 0
    swing_disagree = 0

    for decision in final_scores:
        name = decision["name"]
        final_vote = decision["value"]
        initial_vote = initial_map.get(name)

        if initial_vote is not None and initial_vote != final_vote:
            if final_vote == "agree":
                swing_agree += 1
            elif final_vote == "disagree":
                swing_disagree += 1

    if swing_agree > swing_disagree:
        return "Pro Team wins"
    elif swing_disagree > swing_agree:
        return "Opposing Team wins"
    else:
        final_agree = sum(1 for d in final_scores if d["value"] == "agree")
        final_disagree = sum(1 for d in final_scores if d["value"] == "disagree")

        if final_agree > final_disagree:
            return "Pro Team wins"
        elif final_disagree > final_agree:
            return "Opposing Team wins"
        else:
            return "Tie"


def audience_init_node(state: DebateState):
    audience_workflow = create_audience("init", state["audience_members"])
    audience = audience_workflow.compile()
    result = audience.invoke({
        "topic": state["topic"],
        "transcript": [],
        "initial_scores": [],
        "final_scores": []
    })

    state["initial_scores"] = result["initial_scores"]

    return state


def audience_final_node(state: DebateState):
    audience_workflow = create_audience("final", state["audience_members"])
    audience = audience_workflow.compile()
    result = audience.invoke({
        "topic": state["topic"],
        "transcript": state["transcript"],
        "initial_scores": [],
        "final_scores": []
    })

    state["final_scores"] = result["final_scores"]

    print(determine_winner(state["initial_scores"], state["final_scores"]))

    return state


def create_team_node(member_key: str, team_role: TeamRole):
    def team_node(state: DebateState):
        team_workflow = create_team_workflow(state[member_key])
        team = team_workflow.compile()
        result = team.invoke({
            "topic": state["topic"],
            "team_role": team_role,
            "transcript": state["transcript"],
            "audience_profile": {
                "audience_members": state["audience_members"]
            }
        })
        state["round"] += 1
        state["transcript"] = result["transcript"]
        return state

    return team_node

def user_node(state: DebateState):
    try:
        result = human_argument()
    except GraphInterrupt as gi:
        user_input = input("Please enter your argument: ")
        result = user_input

    state["round"] += 1
    state["transcript"] = [
        {
            "speaker": {
                "name": "Yaroslav Harbar",
                "experience": ["web development", "cloud solutions", "system architecture", "large language models"],
                "description": "Active student in the Warsaw University of Technologies on the AI course"
            },
            "team_role": TeamRole.USER,
            "text": result
        }
    ]

    return state


class AudienceMemberDecisionOutput(BaseModel):
    decision: str = Field(description="Decision: either 'agree' or 'disagree'.")


class DebaterDecisionOutput(BaseModel):
    arguments: str = Field(description="Arguments")


# def user_node(state: DebateState):
#     name = "Robert Smith"
#     experience = "Retired librarian "
#     description = "A retired librarian with a lifelong passion for literature, she now delights in quiet days immersed in books and sharing her wealth of knowledge with the community."
#
#     prompt = PromptTemplate(
#         template="""
#             You are a proposal debater who has actively participated in a debate on the following topic:
#             {topic}
#
#             Debate Transcripts:
#             {transcripts}
#
#             Your personal profile:
#             - Name: {name}
#             - Interests: {description}
#             - Work Experience: {experience}
#
#             Do not use terms, which you probably should not know.
#
#             Your goal is to create argument that convinces the audience of your position.
#         """,
#         input_variables=["name", "description", "experience", "topic", "transcripts"]
#     )
#
#     chain = prompt | gpt_4o_mini.with_structured_output(DebaterDecisionOutput)
#     result = chain.invoke({
#         "name": name,
#         "description": description,
#         "experience": experience,
#         "topic": state["topic"],
#         "transcripts": state["transcript"]
#     })
#
#     state["round"] += 1
#     state["transcript"] += [
#         {
#             "speaker": {
#                 "name": name,
#                 "experience": experience,
#                 "description": description
#             },
#             "team_role": TeamRole.USER,
#             "text": result.arguments
#         }
#     ]
#
#     return state

def get_transcripts_by_role(transcript: List[Transcript], role: TeamRole) -> List[Transcript]:
    return [t for t in transcript if t["team_role"] == role]


def tutor_node(state: DebateState):
    tutor_workflow = creat_tutor()
    tutor = tutor_workflow.compile()

    result = tutor.invoke({
        "topic": state["topic"],
        "user_arguments": get_transcripts_by_role(state["transcript"], TeamRole.USER),
        "opponent_arguments": get_transcripts_by_role(state["transcript"], TeamRole.OPPOSING),
        "audience_profile": {
            "audience_members": state["audience_members"]
        }
    })

    print("============Tutor score===========\n\n", result)

    return state


choice = random.choice([True, False])
first_team = "pro_team" if choice else "opp_team"
second_team = "opp_team" if choice else "pro_team"


def next_round(state: DebateState):
    if "round" in state and state["round"] / 2 < 1:
        return first_team
    else:
        return "audience_final"


def create_debate():
    workflow = StateGraph(DebateState)
    workflow.add_node("audience_init", audience_init_node)
    # workflow.add_node("pro_team", user_node)
    workflow.add_node("pro_team", create_team_node("proposing_members", TeamRole.PROPOSING))
    workflow.add_node("opp_team", create_team_node("opposing_members", TeamRole.OPPOSING))
    workflow.add_node("audience_final", audience_final_node)
    # workflow.add_node("tutor_node", tutor_node)

    workflow.add_edge(START, "audience_init")
    workflow.add_edge("audience_init", first_team)
    workflow.add_edge(first_team, second_team)
    workflow.add_conditional_edges(second_team, next_round, [first_team, "audience_final"])
    # workflow.add_edge("audience_final", "tutor_node")
    workflow.add_edge("audience_final", END)

    return workflow
