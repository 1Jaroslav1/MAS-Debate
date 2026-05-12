import json
from typing import Dict, List, Any
from pathlib import Path

from src.debate_extended.config.model import DebateConfig, MemberConfig, TeamConfig
from src.debate_extended.state import DebateState, Team, UserState
from src.team_extended.common.metrics.execution_metrics import MetricsAggregator
from src.team_extended.state import TeamMember
from src.team_extended.common.team_member import MemberProfile, TeamFocusContext
from src.team_extended.common.argument_creator.model import ArgumentContext
from src.team_extended.common.knowledge.model import SearchContext, KnowledgeNodeConfig
from src.team_extended.common.evaluator.model import EvaluationNodeConfig
from src.team_extended.common.evaluator.evaluator import EvaluationConfig
from src.hub import gpt_4o_mini, openai_text_embedding_3_small, get_tavily_tool, get_llm
from src.audience_extended.audience_node import (
    map_audience_to_domains_goals,
    AudienceNode,
    ListenerProfile,
    Listener
)
from src.reasoning.godsaf.godsaf_service import GoDsAFService
from src.team_extended.common.knowledge.vector_db_manager import VectorDBManager
from langgraph.store.memory import InMemoryStore
from src.debate_extended.debate_result_service import DebateResultsService

class DebateBuilder:
    def __init__(self, config: DebateConfig):
        self.config = config
        self.af = GoDsAFService()
        self.vector_db = VectorDBManager(host="localhost", port=6333)
        self.tavily_tool = get_tavily_tool(max_results=1)
        try:
            self.team_llm = get_llm(self.config.team_llm_model)
        except Exception:
            self.team_llm = gpt_4o_mini
    
    def create_member(self, member_config: MemberConfig, team_focus: TeamFocusContext) -> TeamMember:
        member_profile = MemberProfile(
            name=member_config.name,
            education=member_config.education,
            experience=member_config.experience,
            expertise_domains=member_config.expertise_domains,
            current_role=member_config.current_role,
            thinking_style=member_config.thinking_style,
            communication_style=member_config.communication_style,
            argumentation_preference=member_config.argumentation_preference,
            core_values=member_config.core_values,
            philosophical_stance=member_config.philosophical_stance,
            risk_tolerance=member_config.risk_tolerance,
            decision_making_style=member_config.decision_making_style,
            preferred_evidence_types=member_config.preferred_evidence_types,
            typical_counterargument_approach=member_config.typical_counterargument_approach,
            industry_background=member_config.industry_background,
            cultural_background=member_config.cultural_background,
            notable_biases=member_config.notable_biases
        )
        
        search_context = SearchContext(
            topic=self.config.topic,
            domains=[],
            goals=[],
            previous_arguments=[],
            perspective=member_config.perspective,
            iteration_count=0,
            excluded_sources=[],
            member_profile=member_profile,
            team_focus=team_focus
        )

        argument_context = ArgumentContext(
            topic=self.config.topic,
            domains=[],
            goals=[],
            member_profile=member_profile,
            team_focus=team_focus,
            previous_arguments=[],
            reviewer_feedback=None,
            iteration_count=1,
            max_iterations=member_config.max_iterations
        )

        knowledge_config = KnowledgeNodeConfig(
            active=member_config.knowledge_active,
            use_rag=member_config.knowledge_use_rag,
            use_web_search=member_config.knowledge_use_web_search
        )

        evaluation_config = EvaluationNodeConfig(
            active=member_config.evaluation_active
        )

        return TeamMember(
            name=member_profile.name,
            member_profile=member_profile,
            knowledge_retrival_context=search_context,
            argument_creation_context=argument_context,
            knowledge_node_config=knowledge_config,
            evaluation_node_config=evaluation_config
        )
    
    def create_team(self, team_config: TeamConfig) -> Team:
        """Create a team from configuration"""
        team_focus = TeamFocusContext(
            team_type=team_config.team_type,
            perspective_description=team_config.perspective_description,
            priority_aspects=team_config.priority_aspects,
            evidence_preferences=team_config.evidence_preferences,
            counterargument_strategy=team_config.counterargument_strategy,
            rhetorical_emphasis=team_config.rhetorical_emphasis,
            focus_keywords=team_config.focus_keywords,
            avoid_keywords=team_config.avoid_keywords,
            viewpoint_orientation=team_config.viewpoint_orientation,
            interests_and_concerns=team_config.interests_and_concerns,
            typical_arguments=team_config.typical_arguments
        )

        store = InMemoryStore(
            index={
                "embed": openai_text_embedding_3_small,
                "dims": 1536,
            }
        )

        members = [self.create_member(member_config, team_focus) for member_config in team_config.members]

        # Convert ToTConfig to dict if present, or create default for ToT architecture
        tot_config_dict = None
        if team_config.architecture == "tot":
            if team_config.tot_config:
                # Use provided config
                tot_config_dict = {
                    "num_analysis_branches": team_config.tot_config.num_analysis_branches,
                    "num_argument_variations": team_config.tot_config.num_argument_variations,
                    "pruning_strategy": team_config.tot_config.pruning_strategy,
                    "analysis_pruning_k": team_config.tot_config.analysis_pruning_k,
                    "argument_pruning_k": team_config.tot_config.argument_pruning_k,
                    "search_algorithm": team_config.tot_config.search_algorithm,
                    "enable_fast_scoring": team_config.tot_config.enable_fast_scoring,
                    "diversity_weight": team_config.tot_config.diversity_weight,
                }
            else:
                # Create default config for ToT architecture
                tot_config_dict = {
                    "num_analysis_branches": 3,
                    "num_argument_variations": 3,
                    "pruning_strategy": "top_k",
                    "analysis_pruning_k": 3,
                    "argument_pruning_k": 5,
                    "search_algorithm": "best_first",
                    "enable_fast_scoring": True,
                    "diversity_weight": 0.2,
                }

        return Team(
            team_name=team_config.team_name,
            team_focus=team_focus,
            team_members=members,
            evaluation_config=EvaluationConfig(),
            store=store,
            architecture=team_config.architecture,
            tot_config=tot_config_dict
        )
            

    def create_audience(self) -> AudienceNode:
        custom_listeners = self.config.audience.listeners or []
        
        listeners = []
        for i, listener_config in enumerate(custom_listeners):
            profile = ListenerProfile(
                name=listener_config.get("name", f"Listener {i+1}"),
                education=listener_config.get("education", []),
                experience=listener_config.get("experience", []),
                expertise_domains=listener_config.get("expertise_domains", []),
                current_role=listener_config.get("current_role", "Listener"),
                thinking_style=listener_config.get("thinking_style", "analytical"),
                communication_style=listener_config.get("communication_style", "direct"),
                argumentation_preference=listener_config.get("argumentation_preference", "evidence-heavy"),
                core_values=listener_config.get("core_values", []),
                philosophical_stance=listener_config.get("philosophical_stance", "pragmatic"),
                risk_tolerance=listener_config.get("risk_tolerance", "moderate"),
                decision_making_style=listener_config.get("decision_making_style", "data-driven"),
                preferred_evidence_types=listener_config.get("preferred_evidence_types", []),
                typical_counterargument_approach=listener_config.get("typical_counterargument_approach", "systematic analysis"),
                industry_background=listener_config.get("industry_background"),
                cultural_background=listener_config.get("cultural_background"),
                notable_biases=listener_config.get("notable_biases", [])
            )
            
            listeners.append(Listener(profile))
        
        audience_node = AudienceNode(listeners)
        
        print("🎯 Analyzing audience to generate relevant domains and goals...")
        map_audience_to_domains_goals(
            listeners, 
            self.af,
            max_domains=self.config.audience.max_domains,
            max_goals=self.config.audience.max_goals
        )
        
        return audience_node
    
    def get_initial_user_state(self) -> UserState:
        if self.config.include_user_interaction:
            return UserState(
                team_name=self.config.user_team_name,
                user_interaction_state=None
            )
        return None
    
    def is_user_interaction_enabled(self) -> bool:
        return self.config.include_user_interaction

    def create_initial_state(self, teams: List[Team]) -> DebateState:
        for team in teams:
            self.af.add_team(team["team_name"])
        
        initial_user_state = self.get_initial_user_state()
                
        results_service = DebateResultsService()

        return DebateState(
            af=self.af,
            topic=self.config.topic,
            vector_db=self.vector_db,
            tavily_tool=self.tavily_tool,
            team_llm=self.team_llm,
            teams=teams,
            user=initial_user_state,
            round=0,
            max_rounds=self.config.max_rounds,
            audience_initial_votes=[],
            audience_final_votes=[],
            config_id=self.config.id,
            argument_log=[],
            tgs_snapshots=[],
            domain_goal_pairs=[],
            results_service=results_service,
            metrics_aggregator=MetricsAggregator()
        )
    
    def save_results(self, results: Dict[str, Any]) -> None:
        import sys
        try:
            output_path = Path(self.config.output_file)

            # Ensure the path is absolute
            if not output_path.is_absolute():
                output_path = output_path.absolute()

            # On Windows, use extended-length path syntax for paths >= 260 chars
            # This enables long path support (paths up to 32,767 characters)
            if sys.platform == 'win32' and len(str(output_path)) >= 260:
                # Convert to extended-length path format
                output_path_str = f"\\\\?\\{output_path}"
                parent_path_str = f"\\\\?\\{output_path.parent}"
            else:
                output_path_str = str(output_path)
                parent_path_str = str(output_path.parent)

            # Create parent directory if it doesn't exist
            Path(parent_path_str).mkdir(parents=True, exist_ok=True)

            # Verify parent directory was created
            if not Path(parent_path_str).exists():
                raise IOError(f"Failed to create parent directory: {output_path.parent}")

            # Write results to file
            with open(output_path_str, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            print(f"💾 Results saved to: {output_path}")
        except Exception as e:
            print(f"❌ ERROR: Failed to save results to {self.config.output_file}")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {e}")
            print(f"   Output path: {output_path if 'output_path' in locals() else 'N/A'}")
            print(f"   Path length: {len(str(output_path)) if 'output_path' in locals() else 'N/A'} characters")
            print(f"   Parent dir: {output_path.parent if 'output_path' in locals() else 'N/A'}")
            print(f"   Parent exists: {output_path.parent.exists() if 'output_path' in locals() and output_path.parent else 'N/A'}")

            # If this is a long path issue on Windows, provide specific guidance
            if sys.platform == 'win32' and 'output_path' in locals() and len(str(output_path)) >= 260:
                print(f"   ⚠️  WARNING: Path length ({len(str(output_path))}) exceeds Windows MAX_PATH limit (260)")
                print(f"   💡 Using extended-length path format (\\\\?\\) to bypass limit")

            raise
