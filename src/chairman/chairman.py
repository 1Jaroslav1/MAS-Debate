from langchain_core.prompts import PromptTemplate
from langgraph.constants import END
from pydantic import BaseModel, Field
from src.hub import gpt_4o_mini
from src.debate import DebateState


class ChairmanOutput(BaseModel):
    next_team: str = Field(description="Next team")


def chairman_node(state: DebateState):
    teams = state["teams"]
    executed_teams = state["executed_teams"]
    remaining_teams = [t for t in teams if t not in executed_teams]

    if remaining_teams:
        chairman_prompt = PromptTemplate(
            template="""
                    You are the chairman overseeing an ongoing debate among multiple teams. Your role is to ensure each team presents its arguments in a cohesive and strategic manner, guiding the overall debate flow. Below is the current status of the debate:

                    **Current Debate Status:**
                    - **Teams Participating:** {teams}.
                    - **Teams That Have Already Presented:** {executed_teams}.
                    - **Remaining Teams:** {remaining_teams}.

                    **Your Responsibilities:**
                    1. **Select the Next Team:** Randomly choose team ({remaining_teams}) to present next.
                """,
            input_variables=["teams", "executed_teams", "remaining_teams", "team_arguments"]
        )

        llm_chain = chairman_prompt | gpt_4o_mini.with_structured_output(ChairmanOutput)
        result = llm_chain.invoke(
            {
                "teams": teams,
                "executed_teams": executed_teams,
                "remaining_teams": remaining_teams,
            }
        )

        next_team_name = result.next_team
        opposite_team_arguments = [
            arg for team, args in state["team_arguments"].items() if team != next_team_name for arg in args
        ]
        next_team = None
        for team in teams:
            if team["name"] == next_team_name:
                next_team = team

        next_team_state = {
            "topic": next_team["topic"],
            "opposite_team_arguments": opposite_team_arguments,
            "members": next_team["members"],
            "team_leader_advice": "",
            "executed_members": [],
            "team_arguments": []
        }

        return {
            "executed_teams": state["executed_teams"] + [next_team],
            "next": next_team_name,
            "next_team_state": next_team_state
        }
    else:
        return {
            "next": END
        }
