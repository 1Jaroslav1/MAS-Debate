from typing import List
from src.reasoning.godsaf.godsaf_service import GoDsAFService
from langgraph.store.memory import InMemoryStore
from langgraph.graph import StateGraph, START, END
from src.team_extended.state import TeamMember, TeamState
from src.team_extended.common.argument_creator.model import ArgumentContext
from src.team_extended.common.evaluator.evaluator import EvaluationConfig
from src.team_extended.common.knowledge.model import SearchContext, KnowledgeNodeConfig
from src.team_extended.common.evaluator.model import EvaluationNodeConfig
from src.team_extended.common.knowledge.vector_db_manager import VectorDBManager
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.team_member import MemberProfile, TeamFocusContext
from src.team_extended.godsaf_team_member.team_member_workflow import run_godsaf_team_member_workflow
from src.team_extended.cot_team_member.team_member_workflow import run_cot_team_member_workflow
from src.team_extended.tot_team_member.team_member_workflow import run_tot_team_member_workflow
from src.hub import gpt_4o_mini, openai_text_embedding_3_small, get_tavily_tool
from src.debate_extended.debate_result_service import DebateResultsService

def create_team_member_node(member: TeamMember, architecture: str = "godsaf", tot_config: dict = None):
    def team_member_node(state: TeamState) -> TeamState:
        initial_member_state: TeamMemberState = TeamMemberState(
            af=state["af"],
            topic=state["topic"],
            team_name=state["team_name"],
            team_member_name=member["name"],
            vector_db=state["vector_db"],
            tavily_tool=state["tavily_tool"],
            store=state["store"],
            iteration_number=0,
            architecture=architecture,
            tot_config=tot_config if architecture == "tot" else None,
            analyser_llm=state.get("argument_creation_llm", gpt_4o_mini),
            knowledge_retrival_context=member["knowledge_retrival_context"],
            knowledge_retrival_llm=state.get("knowledge_retrival_llm", gpt_4o_mini),
            argument_creation_context=member["argument_creation_context"],
            argument_creation_llm=state.get("argument_creation_llm", gpt_4o_mini),
            evaluation_config=state["evaluation_config"],
            evaluation_llm=state.get("evaluation_llm", gpt_4o_mini),
            knowledge_retrival_config=None,
            argument_creation_config=None,
            strategy_recommendation=None,
            candidate_id="current_candidate_id",
            round=state.get("round", 0),
            knowledge_node_config=member.get("knowledge_node_config"),
            evaluation_node_config=member.get("evaluation_node_config"),
            metrics_aggregator=state["metrics_aggregator"],
        )

        final_member_state = initial_member_state
        try:
            if architecture == "godsaf":
                final_member_state = run_godsaf_team_member_workflow(initial_member_state)
            elif architecture == "tot":
                final_member_state = run_tot_team_member_workflow(initial_member_state)
            else:
                final_member_state = run_cot_team_member_workflow(initial_member_state)
        except RuntimeError as e:
            if "parsing failed" in str(e) or "grounding stopped because of errors" in str(e):
                print(f"Warning: Team member workflow failed due to parsing/grounding error for member {member["name"]}. Continuing. Error: {e}")
            else:
                raise
        except Exception as e:
            print(f"Warning: Unexpected error in team member workflow for member {member["name"]}. Continuing. Error: {e}")

        finalized_log_entry = final_member_state.get("finalized_argument_log_entry")
        if finalized_log_entry:
            state["argument_log"].append(finalized_log_entry)
        
        try:
            godsaf_results = state["af"].solve()
        except RuntimeError as e:
            if "parsing failed" in str(e) or "grounding stopped because of errors" in str(e):
                print(f"Warning: Failed to solve GoDsAF for member {member["name"]}. Using empty results. Error: {e}")
                godsaf_results = {"tgs": {}}
            else:
                raise
        except Exception as e:
            print(f"Warning: Unexpected error solving GoDsAF for member {member.name}. Using empty results. Error: {e}")
            godsaf_results = {"tgs": {}}

        current_round = state.get("round", 0)
        
        state["tgs_snapshots"].append({
            "round": current_round,
            "team": state["team_name"],
            "member": member["name"],
            "tgs": {f"{g}-{d}": v for (g, d), v in godsaf_results.get("tgs", {}).get(state["team_name"], {}).items()}
        })
        
        return state
    return team_member_node

def create_team_workflow(members: List[TeamMember], architecture: str = "godsaf", tot_config: dict = None) -> StateGraph:
    if len(members) < 1:
        raise ValueError("Not enough members")

    workflow = StateGraph(TeamState)
    i_member = members[0]
    workflow.add_node(i_member["name"], create_team_member_node(i_member, architecture, tot_config))
    workflow.add_edge(START, i_member["name"])

    for i in range(1, len(members) - 1):
        j_member = members[i]
        workflow.add_node(j_member["name"], create_team_member_node(j_member, architecture, tot_config))
        workflow.add_edge(i_member["name"], j_member["name"])
        i_member = j_member

    j_member = members[len(members) - 1]
    if len(members) > 1:
        workflow.add_node(j_member["name"], create_team_member_node(j_member, architecture, tot_config))
        workflow.add_edge(i_member["name"], j_member["name"])

    workflow.add_edge(j_member["name"], END)

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
        argument_creation_context=argument_context,
        knowledge_node_config=KnowledgeNodeConfig(
            active=False,
            use_rag=False,
            use_web_search=False
        ),
        evaluation_node_config=EvaluationNodeConfig(active=True)
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
        argument_creation_context=argument_context,
        knowledge_node_config=KnowledgeNodeConfig(
            active=False,
            use_rag=False,
            use_web_search=False
        ),
        evaluation_node_config=EvaluationNodeConfig(active=True)
    )

def example_usage():
    af = GoDsAFService()

    af.add_team("t_proposition")
    af.add_team("tws")

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
    vector_db = VectorDBManager(host="localhost", port=6333)
    tavily_tool = get_tavily_tool(max_results=1)
    store = InMemoryStore(
        index={
            "embed": openai_text_embedding_3_small,
            "dims": 1536,
        }
    )
    topic = "Should artificial intelligence development be regulated by government?"
    
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
    
    eval_config = EvaluationConfig()

    memebrs = [member1(topic, team_focus), member2(topic, team_focus)]

    workflow = create_team_workflow(memebrs)

    initial_state = TeamState(
        af=af,
        topic=topic,
        team_name="t_proposition",
        vector_db=vector_db,
        tavily_tool=tavily_tool,
        store=store,
        evaluation_config=eval_config,
        team_focus=team_focus
    )

    answer = workflow.invoke(initial_state)
    
    print(answer)
