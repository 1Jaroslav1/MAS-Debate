from langchain_core.prompts import PromptTemplate
from src.team.team_memeber.state import TeamMemberState
from src.hub import gpt_4o_mini
from pydantic import BaseModel, Field


class LexiconManagerNodeOutput(BaseModel):
    refined_argument: str = Field(description="The final refined argument text that is structured to emphasize factual accuracy, logical coherence, and emotional appeal.")
    refinement_notes: str = Field(description="Detailed notes on the adjustments made to vocabulary, tone, style, and structure.")


def lexicon_manager_node(state: TeamMemberState) -> TeamMemberState:
    prompt = PromptTemplate(
        template="""
            Role:
            You are the Lexicon Manager, an expert in rhetoric and language refinement. Your task is to transform the following draft argument so that it is presented in a clear and structured manner, balancing factual accuracy, logical coherence, and emotional appeal.
            You should use lexicon related to your personality: {person}

            Context:
            The refined argument must adhere to these key principles:
            - **Fact-based Argumentation:** Every claim should be supported by verifiable data. Acknowledge uncertainties appropriately.
            - **Logical Argumentation:** Ensure the reasoning is coherent using deductive, inductive, or mixed approaches. Avoid logical fallacies.
            - **Emotional Argumentation:** Engage the audience through storytelling, strategic pauses, and rhetorical devices.
            - **Persuasive Conclusion:** Conclude with a clear call to action or a strong summary of key points.

            Inputs:
            1. Topic: {topic}
            2. Draft Argument: {argument}
            3. Audience Profile: {audience_profile}

            Tasks:
            - Analyze the provided draft argument to identify areas that could benefit from improved clarity, tone, and structure.
            - Adjust the vocabulary, tone, and overall style to ensure the argument resonates with the target audience.
            - Restructure the argument to clearly separate factual evidence, logical reasoning, and emotional appeal.
            - Provide a refined version of the argument along with detailed notes describing the language and style adjustments made.

            Please output your result in JSON format with the following keys:
            - "refined_argument": The final refined argument.
            - "refinement_notes": Detailed notes on language and style adjustments.
        """,
        input_variables=["topic", "person", "argument", "audience_profile"]
    )

    chain = prompt | gpt_4o_mini.with_structured_output(LexiconManagerNodeOutput)
    result = chain.invoke({
        "topic": state["topic"],
        "person": state["person"],
        "argument": state["argument"]["argument_draft"],
        "audience_profile": state["audience_profile"],
    })

    state["lexicon_adjustment"] = {
        "refined_argument": result.refined_argument,
        "refinement_notes": result.refinement_notes,
    }
    return state
