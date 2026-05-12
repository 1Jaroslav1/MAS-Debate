from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from dataclasses import dataclass
from src.reasoning.godsaf.godsaf_service import Domain, Goal, UGNEntry

class TeamFocusContext(BaseModel):
    """Team-specific focus context for different perspectives and viewpoints"""

    team_type: str = Field(
        description="Team type/perspective (e.g., 'stakeholder', 'employee', 'user', 'military', 'civil')"
    )
    perspective_description: str = Field(
        description="Detailed description of this team's viewpoint and concerns"
    )
    priority_aspects: List[str] = Field(
        description="Key areas this team should emphasize"
    )
    evidence_preferences: List[str] = Field(
        description="Types of evidence that support this team's perspective"
    )
    counterargument_strategy: str = Field(
        description="How this team should handle opposing views"
    )
    rhetorical_emphasis: str = Field(
        description="Primary rhetorical focus: 'logical', 'emotional', or 'credibility'"
    )
    focus_keywords: List[str] = Field(
        default=[], description="Keywords to emphasize in searches and arguments"
    )
    avoid_keywords: List[str] = Field(
        default=[], description="Keywords to avoid or counter"
    )

    # New flexible approach fields
    viewpoint_orientation: str = Field(
        description="How this team approaches the topic (e.g., 'supportive', 'critical', 'analytical', 'protective')"
    )
    interests_and_concerns: List[str] = Field(
        description="Primary interests and concerns of this team type"
    )
    typical_arguments: List[str] = Field(
        default=[], description="Types of arguments this team typically makes"
    )

    def get_perspective_descriptor(self) -> str:
        """Get human-readable perspective description"""
        return f"arguing from {self.team_type} perspective focusing on {self.perspective_description}"


class MemberProfile(BaseModel):
    """Team member profile with characteristics that influence argument style"""

    name: str = Field(description="Member name/identifier")

    # Professional background
    education: List[str] = Field(
        description="Educational background (degrees, institutions)"
    )
    experience: List[str] = Field(description="Professional experience areas")
    expertise_domains: List[str] = Field(description="Areas of deep expertise")
    current_role: str = Field(description="Current professional role")

    # Cognitive style and preferences
    thinking_style: str = Field(description="Analytical/intuitive/systematic/creative")
    communication_style: str = Field(
        description="Direct/diplomatic/academic/conversational"
    )
    argumentation_preference: str = Field(
        description="Evidence-heavy/story-driven/logical/emotional"
    )

    # Beliefs and values
    core_values: List[str] = Field(
        description="Fundamental values that guide decision-making"
    )
    philosophical_stance: str = Field(
        description="General worldview or philosophical approach"
    )
    risk_tolerance: str = Field(description="Conservative/moderate/aggressive")

    # Behavioral patterns
    decision_making_style: str = Field(
        description="Quick/deliberate/consensus-seeking/data-driven"
    )
    preferred_evidence_types: List[str] = Field(
        description="Research/case studies/expert opinions/statistics"
    )
    typical_counterargument_approach: str = Field(
        description="How they typically handle opposing views"
    )

    # Contextual factors
    industry_background: Optional[str] = Field(
        default=None, description="Primary industry experience"
    )
    cultural_background: Optional[str] = Field(
        default=None, description="Cultural influences on perspective"
    )
    notable_biases: List[str] = Field(
        default=[], description="Known cognitive biases or blind spots"
    )

    # Personalization control
    use_personalization: bool = Field(
        default=True, description="Whether to use persona information in argument creation"
    )
    use_context_analysis: bool = Field(
        default=True, description="Whether to perform context analysis before argument construction"
    )


