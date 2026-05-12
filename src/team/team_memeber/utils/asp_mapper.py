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


class AtomicFactOutput(BaseModel):
    text: str = Field(description="Atomic fact from the text in ASP syntax. Each fact should be represented as: ```knowledge(domain, atomic_fact).```")


class Text2AspOutput(BaseModel):
    facts: List[AtomicFactOutput] = Field(description="List of ASP facts")


def text_2_asp(text: str, domains: list[str]):
    prompt = PromptTemplate(
        template="""
            **Task:**  
            Convert natural language facts into ASP knowledge facts.
            
            **Format:**  
            Each fact should be represented as:  
            ```
            knowledge(domain, atomic_fact).
            ```
            - **domain:** One of the provided domains.
            - **atomic_fact:** A concise, standalone statement extracted from the input text.
            
            **Input:**  
            Domains: {domains}
            Input Text: {text}
            
            **Instructions:**  
            - Parse the input text and extract atomic facts related to each domain.
            - If a sentence contains multiple facts for a domain, output each as a separate ASP fact.
            - If a sentence mentions multiple domains, generate a separate fact for each domain mentioned.
            - Only include facts relevant to the provided domains.
            - Ensure each output ends with a period.
            
            **Example 1:**  
            *Domains:* solar, wind, geo  
            *Input Text:* "Solar energy is cheap and efficient, whereas wind energy is expensive."  
            *Expected Output:*  
            ```
            knowledge(solar, solar energy is cheap).
            knowledge(solar, solar energy is efficient).
            knowledge(wind, wind energy is expensive).
            ```
            
            **Example 2:**  
            *Domains:* solar, wind, geo  
            *Input Text:* "Geothermal energy is reliable, but solar energy depends on the weather."  
            *Expected Output:*  
            ```
            knowledge(geo, geothermal energy is reliable).
            knowledge(solar, solar energy depends on the weather).
            ```
        """,
        input_variables=["domains", "text"]
    )

    chain = prompt | gpt_4o_mini.with_structured_output(Text2AspOutput)
    result = chain.invoke(
        {
            "domains": domains,
            "text": text
        }
    )

    print(result)


# text_2_asp("Solar energy is cheap and efficient, whereas wind energy is expensive.", ["solar", "wind", "geo"])
text_2_asp("Electric vehicles reduce carbon emissions and require less maintenance, but have higher initial costs compared to gasoline-powered cars.", ["electric", "gasoline", "environment", "economics"])
text_2_asp("The integration of AI in healthcare enables improved diagnostics and personalized treatment plans, although it brings challenges regarding data privacy and algorithmic fairness.", ["ai", "healthcare", "ethics"])
text_2_asp("Advancements in artificial intelligence boost efficiency in healthcare by enabling personalized treatment plans and predictive diagnostics, but raise ethical concerns regarding data privacy and algorithmic bias. Additionally, AI supports administrative tasks, reducing workload on medical staff.", ["ai", "healthcare", "ethics", "administration"])


