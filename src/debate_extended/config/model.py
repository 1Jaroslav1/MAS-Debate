from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ToTConfig:
    """Configuration for Tree of Thoughts architecture"""
    num_analysis_branches: int = 3
    num_argument_variations: int = 3
    pruning_strategy: str = "top_k"
    analysis_pruning_k: int = 3
    argument_pruning_k: int = 5
    search_algorithm: str = "best_first"
    enable_fast_scoring: bool = True
    diversity_weight: float = 0.2


@dataclass
class MemberConfig:
    name: str
    education: List[str]
    experience: List[str]
    expertise_domains: List[str]
    current_role: str
    thinking_style: str
    communication_style: str
    argumentation_preference: str
    core_values: List[str]
    philosophical_stance: str
    risk_tolerance: str
    decision_making_style: str
    preferred_evidence_types: List[str]
    typical_counterargument_approach: str
    industry_background: str
    cultural_background: str
    notable_biases: List[str]
    perspective: str
    max_iterations: int = 3
    use_personalization: bool = True
    use_context_analysis: bool = True
    knowledge_active: bool = False
    knowledge_use_rag: bool = False
    knowledge_use_web_search: bool = False
    evaluation_active: bool = True


@dataclass
class TeamConfig:
    team_name: str
    team_type: str
    perspective_description: str
    priority_aspects: List[str]
    evidence_preferences: List[str]
    counterargument_strategy: str
    rhetorical_emphasis: str
    focus_keywords: List[str]
    avoid_keywords: List[str]
    viewpoint_orientation: str
    interests_and_concerns: List[str]
    typical_arguments: List[str]
    members: List[MemberConfig]
    architecture: str = "godsaf"
    tot_config: Optional[ToTConfig] = None


@dataclass
class AudienceConfig:
    listeners: Optional[List[Dict[str, Any]]] = None
    enable_comparative_evaluation: bool = True
    enable_performance_scoring: bool = True
    max_domains: int = 6
    max_goals: int = 6


@dataclass
class DebateConfig:
    id: Optional[str]
    topic: str
    max_rounds: int
    teams: List[TeamConfig]
    audience: AudienceConfig
    output_file: str = "debate_results.json"
    include_user_interaction: bool = False
    user_team_name: str = "t_user"
    team_llm_model: Optional[str] = None
