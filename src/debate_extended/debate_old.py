from typing import List
from langgraph.graph import StateGraph, START, END
from langgraph.store.memory import InMemoryStore
from src.debate_extended.state import DebateState, Team, UserState
from src.reasoning.godsaf.godsaf_service import GoDsAFService
from src.team_extended.state import TeamMember, TeamState
from src.team_extended.team import create_team_workflow
from src.team_extended.team_member.argument_creator.model import ArgumentContext
from src.team_extended.team_member.evaluator.evaluator import EvaluationConfig
from src.team_extended.team_member.knowledge.model import SearchContext
from src.team_extended.team_member.knowledge.vector_db_manager import VectorDBManager
from src.team_extended.team_member.team_member import MemberProfile, TeamFocusContext
from src.team_extended.user_guidance.user_guidance_service import UserGuidanceService
from src.team_extended.user_guidance.user_node import UserInteractionService
from src.hub import gpt_4o_mini, openai_text_embedding_3_small, get_tavily_tool

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
            team_focus=team["team_focus"]
        )
        workflow = create_team_workflow(team["team_members"])
        workflow.invoke(initial_team_state)
        return state
    return team_node


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

def create_next_round_condition(next_node: str):
    def next_round(state: DebateState):
        current_round = state["round"]
        max_rounds = state["max_rounds"]
        
        if current_round < max_rounds:
            return next_node
        else:
            return END
    return next_round

def increment_round(state: DebateState) -> DebateState:
    current_round = state["round"]
    state["round"] = current_round + 1
    print(f"📈 Round {state['round']} started")
    return state

def create_debate_workflow(teams: List[Team]) -> StateGraph:
    if len(teams) < 1:
        raise ValueError("Not enough teams")

    workflow = StateGraph(DebateState)
    workflow.add_node("user", user_node)
    workflow.add_node("increment_round", increment_round)
    workflow.add_edge(START, "increment_round")
    workflow.add_edge("increment_round", "user")

    first_team = teams[0]
    i_team = first_team 
    workflow.add_node(i_team["team_name"], create_team_node(i_team))
    workflow.add_edge("user", i_team["team_name"])

    for i in range(1, len(teams) - 1):
        j_team = teams[i]
        workflow.add_node(j_team["team_name"], create_team_node(j_team))
        workflow.add_edge(i_team["team_name"], j_team["team_name"])
        i_team = j_team

    j_team = teams[len(teams) - 1]
    if len(teams) > 1:
        workflow.add_node(j_team["team_name"], create_team_node(j_team))
        workflow.add_edge(i_team["team_name"], j_team["team_name"])

    workflow.add_conditional_edges(
        j_team["team_name"], 
        create_next_round_condition("increment_round"),
        ["increment_round", END]
    )

    return workflow.compile()

def member1(topic: str, team_focus: TeamFocusContext) -> TeamMember:
    member_profile = MemberProfile(
        name="AI Debater",
        education=["PhD in Computer Science", "MS in Political Science"],
        experience=["5 years in AI policy research", "3 years in regulatory analysis"],
        expertise_domains=["argumentation", "critical thinking", "research", "debate strategy", "AI policy"],
        current_role="Primary Argumenter",
        thinking_style="analytical",
        communication_style="academic",
        argumentation_preference="evidence-heavy",
        core_values=["evidence-based reasoning", "intellectual honesty", "thorough analysis"],
        philosophical_stance="pragmatic rationalist",
        risk_tolerance="moderate",
        decision_making_style="data-driven",
        preferred_evidence_types=["research", "case studies", "expert opinions", "statistics"],
        typical_counterargument_approach="acknowledge and systematically refute with evidence",
        industry_background="technology policy",
        cultural_background="academic research environment",
        notable_biases=["confirmation bias toward data-driven solutions"]
    )
    search_context = SearchContext(
        topic=topic,
        domains=[],
        goals=[],
        previous_arguments=[],
        perspective="proposition-supporting",
        iteration_count=0,
        excluded_sources=[],
        member_profile=member_profile,
        team_focus=team_focus
    )

    argument_context = ArgumentContext(
        topic=topic,
        domains=[],
        goals=[],
        member_profile=member_profile,
        team_focus=team_focus,
        previous_arguments=[],
        reviewer_feedback=None,
        iteration_count=1,
        max_iterations=3
    )
    return TeamMember(
        name=member_profile.name,
        member_profile=member_profile,
        knowledge_retrival_context=search_context,
        argument_creation_context=argument_context
    )

