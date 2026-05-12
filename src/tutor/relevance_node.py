from typing_extensions import List
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.hub import gpt_4o_mini
from src.tutor.state import TutorState
from src.tutor.utils import summarize_audience_profile


class RelevanceAnalysisOutput(BaseModel):
    alignment_assessment: str = Field(
        description="A summary of how well the user's arguments align with the central debate topic."
    )
    off_topic_observations: str = Field(
        description="Observations on any parts of the user's arguments that deviate from or are not pertinent to the central issue."
    )
    central_issue_coverage: str = Field(
        description="An evaluation of how comprehensively the central issue is addressed within the user's arguments."
    )


class RelevanceFeedbackOutput(BaseModel):
    score: int = Field(
        description="Numeric score (1-10) reflecting how relevant the user's arguments are to the central debate topic."
    )
    feedback: str = Field(
        description="Actionable suggestions to improve the focus and relevance of the user's arguments to the central issue."
    )


def modify_transcripts(transcripts: List[dict]) -> str:
    return "\n".join(
        [f"{t['speaker']} ({t['team_role']}): {t['text']}" for t in transcripts]
    )


def relevance_analysis(state: TutorState) -> RelevanceAnalysisOutput:
    # Focus only on the user's arguments.
    user_transcript = modify_transcripts(state["user_arguments"])

    relevance_analysis_prompt = PromptTemplate(
        template="""
            Role:
            You are a **Relevance Analysis Agent**. Your task is to evaluate the relevance of the user's arguments to the central debate topic "{topic}".

            User Arguments:
            {user_transcript}

            Audience Profile:
            {audience_profile}

            Please perform the following tasks:
            1. Assess how directly and effectively the user's arguments address the central issue.
            2. Identify any segments that deviate from or are not pertinent to the central topic.
            3. Provide a concise summary of the overall relevance of the arguments.

            Return your analysis in JSON format with these keys:
            - "alignment_assessment": A summary of how well the arguments align with the debate topic.
            - "off_topic_observations": Observations on any parts of the argument that are irrelevant or off-topic.
            - "central_issue_coverage": An evaluation of how comprehensively the central issue is covered.
            """,
        input_variables=["topic", "user_transcript", "audience_profile"]
    )

    analysis_chain = relevance_analysis_prompt | gpt_4o_mini.with_structured_output(RelevanceAnalysisOutput)
    analysis_result = analysis_chain.invoke({
        "topic": state["topic"],
        "user_transcript": user_transcript,
        "audience_profile": summarize_audience_profile(state["audience_profile"]),
    })

    return analysis_result


def relevance_feedback_node(state: TutorState) -> TutorState:
    analysis = relevance_analysis(state)

    relevance_feedback_prompt = PromptTemplate(
        template="""
            Role:
            You are a **Relevance Feedback Agent**. Based on the following analysis of the user's arguments:

            - Alignment Assessment: {alignment_assessment}
            - Off-Topic Observations: {off_topic_observations}
            - Central Issue Coverage: {central_issue_coverage}

            Please provide:
            1. A numeric score (1–10) reflecting the overall relevance of the user's arguments to the central debate topic:
               - 1–3: Arguments are largely off-topic with minimal alignment.
               - 4–6: Some points are relevant, but the focus is inconsistent.
               - 7–9: Generally relevant with only minor deviations.
               - 10: Fully aligned; arguments consistently and effectively address the central issue.
            2. Detailed, actionable feedback with suggestions to enhance the focus and relevance of the arguments.

            Return your response in JSON format with these keys:
            - "score": The numeric score.
            - "feedback": Detailed suggestions for improvement.
            """,
        input_variables=["alignment_assessment", "off_topic_observations", "central_issue_coverage"]
    )

    feedback_chain = relevance_feedback_prompt | gpt_4o_mini.with_structured_output(RelevanceFeedbackOutput)
    feedback_result = feedback_chain.invoke({
        "alignment_assessment": analysis.alignment_assessment,
        "off_topic_observations": analysis.off_topic_observations,
        "central_issue_coverage": analysis.central_issue_coverage,
    })

    state["relevance_analysis"] = {
        "score": feedback_result.score,
        "feedback": feedback_result.feedback,
    }

    return state
