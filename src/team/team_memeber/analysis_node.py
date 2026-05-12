from langchain_core.prompts import PromptTemplate
from src.team.team_memeber.state import TeamMemberState
from src.model.model import TeamRole
from src.hub import gpt_4o_mini
from pydantic import BaseModel, Field
from typing_extensions import List


class OpponentArgumentsOutput(BaseModel):
    extracted_arguments: List[str] = Field(
        description="List of extracted key arguments presented by the opposing team."
    )


class AnalysisNodeOutput(BaseModel):
    main_themes_and_issues: List[str] = Field("Main themes and issues")
    opponent_perspectives: List[str] = Field("Opponents’ likely perspectives")
    opponent_weaknesses: List[str] = Field("Weaknesses or inconsistencies in the opponent’s arguments")


def opponent_team_role(team_role: TeamRole) -> TeamRole:
    return TeamRole.OPPOSING if team_role == TeamRole.PROPOSING else TeamRole.PROPOSING


def extract_team_arguments(state: TeamMemberState) -> List[str]:
    return [
        message["text"]
        for message in state["transcript"]
        if message["team_role"] == state["team_role"]
    ]


def extract_opponent_arguments(state: TeamMemberState, opponent_team_role: TeamRole) -> List[str]:
    opponent_transcript = [
        message["text"] for message in state["transcript"] if message["team_role"] == opponent_team_role
    ]

    if not opponent_transcript:
        return []

    prompt = PromptTemplate(
        template="""
            Role:
            You are the Opponent Arguments Extractor Agent.
            You should extract opponent arguments like you are human with such personality and experience: {person}
            You are in {team_role} team.
            
            Your task is to extract and structure key arguments from the opponent team’s statements.

            Instructions:
            - Identify **clear and concise** argument points from the transcript.
            - Format arguments in bullet points, capturing **only substantive claims**.
            
            Topic: {topic}
            Opponent Debate Transcript:
            {opponent_transcript}

            Extracted Arguments:
            - (Provide a structured list of arguments)
        """,
        input_variables=["topic", "team_role", "person", "opponent_transcript"]
    )

    chain = prompt | gpt_4o_mini.with_structured_output(OpponentArgumentsOutput)
    result = chain.invoke({
        "topic": state["topic"],
        "team_role": state["team_role"],
        "person": state["person"],
        "opponent_transcript": opponent_transcript
    })

    return result.extracted_arguments


def analysis_node(state: TeamMemberState) -> TeamMemberState:
    state["opponent_arguments"] = extract_opponent_arguments(state, opponent_team_role(state["team_role"]))
    state["team_arguments"] = extract_team_arguments(state)

    prompt = PromptTemplate(
        template="""
            Role:
            You are the **Debate Strategy Analyzer**, a sharp, experienced human analyst with deep insight and a distinctive personality: {person}.
            
            **Your Mission:**  
            - **Sharpen your team’s argumentation** by introducing **new angles and fresh evidence** rather than repeating points already made.  
            - **Pinpoint weaknesses** in the opponent’s arguments and **develop targeted counterattacks**.  
            - **Identify strategic opportunities** where your team can push the debate forward and **force the opponent onto the defensive**.
    
            **Key Tasks:**  
            1. **Expand Your Team’s Argument:**  
               - Uncover **new perspectives, case studies, or expert-backed evidence** that reinforce your stance.
               - Introduce **alternative reasoning strategies** (historical, legal, economic, psychological, ethical).  
               - Avoid repeating previous team arguments—focus on **gaps and untapped angles**.  
    
            2. **Deconstruct Opponent Arguments:**  
               - Identify **flaws, contradictions, and logical weaknesses** in the opposing team’s case.  
               - Extract their **unstated assumptions** and **turn them against them**.  
               - Provide precise **counterpoints or provocative questions** that force them to clarify or defend a weak stance.  
    
            3. **Varied Evidence Approach:**  
               - Make sure your **team and opponents are not relying on the same data**—introduce fresh studies or real-world comparisons.  
               - Suggest case studies from different **countries, industries, or historical precedents** to bring diverse credibility.  
               - Incorporate **moral, legal, or social implications** for a well-rounded attack.  
    
            4. **Anticipate the Next Round:**  
               - Predict **how the opponent might react** to your team's points and **preemptively weaken their rebuttals**.  
               - Identify **high-risk counterarguments** your team must prepare for in advance.
    
            **Debate Context:**  
            - **Topic:** {topic}  
            - **Opponent Arguments:** {opponent_arguments}  
            - **Your Team’s Previous Arguments:** {team_arguments}  
            - **Audience Profile:** {audience_profile}  
            - **Evaluation Summary:** {evaluation_summary}  
            - **Evaluator Suggestions:** {evaluation_suggestions}   
        """,
        input_variables=["topic", "person", "opponent_arguments", "team_arguments", "audience_profile", "evaluation_summary", "evaluation_suggestions"]
    )
    chain = prompt | gpt_4o_mini.with_structured_output(AnalysisNodeOutput)
    result = chain.invoke({
        "topic": state["topic"],
        "person": state["person"],
        "opponent_arguments": state["opponent_arguments"],
        "team_arguments": state["team_arguments"],
        "audience_profile": state["audience_profile"],
        "evaluation_summary": state["evaluation"].get("evaluation_summary", "No previous evaluation available."),
        "evaluation_suggestions": state["evaluation"].get("suggestions", "No suggestions provided.")
    })

    state["analysis"] = {
        "main_themes_and_issues": result.main_themes_and_issues,
        "opponent_perspectives": result.opponent_perspectives,
        "opponent_weaknesses": result.opponent_weaknesses
    }

    return state
