from typing_extensions import TypedDict, Sequence, Annotated, List
from src.model.model import Decision, AudienceMember, TeamMember, Transcript


class DebateState(TypedDict):
    topic: str
    initial_scores: List[Decision]
    final_scores: List[Decision]
    transcript: List[Transcript]
    round: int
    audience_members: List[AudienceMember]
    proposing_members: List[TeamMember]
    opposing_members: List[TeamMember]