class ArgumentContext(BaseModel):
    """Input context for argument creation"""

    topic: str = Field(description="Main topic for argument creation")
    domains: List[str] = Field(description="Relevant domains")
    goals: List[str] = Field(description="Argument goals")
    perspective: Optional[str] = Field(
        default="balanced", description="Argument perspective"
    )

    # Member profile for personalization
    member_profile: MemberProfile = Field(
        description="Profile of the team member creating the argument"
    )

    # NEW: Team focus context for debate positioning
    team_focus: TeamFocusContext = Field(
        description="Team's focus context and stance for the debate"
    )

    previous_arguments: List[str] = Field(
        default=[], description="Previously created arguments"
    )
    reviewer_feedback: Optional[str] = Field(
        default=None, description="Feedback from reviewer"
    )
    iteration_count: int = Field(default=1, description="Current iteration number")
    max_iterations: int = Field(default=3, description="Maximum iterations allowed")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ArgumentStrategy(BaseModel):
    """Argument strategy output"""

    approach: str = Field(
        description="Strategic approach (supportive, critical, balanced)"
    )
    rhetorical_focus: str = Field(
        description="Primary rhetorical strategy (logos, pathos, ethos)"
    )
    logical_structure: str = Field(
        description="Argument structure (deductive, inductive, mixed)"
    )
    evidence_priorities: List[str] = Field(
        description="Priority order for evidence types"
    )
    counterargument_handling: str = Field(
        description="Strategy for addressing counterarguments"
    )

    # Member-specific strategy elements
    personalization_notes: str = Field(
        description="How the strategy reflects the member's profile and style"
    )

    # Team focus strategy elements
    perspective_alignment: str = Field(
        description="How the strategy aligns with team's assigned perspective"
    )
    focus_emphasis: List[str] = Field(
        description="Priority aspects from team focus that will be emphasized"
    )
    evidence_perspective_filter: str = Field(
        description="How evidence selection supports the team's perspective"
    )


class ArgumentDraft(BaseModel):
    """Complete argument draft"""

    main_thesis: str = Field(description="Central thesis statement")
    supporting_points: List[str] = Field(description="Key supporting arguments")
    evidence_integration: str = Field(description="How evidence is woven throughout")
    counterargument_responses: List[str] = Field(
        description="Responses to potential objections"
    )
    conclusion: str = Field(description="Strong concluding statement")
    full_argument: str = Field(description="Complete formatted argument")

    # NEW: Member-specific elements
    member_voice_notes: str = Field(
        description="Notes on how the argument reflects the member's unique voice and perspective"
    )


class SelfAssessment(BaseModel):
    """Structured self-assessment output"""

    overall_score: float = Field(description="Overall argument quality score (1-10)")
    authenticity_score: float = Field(
        description="How authentic the argument sounds for this member (1-10)"
    )
    perspective_alignment_score: float = Field(
        description="How well the argument represents the team's perspective (1-10)"
    )
    focus_compliance_score: float = Field(
        description="How well it emphasizes required priority aspects (1-10)"
    )
    logic_score: float = Field(description="Logical consistency and structure (1-10)")
    evidence_score: float = Field(
        description="Evidence quality and perspective support (1-10)"
    )
    persuasiveness_score: float = Field(
        description="Persuasiveness for the assigned perspective (1-10)"
    )
    feedback_response_score: float = Field(
        description="How well it addresses reviewer feedback (1-10)"
    )

    key_strengths: List[str] = Field(description="Main strengths of the argument")
    areas_for_improvement: List[str] = Field(description="Areas that could be improved")
    authenticity_check: bool = Field(
        description="Does this truly sound like the member would write it"
    )
    perspective_alignment_check: bool = Field(
        description="Does this effectively serve the team's perspective"
    )
    ready_for_review: bool = Field(
        description="Is the argument ready for external review"
    )
    assessment_summary: str = Field(
        description="Brief overall assessment including perspective effectiveness"
    )

class RetrievedDocument(BaseModel):
    """Retrieved document with metadata and team relevance"""

    content: str = Field(description="Document content")
    title: str = Field(description="Document title")
    source: str = Field(description="Source of the document (URL or document ID)")
    relevance_score: float = Field(description="Relevance score")
    timestamp: datetime = Field(default_factory=datetime.now)
    domain: str = Field(default="", description="Domain of the document")
    goal: str = Field(default="", description="Goal this document addresses")
    embedding_id: Optional[str] = Field(
        default=None, description="ID in vector database"
    )
    member_expertise_score: float = Field(
        default=0.0, description="How well this document matches member's expertise"
    )
    team_perspective_score: float = Field(
        default=0.0, description="How well this document supports team perspective"
    )
    evidence_type_match: bool = Field(
        default=False,
        description="Whether document matches member's preferred evidence types",
    )

class ArgumentCreatorState(BaseModel):
    """State for argument creator workflow"""

    context: ArgumentContext
    retrieved_knowledge: List[RetrievedDocument] = []
    strategy: Optional[ArgumentStrategy] = None
    draft: Optional[ArgumentDraft] = None
    self_assessment: Optional[SelfAssessment] = None
    final_argument: Optional[str] = None
    needs_revision: bool = False
    revision_notes: List[str] = []

