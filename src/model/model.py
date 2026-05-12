from enum import Enum

from typing_extensions import TypedDict, List


class Decision(TypedDict):
    name: str
    value: str


class AudienceMember(TypedDict):
    name: str
    interests: List[str]
    work_experience: List[str]
    personality: List[str]


class TeamRole(str, Enum):
    PROPOSING = 'PROPOSING'
    OPPOSING = 'OPPOSING'
    CHAIRMAN = 'CHAIRMAN'
    AUDIENCE = 'AUDIENCE'
    USER = 'USER'


class TeamMember(TypedDict):
    name: str
    expertise: str
    description: str


class Transcript(TypedDict):
    speaker: TeamMember
    team_role: TeamRole
    text: str


class AudienceProfile(TypedDict):
    audience_members: List[AudienceMember]
