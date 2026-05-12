from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.hub import gpt_4o_mini
from src.tutor.state import TutorState


class ComplexFeedbackOutput(BaseModel):
    overall_score: int = Field(
        description="Aggregated overall score (1-10) considering all evaluation dimensions."
    )
    detailed_feedback: str = Field(
        description="A comprehensive summary of the evaluations, highlighting strengths, weaknesses, and actionable recommendations."
    )


def summary_feedback_node(state: TutorState) -> TutorState:
    summary_feedback_prompt = PromptTemplate(
        template="""
            You are a **Comprehensive Feedback Summarizer Agent**. You have received the following feedback from four different evaluation agents:

            Relevance Analysis:
              - Score: {relevance_score}
              - Feedback: {relevance_feedback}

            Evidence Support Analysis:
              - Score: {evidence_score}
              - Feedback: {evidence_feedback}

            Emotional Appeal Analysis:
              - Score: {emotional_score}
              - Feedback: {emotional_feedback}

            Style & Clarity Analysis:
              - Score: {style_score}
              - Feedback: {style_feedback}

            Based on the above evaluations, please provide:
            1. An overall aggregated score (1-10) that reflects the combined strengths and weaknesses across all dimensions.
            2. A comprehensive summary that synthesizes the individual feedback into detailed, actionable recommendations for improvement.

            Return your response in JSON format with the following keys:
            - "overall_score": The aggregated overall score.
            - "detailed_feedback": A comprehensive summary of the feedback.
        """,
        input_variables=[
            "relevance_score", "relevance_feedback",
            "evidence_score", "evidence_feedback",
            "emotional_score", "emotional_feedback",
            "style_score", "style_feedback",
        ]
    )

    summary_feedback_chain = summary_feedback_prompt | gpt_4o_mini.with_structured_output(ComplexFeedbackOutput)
    summary_result = summary_feedback_chain.invoke({
        "relevance_score": state["relevance_analysis"]["score"],
        "relevance_feedback": state["relevance_analysis"]["feedback"],
        "evidence_score": state["evidence_support_analysis"]["score"],
        "evidence_feedback": state["evidence_support_analysis"]["feedback"],
        "emotional_score": state["emotional_appeal_analysis"]["score"],
        "emotional_feedback": state["emotional_appeal_analysis"]["feedback"],
        "style_score": state["style_clarity_analysis"]["score"],
        "style_feedback": state["style_clarity_analysis"]["feedback"],
    })

    state["complex_feedback"] = {
        "score": summary_result.overall_score,
        "feedback": summary_result.detailed_feedback,
    }

    return state