def member2(topic: str, team_focus: TeamFocusContext) -> TeamMember:
    member_profile = MemberProfile(
        name="MedTech Advocate",
        education=["BA in Medicine (4th year)", "Online certificates in AI/ML basics"],
        experience=["2 years clinical rotations", "1 year medical research assistant", "AI in medicine blog writer"],
        expertise_domains=["medical knowledge", "patient care", "medical ethics", "basic AI understanding", "healthcare technology"],
        current_role="Primary Argumenter",
        thinking_style="scientific",
        communication_style="clinical",
        argumentation_preference="case-study-based",
        core_values=["patient safety", "medical ethics", "scientific rigor", "innovation in healthcare"],
        philosophical_stance="medical pragmatist",
        risk_tolerance="calculated",
        decision_making_style="evidence-based medicine",
        preferred_evidence_types=["clinical trials", "medical case studies", "FDA reports", "medical AI research", "patient outcomes"],
        typical_counterargument_approach="present medical evidence and patient safety concerns",
        industry_background="healthcare (student)",
        cultural_background="medical academic environment",
        notable_biases=["prioritizes patient safety", "enthusiasm for medical innovation", "trust in peer-reviewed research"]
    )
    search_context = SearchContext(
        topic=topic,
        domains=[],
        goals=[],
        previous_arguments=[],
        perspective="proposition-supporting",
        iteration_count=0,
        excluded_sources=[],
        member_profile=member_profile,
        team_focus=team_focus
    )

    argument_context = ArgumentContext(
        topic=topic,
        domains=[],
        goals=[],
        member_profile=member_profile,
        team_focus=team_focus,
        previous_arguments=[],
        reviewer_feedback=None,
        iteration_count=1,
        max_iterations=3
    )
    return TeamMember(
        name=member_profile.name,
        member_profile=member_profile,
        knowledge_retrival_context=search_context,
        argument_creation_context=argument_context
    )

def team_1(topic: str) -> Team:
    team_focus = TeamFocusContext(
        team_type="proposition",
        perspective_description="Advocating for AI regulation with evidence-based arguments focusing on public safety and innovation balance",
        priority_aspects=[
            "Public safety considerations",
            "Innovation protection",
            "Regulatory precedents",
            "International competitiveness"
        ],
        evidence_preferences=[
            "Empirical studies",
            "Policy analysis reports",
            "Expert testimonials",
            "Regulatory case studies"
        ],
        counterargument_strategy="Acknowledge concerns while demonstrating superior benefits through evidence",
        rhetorical_emphasis="logical",
        focus_keywords=["regulation", "safety", "innovation", "oversight", "standards"],
        avoid_keywords=["stifling", "bureaucracy", "overreach"],
        viewpoint_orientation="supportive",
        interests_and_concerns=[
            "Public safety from AI risks",
            "Maintaining innovation momentum",
            "Creating effective oversight",
            "International regulatory coordination"
        ],
        typical_arguments=[
            "Evidence-based reasoning for regulation necessity",
            "Balanced approach preserving innovation",
            "Comparative analysis with other regulated industries",
            "Risk mitigation through proactive measures"
        ]
    )

    store = InMemoryStore(
        index={
            "embed": openai_text_embedding_3_small,
            "dims": 1536,
        }
    )

    members = [member1(topic, team_focus), member2(topic, team_focus)]

    return Team(
        team_name="t_proposition",
        team_focus=team_focus,
        team_members=members,
        evaluation_config=EvaluationConfig(),
        store=store
    )


def example_usage():
    af = GoDsAFService()

    af.add_team("t_proposition")
    af.add_team("t_user")

    af.add_domain("d_culture", "Organizational Culture", 25)
    af.add_domain("d_ops", "Operations", 80)

    af.add_goal("g_innovation", "Innovation and Creativity", {
        "d_culture": 10, 
        "d_ops": 30
    })
    af.add_goal("g_retention", "Employee Retention", {
        "d_culture": 15, 
        "d_ops": 55
    })

    topic = "Should artificial intelligence development be regulated by government?"

    vector_db = VectorDBManager(host="localhost", port=6333)
    tavily_tool = get_tavily_tool(max_results=1)

    teams = [team_1(topic)]

    initial_user_state = UserState(
        team_name="t_user",
        user_interaction_state=None
    )
    initial_state = DebateState(
        af=af,
        topic=topic,
        vector_db=vector_db,
        tavily_tool=tavily_tool,
        teams=teams,
        user=initial_user_state,
        round=0,
        max_rounds=3
    )
    workflow = create_debate_workflow(teams)

    answer = workflow.invoke(initial_state)

    print(answer)
