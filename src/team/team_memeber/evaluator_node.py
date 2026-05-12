from langchain_core.prompts import PromptTemplate
from src.team.team_memeber.state import TeamMemberState
from src.hub import gpt_4o_mini
from pydantic import BaseModel, Field


class EvaluatorNodeOutput(BaseModel):
    evaluation_summary: str = Field(description="A comprehensive evaluation of the argument focusing on its overall persuasiveness, clarity, and integration of factual, logical, and emotional elements.")
    style_evaluation: str = Field(description="An assessment of the argument’s language, tone, and overall style, including how well it engages the audience.")
    logical_evaluation: str = Field(description="A detailed review of the argument's logical coherence, including identification of any logical fallacies such as circular reasoning, false analogy, hasty generalization, false dilemma, or slippery slope.")
    suggestions: str = Field(description="Actionable recommendations for improving the argument based on the evaluation.")
    reprocess: bool = Field(description="A flag that is True if further processing (analysis, argumentation, or data retrieval) is needed due to critical shortcomings, and False if the argument is satisfactory.")


def evaluator_node(state: TeamMemberState) -> TeamMemberState:
    prompt = PromptTemplate(
        template="""
               Role:
               You are the Argument Evaluator, an expert in analyzing and assessing arguments for clarity, logic, and persuasiveness. Your task is to evaluate the refined argument provided below, focusing on its factual accuracy, logical coherence, and emotional appeal.
               You should evaluate arguments like you are human with the personality and experience of {person}
               You are in {team_role} team.

               Context:
               The argument should be methodical, clear, and critically evaluated. In your analysis, please be vigilant in identifying common logical fallacies such as:
               - Circular reasoning (e.g., "He talks a lot, so he surely cannot keep a secret.")
               - False analogy (e.g., "Kristina is like a butterfly—sometimes pretty, sometimes ugly.")
               - Hasty generalization (e.g., "My car broke down after five years. Cars of this brand always break down after five years.")
               - False dilemma (e.g., "We either go to the beach or do nothing.")
               - Slippery slope (e.g., "He missed one meeting, didn’t answer his phone yesterday, so today he’ll probably ignore me, and tomorrow he’ll end things with me!")

               Inputs:
               1. Topic: {topic}
               3. Refined Argument: {refined_argument}
               4. Audience Profile: {audience_profile}

               Tasks:
               - Evaluate the overall persuasiveness of the argument.
               - Assess the clarity, tone, and style to ensure the argument is engaging.
               - Review the logical structure of the argument and check for any instances of logical fallacies.
               - Based on your evaluation, determine if the argument requires further processing (analysis, argumentation, or additional data retrieval). If critical shortcomings are present, set "reprocess_flag" to true; otherwise, set it to false.
               - Provide recommendations and actionable suggestions to improve the argument.

               Please output your result in JSON format with the following keys:
               "evaluation_summary", "style_evaluation", "logical_evaluation", "suggestions", and "reprocess".
           """,
        input_variables=["topic", "team_role", "person", "refined_argument", "audience_profile"]
    )

    chain = prompt | gpt_4o_mini.with_structured_output(EvaluatorNodeOutput)
    result = chain.invoke({
        "topic": state["topic"],
        "team_role": state["team_role"],
        "person": state["person"],
        "refined_argument": state["lexicon_adjustment"]["refined_argument"],
        "audience_profile": state["audience_profile"],
    })

    state["evaluation"] = {
        "evaluation_summary": result.evaluation_summary,
        "style_evaluation": result.style_evaluation,
        "logical_evaluation": result.logical_evaluation,
        "suggestions": result.suggestions,
        "reprocess": result.reprocess,
    }

    state["iteration_number"] = state["iteration_number"] + 1

    return state
