from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict as ExtTypedDict
from pydantic import BaseModel, Field
import uuid

from src.team_extended.common.team_member import MemberProfile, RetrievedDocument, TeamFocusContext


class SearchContext(BaseModel):
    """Input context for knowledge retrieval with team integration"""

    topic: str = Field(description="Main topic for knowledge retrieval")
    domains: List[str] = Field(description="Relevant domains to search within")
    goals: List[str] = Field(description="Goals for the retrieved knowledge")
    domain_goal_connections: Optional[List[tuple]] = Field(
        default=[], description="Domain-goal connection pairs from UGNs"
    )
    previous_arguments: Optional[List[str]] = Field(
        default=[], description="Previously generated arguments"
    )
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Session ID for memory"
    )
    perspective: Optional[str] = Field(
        default=None, description="Current perspective/angle"
    )
    iteration_count: int = Field(default=0, description="Current iteration number")
    excluded_sources: List[str] = Field(default=[], description="Sources to exclude")

    member_profile: Optional[MemberProfile] = Field(
        default=None, description="Team member profile for personalized search"
    )
    team_focus: Optional[TeamFocusContext] = Field(
        default=None, description="Team focus context for perspective-aware search"
    )


class SearchQuery(BaseModel):
    """Individual search query with metadata and team context"""

    query: str = Field(description="The search query string")
    domain: str = Field(description="Target domain for this query")
    target_goal: Optional[str] = Field(
        default=None, description="Specific goal this query targets"
    )
    search_type: str = Field(
        description="Type of search: 'exploratory', 'supporting', 'contradicting'"
    )
    priority: float = Field(default=1.0, description="Priority score for this query")
    perspective_modifier: Optional[str] = Field(
        default=None, description="Perspective modifier"
    )

    member_expertise_focus: Optional[str] = Field(
        default=None, description="Member expertise area this query targets"
    )
    team_perspective_alignment: Optional[str] = Field(
        default=None, description="How this query aligns with team perspective"
    )
    evidence_type_preference: Optional[str] = Field(
        default=None, description="Preferred evidence type for this member"
    )


class KnowledgeMemory(ExtTypedDict):
    """Memory structure for knowledge retrieval with team context"""

    query: str
    documents: List[Dict[str, Any]]
    timestamp: str
    domains: List[str]
    goals: List[str]
    perspective: Optional[str]
    session_id: str
    retrieved_sources: List[str]
    member_name: Optional[str]
    team_type: Optional[str]
    search_adaptations: Optional[List[str]]


class KnowledgeNodeConfig(BaseModel):
    """Configuration for knowledge retrieval node behavior"""

    active: bool = Field(
        default=False,
        description="Controls whether knowledge retrieval node executes"
    )
    use_rag: bool = Field(
        default=False,
        description="Enable RAG search against vector database"
    )
    use_web_search: bool = Field(
        default=False,
        description="Enable web search via Tavily"
    )

    def is_effective_active(self) -> bool:
        """Check if config is effectively active"""
        return self.active and (self.use_rag or self.use_web_search)

    def validate_config(self) -> List[str]:
        """Return list of validation warnings"""
        warnings = []
        if self.active and not self.use_rag and not self.use_web_search:
            warnings.append(
                "knowledge_node_config.active=True but both use_rag and use_web_search are False. "
                "Knowledge retrieval will be skipped."
            )
        return warnings


class KnowledgeRetrievalState(BaseModel):
    """State for knowledge retrieval workflow with team integration"""

    context: SearchContext
    search_queries: List[SearchQuery] = []
    retrieved_documents: List[RetrievedDocument] = []
    current_query_index: int = 0
    memory_items: List[Dict[str, Any]] = []
    llm_input_messages: Optional[List[Any]] = None
    session_id: str = ""
    member_adapted_queries: List[SearchQuery] = []
    team_filtered_documents: List[RetrievedDocument] = []
    expertise_coverage: Dict[str, int] = {}
