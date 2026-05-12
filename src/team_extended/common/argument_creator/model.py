from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from src.team_extended.common.team_member import MemberProfile, TeamFocusContext, RetrievedDocument


class ArgumentContext(BaseModel):
    topic: str = Field(description="Main topic for argument creation")
    domains: List[str] = Field(description="Relevant domains")
    goals: List[str] = Field(description="Argument goals")
    domain_goal_connections: Optional[List[tuple]] = Field(default=[], description="Domain-goal connection pairs from UGNs")
    member_profile: MemberProfile = Field(description="Profile of the team member creating the argument")
    team_focus: TeamFocusContext = Field(description="Team's focus context and stance for the debate")
    previous_arguments: List[str] = Field(default=[], description="Previously created arguments")
    reviewer_feedback: Optional[str] = Field(default=None, description="Feedback from reviewer")
    iteration_count: int = Field(default=1, description="Current iteration number")
    max_iterations: int = Field(default=3, description="Maximum iterations allowed")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ArgumentStrategy(BaseModel):
    approach: str = Field(description="Strategic approach (supportive, critical, balanced)")
    rhetorical_focus: str = Field(description="Primary rhetorical strategy (logos, pathos, ethos)")
    logical_structure: str = Field(description="Argument structure (deductive, inductive, mixed)")
    evidence_priorities: List[str] = Field(description="Priority order for evidence types")
    counterargument_handling: str = Field(description="Strategy for addressing counterarguments")
    # Member-specific strategy elements
    personalization_notes: str = Field(description="How the strategy reflects the member's profile and style")
    # Team focus strategy elements
    perspective_alignment: str = Field(description="How the strategy aligns with team's assigned perspective")
    focus_emphasis: List[str] = Field(description="Priority aspects from team focus that will be emphasized")
    evidence_perspective_filter: str = Field(description="How evidence selection supports the team's perspective")


class ArgumentDraft(BaseModel):
    main_thesis: str = Field(description="Central thesis statement")
    supporting_points: List[str] = Field(description="Key supporting arguments")
    evidence_integration: str = Field(description="How evidence is woven throughout")
    counterargument_responses: List[str] = Field(description="Responses to potential objections")
    conclusion: str = Field(description="Strong concluding statement")
    full_argument: str = Field(description="Complete formatted argument")
    member_voice_notes: str = Field(description="Notes on how the argument reflects the member's unique voice and perspective")
    domain_alignment_check: str = Field(default="", description="Confirmation of which strategic domains are covered in the argument")


class SelfAssessment(BaseModel):
    overall_score: float = Field(description="Overall argument quality score (1-10)")
    authenticity_score: float = Field(description="How authentic the argument sounds for this member (1-10)")
    perspective_alignment_score: float = Field(description="How well the argument represents the team's perspective (1-10)")
    focus_compliance_score: float = Field(description="How well it emphasizes required priority aspects (1-10)")
    logic_score: float = Field(description="Logical consistency and structure (1-10)")
    evidence_score: float = Field(description="Evidence quality and perspective support (1-10)")
    persuasiveness_score: float = Field(description="Persuasiveness for the assigned perspective (1-10)")
    feedback_response_score: float = Field(description="How well it addresses reviewer feedback (1-10)")
    key_strengths: List[str] = Field(description="Main strengths of the argument")
    areas_for_improvement: List[str] = Field(description="Areas that could be improved")
    authenticity_check: bool = Field(description="Does this truly sound like the member would write it")
    perspective_alignment_check: bool = Field(description="Does this effectively serve the team's perspective")
    ready_for_review: bool = Field(description="Is the argument ready for external review")
    assessment_summary: str = Field(description="Brief overall assessment including perspective effectiveness")


class ArgumentCreatorState(BaseModel):
    context: ArgumentContext
    retrieved_knowledge: List[RetrievedDocument] = Field(default_factory=list)
    strategy: Optional[ArgumentStrategy] = None
    draft: Optional[ArgumentDraft] = None
    self_assessment: Optional[SelfAssessment] = None
    final_argument: Optional[str] = None
    needs_revision: bool = False
    revision_notes: List[str] = Field(default_factory=list)
    token_usage: List[dict] = Field(default_factory=list)  # Track token usage per phase
