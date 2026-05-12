from typing_extensions import List
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.hub import gpt_4o_mini
from src.tutor.state import TutorState
from src.tutor.utils import summarize_audience_profile


class EvidenceAnalysisOutput(BaseModel):
    evidence_quality: str = Field(
        description="A summary evaluation of the overall quality and relevance of the evidence and examples used."
    )
    credibility_assessment: str = Field(
        description="An evaluation of the credibility and reliability of the evidence and examples presented."
    )
    evidence_completeness: str = Field(
        description="An assessment of whether the evidence sufficiently supports the arguments, including any gaps or weaknesses."
    )


class EvidenceFeedbackOutput(BaseModel):
    score: int = Field(
        description="Numeric score (1-10) reflecting the overall quality, credibility, and sufficiency of the evidence supporting the arguments."
    )
    feedback: str = Field(
        description="Actionable suggestions to improve the selection, quality, and presentation of evidence in the argumentation."
    )


def modify_transcripts(transcripts: List[dict]) -> str:
    return "\n".join(
        [f"{t['speaker']} ({t['team_role']}): {t['text']}" for t in transcripts]
    )


def evidence_analysis(state: TutorState) -> EvidenceAnalysisOutput:
    # Focus on the user's arguments which contain the supporting evidence.
    user_transcript = modify_transcripts(state["user_arguments"])

    analysis_prompt = PromptTemplate(
        template="""
            Role:
            You are an **Evidence Support Analysis Agent**. Your task is to evaluate the quality and credibility of the evidence and examples used by the user to support their arguments for the topic "{topic}".

            User Argument Transcript:
            {user_transcript}

            Audience Profile:
            {audience_profile}

            Please perform the following tasks:
            1. Evaluate the overall quality of the evidence: How strong, relevant, and convincing is the evidence presented?
            2. Assess the credibility of the sources and examples used to substantiate the arguments.
            3. Identify any gaps or weaknesses in the evidence that may undermine the persuasiveness of the argument.

            Return your analysis in JSON format with these keys:
            - "evidence_quality": A summary of the quality and relevance of the evidence.
            - "credibility_assessment": An evaluation of the reliability and trustworthiness of the evidence.
            - "evidence_completeness": An assessment of whether the evidence sufficiently supports the arguments.
            """,
        input_variables=["topic", "user_transcript", "audience_profile"]
    )

    analysis_chain = analysis_prompt | gpt_4o_mini.with_structured_output(EvidenceAnalysisOutput)
    analysis_result = analysis_chain.invoke({
        "topic": state["topic"],
        "user_transcript": user_transcript,
        "audience_profile": summarize_audience_profile(state["audience_profile"]),
    })

    return analysis_result


def evidence_feedback_node(state: TutorState) -> TutorState:
    analysis = evidence_analysis(state)

    feedback_prompt = PromptTemplate(
        template="""
            Role:
            You are an **Evidence Support Feedback Agent**. Based on the following analysis of the evidence supporting the user's arguments:

            - Evidence Quality: {evidence_quality}
            - Credibility Assessment: {credibility_assessment}
            - Evidence Completeness: {evidence_completeness}

            Please provide:
            1. A numeric score (1–10) reflecting the overall quality, credibility, and sufficiency of the evidence:
               - 1–3: The evidence is weak, irrelevant, or lacks credibility.
               - 4–6: The evidence is moderately convincing but has significant shortcomings.
               - 7–9: The evidence is strong and credible with only minor areas for improvement.
               - 10: The evidence is exceptional—highly relevant, credible, and fully supportive of the arguments.
            2. Detailed, actionable feedback with suggestions to enhance the quality, credibility, and presentation of the evidence.

            Return your response in JSON format with these keys:
            - "score": The numeric score.
            - "feedback": Detailed suggestions for improvement.
            """,
        input_variables=["evidence_quality", "credibility_assessment", "evidence_completeness"]
    )

    feedback_chain = feedback_prompt | gpt_4o_mini.with_structured_output(EvidenceFeedbackOutput)
    feedback_result = feedback_chain.invoke({
        "evidence_quality": analysis.evidence_quality,
        "credibility_assessment": analysis.credibility_assessment,
        "evidence_completeness": analysis.evidence_completeness,
    })

    state["evidence_support_analysis"] = {
        "score": feedback_result.score,
        "feedback": feedback_result.feedback,
    }

    return state
