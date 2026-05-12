from typing import List, Optional
from dataclasses import dataclass
from src.reasoning.godsaf.godsaf_service import Domain, Goal, UGNEntry

@dataclass
class UserGuidance:
    """Guidance provided to the user for argument creation"""
    recommended_domains: List[Domain]
    recommended_goals: List[Goal]
    primary_ugns: Optional[List[UGNEntry]] = None  # New: direct access to UGNs
    secondary_ugns: Optional[List[UGNEntry]] = None  # New: direct access to UGNs
    strategic_explanation: str = ""
    current_situation_analysis: str = ""
    examples: List[str] = None
    priority_level: str = "medium"  # "high", "medium", "low"
    opponent_analysis: str = ""
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []


@dataclass
class ArgumentSuggestion:
    """Suggestion for argument structure"""
    target_domains: List[str]
    target_goals: List[str]
    reasoning: str
    potential_attacks: List[str]
    expected_impact: str


@dataclass
class ArgumentStrategy:
    """LLM-generated argument strategy"""
    argument_text: str
    reasoning: str
    strategic_rationale: str
    targets_domains: List[str]
    supports_goals: List[str]
