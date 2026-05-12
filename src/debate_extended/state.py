from typing import List, TypedDict, Optional, Dict, Any
from langchain_core.language_models.chat_models import BaseChatModel
from src.hub.search_tool_hub import TavilySearchResults
from langgraph.store.memory import InMemoryStore
from src.reasoning.godsaf.godsaf_service import GoDsAFService
from src.team_extended.state import TeamMember
from src.team_extended.common.evaluator.evaluator import EvaluationConfig
from src.team_extended.common.knowledge.vector_db_manager import VectorDBManager
from src.team_extended.common.team_member import TeamFocusContext
from src.team_extended.common.state import TeamMemberState
from src.team_extended.user_guidance.user_node import UserInteractionState
from src.team_extended.common.metrics.execution_metrics import MetricsAggregator


class Team(TypedDict):
    team_name: str
    team_focus: TeamFocusContext
    team_members: List[TeamMember]
    evaluation_config: EvaluationConfig
    store: InMemoryStore
    architecture: str
    tot_config: Optional[Dict[str, Any]]
    

class UserState(TypedDict):
    team_name: str
    user_interaction_state: Optional[UserInteractionState]


class DebateState(TypedDict):
    af: GoDsAFService
    topic: str
    vector_db: VectorDBManager
    tavily_tool: TavilySearchResults
    team_llm: BaseChatModel
    teams: List[Team]
    user: UserState
    round: int
    max_rounds: int
    # Audience components
    audience_initial_votes: List[Dict[str, str]]
    audience_final_votes: List[Dict[str, str]]
    # Enhanced audience components (optional)
    audience_initial_evaluations: Optional[List[Dict[str, Any]]]
    audience_final_votes_enhanced: Optional[List[Dict[str, Any]]]
    # Initial voting metrics (with initial_ prefix)
    initial_vote_counts: Optional[Dict[str, int]]
    initial_winning_team: Optional[str]
    initial_margin_of_victory: Optional[int]
    # Final voting metrics (with final_ prefix)
    final_vote_counts: Optional[Dict[str, int]]
    final_winning_team: Optional[str]
    final_margin_of_victory: Optional[int]
    final_vote_changes: Optional[Dict[str, Any]]
    # Deprecated fields (kept for backwards compatibility)
    winning_team: Optional[str]
    vote_counts: Optional[Dict[str, int]]
    margin_of_victory: Optional[int]
    team_performances: Optional[Dict[str, Dict[str, Any]]]
    # Results aggregation
    config_id: Optional[str]
    argument_log: List[Dict[str, Any]]
    tgs_snapshots: List[Dict[str, Any]]
    domain_goal_pairs: Optional[List[Dict[str, str]]]
    results_service: Any
    # Execution metrics
    metrics_aggregator: MetricsAggregator
