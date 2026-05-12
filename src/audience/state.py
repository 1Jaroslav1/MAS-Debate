from typing_extensions import TypedDict, List
from typing import Annotated

from src.model.model import Decision, Transcript


def topic_reducer(existing: str, new: str) -> str:
    return existing if existing else new


def transcript_reducer(existing: List[Transcript], new: List[Transcript]) -> List[Transcript]:
    return existing if existing else new


def unique_append(existing: List[dict], new: List[dict]) -> List[dict]:
    existing_set = {frozenset(item.items()) for item in existing}
    for item in new:
        if frozenset(item.items()) not in existing_set:
            existing.append(item)
    return existing


class AudienceState(TypedDict):
    topic: Annotated[str, topic_reducer]
    transcript: Annotated[List[Transcript], transcript_reducer]
    initial_scores: Annotated[List[Decision], unique_append]
    final_scores: Annotated[List[Decision], unique_append]