@dataclass
class StrategyRecommendation:
    """Represents a strategy recommendation for new arguments"""

    team: str
    primary_ugns: List[UGNEntry]
    secondary_ugns: List[UGNEntry]
    analysis_summary: str
    
    # Legacy properties for backward compatibility - will be deprecated
    @property
    def recommended_domains(self) -> List[Domain]:
        """Extract domains from UGNs (legacy - use primary_ugns/secondary_ugns directly)"""
        domains = []
        seen_domains = set()
        for ugn in self.primary_ugns + self.secondary_ugns:
            if ugn.domain.name not in seen_domains:
                domains.append(ugn.domain)
                seen_domains.add(ugn.domain.name)
        return domains[:2]  # Limit to max 2 domains
    
    @property
    def recommended_goals(self) -> List[Goal]:
        """Extract goals from UGNs (legacy - use primary_ugns/secondary_ugns directly)"""
        goals = []
        seen_goals = set()
        for ugn in self.primary_ugns + self.secondary_ugns:
            if ugn.goal.name not in seen_goals:
                goals.append(ugn.goal)
                seen_goals.add(ugn.goal.name)
        return goals[:2]  # Limit to max 2 goals

class TeamFocusContext(BaseModel):
    """Team-specific focus context for different perspectives and viewpoints"""

    team_type: str = Field(
        description="Team type/perspective (e.g., 'stakeholder', 'employee', 'user', 'military', 'civil')"
    )
    perspective_description: str = Field(
        description="Detailed description of this team's viewpoint and concerns"
    )
    priority_aspects: List[str] = Field(
        description="Key areas this team should emphasize"
    )
    evidence_preferences: List[str] = Field(
        description="Types of evidence that support this team's perspective"
    )
    counterargument_strategy: str = Field(
        description="How this team should handle opposing views"
    )
    rhetorical_emphasis: str = Field(
        description="Primary rhetorical focus: 'logical', 'emotional', or 'credibility'"
    )
    focus_keywords: List[str] = Field(
        default=[], description="Keywords to emphasize in searches and arguments"
    )
    avoid_keywords: List[str] = Field(
        default=[], description="Keywords to avoid or counter"
    )

    # New flexible approach fields
    viewpoint_orientation: str = Field(
        description="How this team approaches the topic (e.g., 'supportive', 'critical', 'analytical', 'protective')"
    )
    interests_and_concerns: List[str] = Field(
        description="Primary interests and concerns of this team type"
    )
    typical_arguments: List[str] = Field(
        default=[], description="Types of arguments this team typically makes"
    )

    def get_perspective_descriptor(self) -> str:
        """Get human-readable perspective description"""
        return f"arguing from {self.team_type} perspective focusing on {self.perspective_description}"


class MemberProfile(BaseModel):
    """Team member profile with characteristics that influence argument style"""

    name: str = Field(description="Member name/identifier")

    # Professional background
    education: List[str] = Field(
        description="Educational background (degrees, institutions)"
    )
    experience: List[str] = Field(description="Professional experience areas")
    expertise_domains: List[str] = Field(description="Areas of deep expertise")
    current_role: str = Field(description="Current professional role")

    # Cognitive style and preferences
    thinking_style: str = Field(description="Analytical/intuitive/systematic/creative")
    communication_style: str = Field(
        description="Direct/diplomatic/academic/conversational"
    )
    argumentation_preference: str = Field(
        description="Evidence-heavy/story-driven/logical/emotional"
    )

    # Beliefs and values
    core_values: List[str] = Field(
        description="Fundamental values that guide decision-making"
    )
    philosophical_stance: str = Field(
        description="General worldview or philosophical approach"
    )
    risk_tolerance: str = Field(description="Conservative/moderate/aggressive")

    # Behavioral patterns
    decision_making_style: str = Field(
        description="Quick/deliberate/consensus-seeking/data-driven"
    )
    preferred_evidence_types: List[str] = Field(
        description="Research/case studies/expert opinions/statistics"
    )
    typical_counterargument_approach: str = Field(
        description="How they typically handle opposing views"
    )

    # Contextual factors
    industry_background: Optional[str] = Field(
        default=None, description="Primary industry experience"
    )
    cultural_background: Optional[str] = Field(
        default=None, description="Cultural influences on perspective"
    )
    notable_biases: List[str] = Field(
        default=[], description="Known cognitive biases or blind spots"
    )

    # Personalization control
    use_personalization: bool = Field(
        default=True, description="Whether to use persona information in argument creation"
    )
    use_context_analysis: bool = Field(
        default=True, description="Whether to perform context analysis before argument construction"
    )

