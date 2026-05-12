from typing_extensions import TypedDict, NotRequired
from langchain_core.runnables import RunnableConfig
from typing import Optional, Dict, Any, List
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.store.memory import InMemoryStore

from src.reasoning.godsaf.godsaf_service import GoDsAFService
from src.team_extended.common.argument_creator.model import (
    ArgumentContext,
    ArgumentCreatorState,
)
from src.team_extended.common.evaluator.evaluator import EvaluationConfig
from src.team_extended.common.evaluator.model import UnifiedArgumentEvaluation
from src.team_extended.common.knowledge.model import KnowledgeRetrievalState, SearchContext, KnowledgeNodeConfig
from src.team_extended.common.evaluator.model import EvaluationNodeConfig
from src.team_extended.common.knowledge.vector_db_manager import VectorDBManager
from src.team_extended.common.team_member import StrategyRecommendation
from src.team_extended.common.metrics.execution_metrics import MetricsAggregator, NodeExecutionMetrics
from src.team_extended.common.metrics.token_tracking import NodeTokenUsage, TokenUsageAggregator


class TeamMemberState(TypedDict):
    af: GoDsAFService
    topic: str
    team_member_name: str
    team_name: str
    # used for chain of thought evaluation
    analysis_result: NotRequired[Optional[Dict[str, Any]]]
    # used for godsaf analysis
    strategy_recommendation: NotRequired[StrategyRecommendation]
    knowledge_retrival_results: NotRequired[KnowledgeRetrievalState]
    argument_creator_results: NotRequired[ArgumentCreatorState]
    evaluator_results: NotRequired[UnifiedArgumentEvaluation]

    iteration_number: int
    architecture: str

    vector_db: VectorDBManager
    tavily_tool: TavilySearchResults
    store: InMemoryStore

    analyser_llm: BaseChatModel

    # knowledge retrieval parameters
    knowledge_retrival_context: SearchContext
    knowledge_retrival_llm: BaseChatModel
    knowledge_retrival_config: Optional[RunnableConfig] = None

    # argument creation parameters
    argument_creation_context: ArgumentContext
    argument_creation_llm: BaseChatModel
    argument_creation_config: Optional[RunnableConfig] = None

    # evaluation
    evaluation_config: EvaluationConfig
    evaluation_llm: BaseChatModel
    candidate_id: str

    # execution metrics - stores metrics for each node
    node_execution_metrics: NotRequired[Dict[str, NodeExecutionMetrics]]

    # per-node token usage tracking
    node_token_usage: NotRequired[Dict[str, NodeTokenUsage]]
    token_aggregator: NotRequired[TokenUsageAggregator]
    metrics_aggregator: MetricsAggregator

    # round number from debate state
    round: NotRequired[int]

    knowledge_node_config: NotRequired[Optional[KnowledgeNodeConfig]]
    evaluation_node_config: NotRequired[Optional[EvaluationNodeConfig]]

    tot_config: NotRequired[Optional[Dict[str, Any]]]
    tot_analysis_branches: NotRequired[List[Dict[str, Any]]]
    tot_argument_variations: NotRequired[List[Dict[str, Any]]]
    tot_tree_metadata: NotRequired[Dict[str, Any]]

    finalized_argument_log_entry: NotRequired[Optional[Dict[str, Any]]]
