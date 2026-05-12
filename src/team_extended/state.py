from typing import List, TypedDict, Any, Dict, Optional
from src.reasoning.godsaf.godsaf_service import GoDsAFService
from src.team_extended.common.argument_creator.model import ArgumentContext
from src.team_extended.common.evaluator.evaluator import EvaluationConfig
from src.team_extended.common.knowledge.model import SearchContext, KnowledgeNodeConfig
from src.team_extended.common.evaluator.model import EvaluationNodeConfig
from src.team_extended.common.knowledge.vector_db_manager import VectorDBManager
from langgraph.store.memory import InMemoryStore
from langchain_community.tools.tavily_search import TavilySearchResults
from src.team_extended.common.team_member import MemberProfile, TeamFocusContext
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.metrics.execution_metrics import MetricsAggregator

class TeamState(TypedDict):
    af: GoDsAFService
    topic: str
    evaluation_config: EvaluationConfig

    vector_db: VectorDBManager
    tavily_tool: TavilySearchResults
    store: InMemoryStore
    knowledge_retrival_llm: Any
    argument_creation_llm: Any
    evaluation_llm: Any
    
    team_name: str
    team_focus: TeamFocusContext
    team_member_states: List[TeamMemberState]
    round: int
    tgs_snapshots: List[Dict[str, Any]]
    argument_log: List[Dict[str, Any]]
    metrics_aggregator: MetricsAggregator

class TeamMember(TypedDict):
    name: str
    member_profile: MemberProfile
    knowledge_retrival_context: SearchContext
    argument_creation_context: ArgumentContext
    knowledge_node_config: Optional[KnowledgeNodeConfig]
    evaluation_node_config: Optional[EvaluationNodeConfig]
