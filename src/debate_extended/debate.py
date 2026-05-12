import traceback
from typing import List
from langgraph.graph import StateGraph, START, END
from src.debate_extended.debate_result_service import DebateResultsService
from src.debate_extended.state import DebateState, Team
from src.team_extended.state import TeamState
from src.team_extended.team import create_team_workflow
from src.team_extended.user_guidance.user_guidance_service import UserGuidanceService
from src.team_extended.user_guidance.user_node import UserInteractionService
from src.hub import gpt_4o_mini
from src.audience_extended.audience_node import AudienceNode
from src.team_extended.common.metrics.execution_metrics import MetricsAggregator

def create_team_node(team: Team):
    def team_node(state: DebateState) -> DebateState:
        initial_team_state: TeamState = TeamState(
            af=state["af"],
            topic=state["topic"],
            team_name=team["team_name"],
            vector_db=state["vector_db"],
            tavily_tool=state["tavily_tool"],
            store=team["store"],
            evaluation_config=team["evaluation_config"],
            team_focus=team["team_focus"],
            knowledge_retrival_llm=state["team_llm"],
            argument_creation_llm=state["team_llm"],
            evaluation_llm=state["team_llm"],
            round=state["round"],
            metrics_aggregator=state["metrics_aggregator"],
            tgs_snapshots=[],
            argument_log=[]
        )
        tot_config = team.get("tot_config")
        workflow = create_team_workflow(team["team_members"], team["architecture"], tot_config)

        try:
            final_team_state = workflow.invoke(initial_team_state)
        except RuntimeError as e:
            if "parsing failed" in str(e) or "grounding stopped because of errors" in str(e):
                print(f"Warning: Team workflow failed due to parsing/grounding error for team {team['team_name']}. Continuing. Error: {e}")
                final_team_state = initial_team_state
            else:
                raise
        except Exception as e:
            print(
                f"Warning: Unexpected error in team workflow for team {team['team_name']}. Continuing."
            )
            traceback.print_exc()
            final_team_state = initial_team_state
        if "tgs_snapshots" in final_team_state:
            state["tgs_snapshots"].extend(final_team_state["tgs_snapshots"])
        
        if "argument_log" in final_team_state:
            state["argument_log"].extend(final_team_state["argument_log"])
        return state
    return team_node


def create_audience_initial_voting_node(audience_node: AudienceNode):
    def audience_initial_voting(state: DebateState) -> DebateState:
        return audience_node.initial_voting_node(state)
    return audience_initial_voting


def create_audience_final_voting_node(audience_node: AudienceNode):
    def audience_final_voting(state: DebateState) -> DebateState:
        return audience_node.final_voting_node(state)
    return audience_final_voting


def user_node(state: DebateState) -> DebateState:
    interaction_state = state["user"]["user_interaction_state"]

    guidance_service = UserGuidanceService(
        godsaf_service=state["af"],
        llm=gpt_4o_mini
    )
    
    interaction_service = UserInteractionService(guidance_service)

    team_name = state["user"]["team_name"]
    topic = state["topic"]
    
    result, updated_interaction_state = interaction_service.run_user_interaction(
        team_name, topic, interaction_state
    )

    state["user"]["user_interaction_state"] = updated_interaction_state

    if updated_interaction_state.step >= 6:
        print(f"\n🎭 User interaction completed: {result}")
    
    return state


def create_next_round_condition(state: DebateState):
    current_round = state["round"]
    max_rounds = state["max_rounds"]
    
    if current_round < max_rounds:
        return "increment_round"
    else:
        return "audience_final_voting"


def increment_round(state: DebateState) -> DebateState:
    current_round = state["round"]
    state["round"] = current_round + 1
    print(f"📈 Round {state['round']} started")
    return state


def create_enhanced_debate_workflow(teams: List[Team], audience_node: AudienceNode, include_user_interaction: bool) -> StateGraph:
    """Create enhanced debate workflow with audience voting and multiple rounds"""
    if len(teams) < 2:
        raise ValueError("Need at least 2 teams for debate")

    workflow = StateGraph[DebateState, None, DebateState, DebateState](DebateState)
    
    workflow.add_node("audience_initial_voting", create_audience_initial_voting_node(audience_node))
    workflow.add_node("increment_round", increment_round)

    if(include_user_interaction):
        workflow.add_node("user", user_node)
    
    for team in teams:
        workflow.add_node(team["team_name"], create_team_node(team))
    
    workflow.add_node("audience_final_voting", create_audience_final_voting_node(audience_node))
    
    workflow.add_edge(START, "audience_initial_voting")
    workflow.add_edge("audience_initial_voting", "increment_round")
    
    if(include_user_interaction):
        workflow.add_edge("increment_round", "user")
        workflow.add_edge("user", teams[0]["team_name"])
    else:
        workflow.add_edge("increment_round", teams[0]["team_name"])

    for i in range(len(teams) - 1):
        workflow.add_edge(teams[i]["team_name"], teams[i + 1]["team_name"])
    
    workflow.add_conditional_edges(
        teams[-1]["team_name"], 
        create_next_round_condition,
        ["increment_round", "audience_final_voting"]
    )
    
    workflow.add_edge("audience_final_voting", END)

    return workflow.compile()
