from langgraph.graph import StateGraph, START, END
from src.tutor.emotional_appeal_node import emotional_feedback_node
from src.tutor.relevance_node import relevance_feedback_node
from src.tutor.evidence_support_node import evidence_feedback_node
from src.tutor.style_clarity_node import style_clarity_feedback_node
from src.tutor.tutur_summarize import summary_feedback_node
from src.tutor.state import TutorState


def creat_tutor():
    workflow = StateGraph(TutorState)

    workflow.add_node("relevance_feedback_node", relevance_feedback_node)
    workflow.add_node("evidence_feedback_node", evidence_feedback_node)
    workflow.add_node("emotional_feedback_node", emotional_feedback_node)
    workflow.add_node("style_clarity_feedback_node", style_clarity_feedback_node)
    workflow.add_node("complex_feedback_node", summary_feedback_node)

    workflow.add_edge(START, "relevance_feedback_node")
    workflow.add_edge(START, "evidence_feedback_node")
    workflow.add_edge(START, "emotional_feedback_node")
    workflow.add_edge(START, "style_clarity_feedback_node")
    workflow.add_edge("relevance_feedback_node", "complex_feedback_node")
    workflow.add_edge("evidence_feedback_node", "complex_feedback_node")
    workflow.add_edge("emotional_feedback_node", "complex_feedback_node")
    workflow.add_edge("style_clarity_feedback_node", "complex_feedback_node")
    workflow.add_edge("complex_feedback_node", END)

    return workflow
