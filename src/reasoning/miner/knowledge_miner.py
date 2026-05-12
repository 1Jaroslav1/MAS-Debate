from langchain_core.prompts import PromptTemplate
from src.hub import gpt_4o_mini
from pydantic import BaseModel, Field
from typing import List

class KnowledgeModel(BaseModel):
    domain: str = Field(description="Knowledge's domain")
    atomicFact: str = Field(description="Knowledge's atomic fact")

class Knowledge(BaseModel):
    knowledge: List[KnowledgeModel]

def knowledge_parser_node():
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

            **Filtering Criteria:**  
            Only extract atomic facts that clearly demonstrate at least one of the following benefits:
            {metrics}

            **Input:**  
            Domains: {domains}
            Text containing statements: {text}

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
            *Domains:* agriculture, climate, economy
            *Input Text:* "Climate change affects crop yields and disrupts the economy. Agricultural practices can reduce emissions."  
            *Expected Output:*  
            ```
            knowledge(climate, climate change affects crop yields).
            knowledge(climate, climate change disrupts the economy).
            knowledge(economy, climate change disrupts the economy).
            knowledge(agriculture, agricultural practices can reduce emissions).
            ```
        """,
        input_variables=["domains", "text", "metrics"]
    )

    return prompt | gpt_4o_mini.with_structured_output(Knowledge)
