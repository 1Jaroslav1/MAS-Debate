from typing_extensions import List
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.hub import gpt_4o_mini
from src.tutor.state import TutorState
from src.tutor.utils import summarize_audience_profile


class StyleClarityAnalysisOutput(BaseModel):
    language_use: str = Field(
        description="An evaluation of the vocabulary, tone, and overall language quality used in the user's arguments."
    )
    sentence_structure: str = Field(
        description="An assessment of the grammar, flow, and construction of sentences in the argumentation."
    )
    readability: str = Field(
        description="An evaluation of how clear and easy-to-read the argumentation is overall."
    )


class StyleClarityFeedbackOutput(BaseModel):
    score: int = Field(
        description="Numeric score (1-10) reflecting the overall clarity and style of the user's argumentation."
    )
    feedback: str = Field(
        description="Actionable suggestions to improve language use, sentence structure, and readability."
    )


def modify_transcripts(transcripts: List[dict]) -> str:
    return "\n".join(
        [f"{t['speaker']} ({t['team_role']}): {t['text']}" for t in transcripts]
    )


def style_clarity_analysis(state: TutorState) -> StyleClarityAnalysisOutput:
    # Focus on the user's argument transcript.
    user_transcript = modify_transcripts(state["user_arguments"])

    analysis_prompt = PromptTemplate(
        template="""
            Role:
            You are a **Style and Clarity Analysis Agent**. Your task is to evaluate how clearly and effectively the user's arguments are communicated for the topic "{topic}".

            User Argument Transcript:
            {user_transcript}

            Audience Profile:
            {audience_profile}

            Please perform the following tasks:
            1. Assess the language use, including vocabulary, tone, and overall language quality.
            2. Evaluate the sentence structure, grammar, and flow of the arguments.
            3. Determine the overall readability and clarity of the argumentation.

            Return your analysis in JSON format with these keys:
            - "language_use": Your evaluation of the language and tone.
            - "sentence_structure": Your assessment of the sentence construction and flow.
            - "readability": Your evaluation of the overall clarity and readability.
            """,
        input_variables=["topic", "user_transcript", "audience_profile"]
    )

    analysis_chain = analysis_prompt | gpt_4o_mini.with_structured_output(StyleClarityAnalysisOutput)
    analysis_result = analysis_chain.invoke({
        "topic": state["topic"],
        "user_transcript": user_transcript,
        "audience_profile": summarize_audience_profile(state["audience_profile"]),
    })

    return analysis_result


def style_clarity_feedback_node(state: TutorState) -> TutorState:
    analysis = style_clarity_analysis(state)

    feedback_prompt = PromptTemplate(
        template="""
            Role:
            You are a **Style and Clarity Feedback Agent**. Based on the following analysis of the user's argumentation:

            - Language Use: {language_use}
            - Sentence Structure: {sentence_structure}
            - Readability: {readability}

            Please provide:
            1. A numeric score (1–10) that reflects the overall clarity and style of the user's argumentation:
               - 1–3: Poor clarity and style; the argument is difficult to read and understand.
               - 4–6: Average clarity and style; some areas need improvement.
               - 7–9: Good clarity and style; minor enhancements could be made.
               - 10: Excellent clarity and style; the argument is exceptionally well-written and easy to follow.
            2. Detailed, actionable feedback with specific suggestions for enhancing language use, sentence structure, and overall readability.

            Return your response in JSON format with these keys:
            - "score": The numeric score.
            - "feedback": Detailed suggestions for improvement.
            """,
        input_variables=["language_use", "sentence_structure", "readability"]
    )

    feedback_chain = feedback_prompt | gpt_4o_mini.with_structured_output(StyleClarityFeedbackOutput)
    feedback_result = feedback_chain.invoke({
        "language_use": analysis.language_use,
        "sentence_structure": analysis.sentence_structure,
        "readability": analysis.readability,
    })

    state["style_clarity_analysis"] = {
        "score": feedback_result.score,
        "feedback": feedback_result.feedback,
    }

    return state
