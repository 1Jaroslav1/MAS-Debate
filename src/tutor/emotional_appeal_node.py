from typing_extensions import List
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.hub import gpt_4o_mini
from src.tutor.state import TutorState
from src.tutor.utils import summarize_audience_profile


class EmotionalAnalysisOutput(BaseModel):
    emotional_connection: str = Field(
        description="A summary evaluation of how effectively the user's arguments establish an emotional connection with the audience."
    )
    emotional_appropriateness: str = Field(
        description="An assessment of whether the emotional elements used are appropriate for the debate topic and the intended audience."
    )
    emotional_impact: str = Field(
        description="A summary of the overall impact of the emotional appeal in persuading and engaging the audience."
    )


class EmotionalFeedbackOutput(BaseModel):
    score: int = Field(
        description="Numeric score (1-10) reflecting the overall effectiveness of the emotional appeal in the user's arguments."
    )
    feedback: str = Field(
        description="Actionable suggestions to improve the use, appropriateness, and impact of emotional elements in the argumentation."
    )


def modify_transcripts(transcripts: List[dict]) -> str:
    return "\n".join(
        [f"{t['speaker']} ({t['team_role']}): {t['text']}" for t in transcripts]
    )


def emotional_analysis(state: TutorState) -> EmotionalAnalysisOutput:
    # Focus solely on the user's arguments
    user_transcript = modify_transcripts(state["user_arguments"])

    analysis_prompt = PromptTemplate(
        template="""
            Role:
            You are an **Emotional Appeal Analysis Agent**. Your task is to evaluate the emotional aspects of the user's arguments for the topic "{topic}".

            User Argument Transcript:
            {user_transcript}

            Audience Profile:
            {audience_profile}

            Please perform the following tasks:
            1. Evaluate how effectively the arguments establish an emotional connection with the audience.
            2. Assess the appropriateness of the emotional elements in relation to the debate topic and the audience's expectations.
            3. Determine the overall impact of the emotional appeal on the persuasiveness of the arguments.

            Return your analysis in JSON format with these keys:
            - "emotional_connection": A summary of the emotional connection established.
            - "emotional_appropriateness": An assessment of the appropriateness of the emotional tone.
            - "emotional_impact": A summary of the overall emotional impact.
            """,
        input_variables=["topic", "user_transcript", "audience_profile"]
    )

    analysis_chain = analysis_prompt | gpt_4o_mini.with_structured_output(EmotionalAnalysisOutput)
    analysis_result = analysis_chain.invoke({
        "topic": state["topic"],
        "user_transcript": user_transcript,
        "audience_profile": summarize_audience_profile(state["audience_profile"]),
    })

    return analysis_result


def emotional_feedback_node(state: TutorState) -> TutorState:
    analysis = emotional_analysis(state)

    feedback_prompt = PromptTemplate(
        template="""
            Role:
            You are an **Emotional Appeal Feedback Agent**. Based on the following analysis of the user's emotional appeal:

            - Emotional Connection: {emotional_connection}
            - Emotional Appropriateness: {emotional_appropriateness}
            - Emotional Impact: {emotional_impact}

            Please provide:
            1. A numeric score (1–10) reflecting the overall effectiveness of the emotional appeal in the user's arguments:
               - 1–3: The emotional appeal is weak, inappropriate, or ineffective.
               - 4–6: The emotional appeal is moderate but could be enhanced.
               - 7–9: The emotional appeal is strong with minor improvements needed.
               - 10: The emotional appeal is outstanding—highly engaging and persuasive.
            2. Detailed, actionable feedback with suggestions to improve the use of emotional elements in the argumentation.

            Return your response in JSON format with these keys:
            - "score": The numeric score.
            - "feedback": Detailed suggestions for improvement.
            """,
        input_variables=["emotional_connection", "emotional_appropriateness", "emotional_impact"]
    )

    feedback_chain = feedback_prompt | gpt_4o_mini.with_structured_output(EmotionalFeedbackOutput)
    feedback_result = feedback_chain.invoke({
        "emotional_connection": analysis.emotional_connection,
        "emotional_appropriateness": analysis.emotional_appropriateness,
        "emotional_impact": analysis.emotional_impact,
    })

    state["emotional_appeal_analysis"] = {
        "score": feedback_result.score,
        "feedback": feedback_result.feedback,
    }

    return state
