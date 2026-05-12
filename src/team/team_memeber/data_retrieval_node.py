from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage
from src.hub import gpt_4o_mini
from src.team.team_memeber.state import TeamMemberState
from langgraph.prebuilt import ToolNode
from src.hub import get_tavily_tool
from pydantic import BaseModel, Field
from typing import List, Optional


tavily_tool = get_tavily_tool(max_results=1)
tools = [tavily_tool]
team_tools_node = ToolNode(tools)


class EvidenceItem(BaseModel):
    summary: str = Field(description="A brief summary of the evidence.")
    source: str = Field(description="The name of the source or publication.")
    url: str = Field(description="A URL link to the evidence (if available).")
    publication_date: Optional[str] = Field(None, description="Optional publication date.")


class DataRetrievalNodeOutput(BaseModel):
    evidence_summary: str = Field(description="A consolidated summary of the retrieved evidence.")
    evidence_items: List[EvidenceItem] = Field(description="A list of structured evidence items.")


def data_retrieval_node(state: TeamMemberState) -> TeamMemberState:
    analysis_themes = state.get("analysis", {}).get("main_themes_and_issues", [])
    search_queries = [f"credible sources on {theme}" for theme in analysis_themes]

    search_messages = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "tavily_search",
                "args": {"query": query},
                "id": f"tool_call_{idx}",
                "type": "tool_call",
            }
            for idx, query in enumerate(search_queries)
        ],
    )

    tool_results = team_tools_node.invoke({"messages": [search_messages]})

    raw_evidence_list = [msg.content for msg in tool_results.get("messages", [])]
    raw_evidence = "\n".join(raw_evidence_list)

    prompt = PromptTemplate(
        template="""
            Role:
            You are the Evidence Structuring Agent. Your task is to organize the raw evidence retrieved for the debate topic into a structured format that best supports argument creation.
            You should find the newest information.
            You should retrieve evidence based on knowledge and experience as if you were a human with the personality and experience of {person}
            
            Context:
            - Topic: {topic}
            - Analysis Themes: {analysis_summary}
            - Raw Evidence: {raw_evidence}
            
             Additional Instructions:
            - This is a reprocessing cycle based on evaluator feedback. Consider the evaluation details below to refine your evidence search:
              Evaluation Summary: {evaluation_summary}
              Suggestions: {evaluation_suggestions}
            - Update your evidence search by addressing any identified gaps or by expanding queries where necessary.

            Tasks:
            1. Provide a consolidated summary that highlights key findings, statistics, expert opinions, and research results relevant to the debate.
            2. Create a list of evidence items. For each item, include:
                - summary: A brief description of the evidence.
                - source: The name of the source or publication.
                - url: A URL link to the evidence, if available.
                - publication_date: (Optional) The publication date.
        """,
        input_variables=["topic", "person", "analysis_summary", "raw_evidence", "evaluation_summary", "evaluation_suggestions"]
    )

    chain = prompt | gpt_4o_mini.with_structured_output(DataRetrievalNodeOutput)
    result = chain.invoke({
        "topic": state["topic"],
        "person": state["person"],
        "analysis_summary": ", ".join(analysis_themes),
        "raw_evidence": raw_evidence,
        "evaluation_summary": state["evaluation"].get("evaluation_summary", "No previous evaluation available."),
        "evaluation_suggestions": state["evaluation"].get("suggestions", "No suggestions provided.")
    })

    state["retrieved_data"] = {
        "evidence_summary": result.evidence_summary,
        "evidence_items": [item.dict() for item in result.evidence_items]
    }

    return state
