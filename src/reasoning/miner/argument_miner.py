from langchain_core.prompts import PromptTemplate
from src.hub import gpt_4o_mini
from pydantic import BaseModel, Field
from typing import List, Optional

class GoalMapping(BaseModel):
    goal: str = Field(description="Goal identifier (e.g., 'goal_innovation')")
    domains: List[str] = Field(description="Domains this goal applies to")

class Argument(BaseModel):
    name: str = Field(description="argument name (e.g a_innovation, a_cheap)")
    domains: List[str] = Field(description="Domains covered by argument (e.g. ['domain_culture', 'domain_energy'])")
    goals: List[GoalMapping] = Field(
        default=[],
        description="Goals covered by the argument with their domain mappings"
    )

def argument_parser_node() -> Argument:
    prompt = PromptTemplate(
        template="""
            ### Task:
            Map a natural language argument into an Argument object for a debate on the topic: {topic}.

            ### Available Domains:
            {domains_info}

            ### Available Goals:
            {goals_info}

            ### Input:
            Raw argument: {argument}
            Existing argument names: {existing_arguments}

            ### Instructions:
            1. **Generate a unique name** for the argument following the format "a_[descriptive_word]" (e.g., "a_innovation", "a_security", "a_efficiency"). Avoid duplication with existing names.
               - IMPORTANT: Use only letters, numbers, and underscores. Do NOT use purely numeric identifiers.
            
            2. **Select relevant domains** (up to 2):
               - Choose domains where this argument would have the most impact or relevance
               - Consider the domain descriptions and salience values (higher salience = more important)
               - If the argument clearly fits only one domain, select just that one
               - IMPORTANT: Use only the exact domain IDs provided above. Do NOT use numeric values.
            
            3. **Map to supportive goals** (up to 2):
               - Identify which goals this argument helps achieve
               - For each selected goal, specify which domain(s) it applies to
               - Consider the goal descriptions and how the argument contributes to achieving them
               - Goals must only map to domains you've selected for the argument
               - IMPORTANT: Use only the exact goal IDs provided above. Do NOT use numeric values.

            ### Domain Selection Guidelines:
            - Higher salience domains are generally more impactful in the debate
            - Choose domains where the argument has clear, direct relevance
            - Consider both immediate and secondary effects of the argument

            ### Goal Mapping Guidelines:
            - An argument can support the same goal across multiple domains
            - Different goals can be supported in different domains
            - Only map goals where there's a clear logical connection to the argument

            ### Output Format (JSON only):
            Return a JSON object with this exact structure:

            ```json
            {{
                "name": "a_descriptive_name",
                "domains": ["domain_id_1", "domain_id_2"],
                "goals": [
                    {{"goal": "goal_id_1", "domains": ["domain_id_1"]}},
                    {{"goal": "goal_id_2", "domains": ["domain_id_1", "domain_id_2"]}}
                ]
            }}
            ```

            **Important**: Use only the exact domain and goal IDs provided above. If no goals are applicable, return an empty goals array.
        """,
        input_variables=["topic", "domains_info", "goals_info", "argument", "existing_arguments"]
    )

    return prompt | gpt_4o_mini.with_structured_output(Argument)
