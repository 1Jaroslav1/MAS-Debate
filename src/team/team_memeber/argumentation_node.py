from langchain_core.prompts import PromptTemplate
from src.team.team_memeber.state import TeamMemberState
from src.hub import gpt_4o_mini
from pydantic import BaseModel, Field


class ArgumentationStrategyOutput(BaseModel):
    rhetorical_strategy: str = Field(description="The chosen rhetorical strategy (logos, pathos, ethos) for engaging the audience emotionally and ethically.")
    logical_structure: str = Field(description="The selected logical structure (deductive, inductive, or mixed) for coherent reasoning.")
    factual_strategy: str = Field(description="The approach to integrate and validate factual evidence in the argument.")
    counterargument_strategy: str = Field(description="The strategy for anticipating and refuting potential counterarguments.")
    contextual_adaptation: str = Field(description="The method used to tailor the argument to the specific audience and situational context.")


class CompleteArgumentationOutput(BaseModel):
    argument_draft: str = Field(description="The final drafted argument that integrates all strategies.")
    rhetorical_strategy: str = Field(description="The chosen rhetorical strategy (e.g., logos, pathos, ethos) to emotionally and ethically engage the audience.")
    logical_structure: str = Field(description="The selected logical structure (deductive, inductive, or mixed) to ensure coherent reasoning.")
    factual_strategy: str = Field(description="The approach to integrate and verify factual evidence supporting the argument.")
    counterargument_strategy: str = Field(description="The plan to anticipate and refute potential counterarguments.")
    contextual_adaptation: str = Field(description="The method of tailoring the argument to the specific context and nuances of the audience.")


def argumentation_node(state: TeamMemberState) -> TeamMemberState:
    strategy_prompt = PromptTemplate(
        template="""
            Role:
            You are an **Expert Argumentation Strategist**, tasked with developing a **high-impact, distinct, and strategically sound** debate argument. 
            You should behave like you are human with such personality and experience: {person}.
            You are in the {team_role} team.

            **Objective:**  
            - Ensure your team's argument is **clear, strong, and uniquely positioned** in contrast to the opposing side.  
            - Identify **key ideological differences** and **exploit weaknesses** in the opponent’s position.  
            - Structure your argument in a way that will **put your opponent on the defensive** while reinforcing your core stance.  

            **Instructions:**  
            1. **Distinctiveness:**  
                - **Avoid overlapping with previous team arguments**—introduce fresh angles, unique case studies, or new dimensions.  
                - If your team is *proposing regulation*, make a strong case for **strict oversight and consequences for violations** rather than just responsibility.  
                - If your team is *opposing regulation*, emphasize **freedom, constitutional integrity, and the failures of overregulation** rather than conceding to education-based solutions.  

            2. **Engagement & Persuasion:**  
                - Utilize a **compelling storytelling approach** that resonates emotionally with the audience.  
                - Consider **historical precedents, psychological studies, or real-world case studies** to reinforce your points.  
                - Avoid generic rhetoric—**make the debate personal, impactful, and engaging**.  

            3. **Strategic Defense & Counterattacks:**  
                - Anticipate the strongest **counterarguments** from the opponent and prepare **targeted rebuttals**.  
                - Identify **logical inconsistencies** in the opposing side's stance and **turn them into strategic weaknesses**.  
                - Incorporate **unexpected but powerful arguments** that force the other side to rethink their position.  

            **Debate Context:**  
            - **Topic:** {topic}  
            - **Your Team’s Previous Arguments:** {team_arguments}  
            - **Opponent’s Expected Arguments:** {analysis_summary}  
            - **Retrieved Evidence:** {evidence_summary}  
            - **Audience Profile:** {audience_profile}  

            **Output Format:**  
            Provide a JSON response with the following keys:  
            - **"rhetorical_strategy"**: (logos, pathos, ethos - select one based on what best resonates with the audience).  
            - **"logical_structure"**: (deductive, inductive, or mixed reasoning).  
            - **"factual_strategy"**: (How to integrate **diverse, fresh, and varied** evidence).  
            - **"counterargument_strategy"**: (How to **target, challenge, and refute** opposing arguments).  
            - **"contextual_adaptation"**: (How to tailor the argument to the audience and make it persuasive).  
        """,
        input_variables=["topic", "team_arguments", "team_role", "analysis_summary", "evidence_summary",
                         "audience_profile"]
    )
    strategy_chain = strategy_prompt | gpt_4o_mini.with_structured_output(ArgumentationStrategyOutput)
    strategy_result = strategy_chain.invoke({
        "topic": state["topic"],
        "team_arguments": state["team_arguments"],
        "team_role": state["team_role"],
        "person": state["person"],
        "analysis_summary": state["analysis"]["main_themes_and_issues"],
        "evidence_summary": state["retrieved_data"]["evidence_summary"],
        "audience_profile": state["audience_profile"]
    })

    combined_analysis = state["analysis"]["main_themes_and_issues"] + state.get("team_arguments", [])

    argument_prompt = PromptTemplate(
        template="""
            Role:
            You are the **Debate Argumentation Agent**, responsible for crafting a **powerful, ideologically distinct, and strategically sound** debate argument.  
            You should create arguments like you are human with such personality and experience: {person}.  

            **Your Mission:**  
            - Ensure your argument is **clear, forceful, and contrasts sharply** with the opposition.  
            - Present a **strategic, well-reasoned case** that **engages the audience and preemptively counters** the opponent’s likely attacks.  
            - Craft **unexpected yet compelling angles** that strengthen your team’s stance while putting the opposing side on the defensive.  

            **Key Elements for Success:**  

            1. **Fresh & Unique Arguments:**  
                - **Do NOT repeat previous team arguments**—instead, introduce **new dimensions, examples, or frameworks**.  
                - If your team is *proposing regulation*, argue for **why restrictions are necessary to prevent societal harm**, not just "balance."  
                - If your team is *opposing regulation*, focus on **freedom, unintended consequences of laws, and historical failures of similar regulations**.  

            2. **Strategic Persuasion & Emotional Impact:**  
                - Choose a **rhetorical approach (logos, pathos, ethos)** that is **best suited for this specific audience**.  
                - Use **compelling examples, dramatic storytelling, or unexpected real-world cases** to **hold attention and convince**.  
                - Avoid generic rhetoric—make your argument feel urgent, **as if the debate has real-life stakes**.  

            3. **Counterargument Strategy:**  
                - Identify the **biggest weaknesses in the opposing argument** and **design responses that dismantle their position**.  
                - Use their **own logic against them**—if they claim regulation improves safety, **cite cases where it has failed**.  
                - Predict the opponent’s **strongest counterpoints** and **neutralize them in advance**.  

            4. **Varied & Strong Evidence Selection:**  
                - Ensure **your sources do NOT overlap** with the opposing team’s evidence.  
                - Use **a mix of empirical data, case studies, expert opinions, and historical comparisons**.  
                - Highlight **unexpected yet powerful data points** that disrupt standard narratives.  

            **Debate Context:**  
            - **Topic:** {topic}  
            - **Your Team’s Previous Arguments:** {team_arguments}  
            - **Opponent’s Likely Arguments:** {analysis_summary}  
            - **Retrieved Evidence:** {evidence_summary}  
            - **Audience Profile:** {audience_profile}  
            - **Evaluation Summary:** {evaluation_summary}  
            - **Evaluator Suggestions:** {evaluation_suggestions}  

            **Output Format:**  
            Provide a JSON response with the following keys:  
            - **"argument_draft"**: (A fully structured and engaging argument).  
            - **"rhetorical_strategy"**: (logos, pathos, ethos - use the most effective approach for this audience).  
            - **"logical_structure"**: (deductive, inductive, or mixed reasoning).  
            - **"factual_strategy"**: (How to integrate **strong, varied, and unique** evidence).  
            - **"counterargument_strategy"**: (How to preemptively **challenge and refute** opposing views).  
            - **"contextual_adaptation"**: (How to adjust argument style to the specific audience and debate context).  
        """,
        input_variables=[
            "topic", "team_arguments", "person", "evaluation_summary", "evaluation_suggestions",
            "analysis_summary", "evidence_summary", "audience_profile",
            "rhetorical_strategy", "logical_structure", "factual_strategy",
            "counterargument_strategy", "contextual_adaptation"
        ]
    )
    argument_chain = argument_prompt | gpt_4o_mini.with_structured_output(CompleteArgumentationOutput)
    argument_result = argument_chain.invoke({
        "topic": state["topic"],
        "team_arguments": state["team_arguments"],
        "person": state["person"],
        "evaluation_summary": state["evaluation"].get("evaluation_summary", "No previous evaluation available."),
        "evaluation_suggestions": state["evaluation"].get("suggestions", "No suggestions provided."),
        "analysis_summary": combined_analysis,
        "evidence_summary": state["retrieved_data"]["evidence_summary"],
        "audience_profile": state["audience_profile"],
        "rhetorical_strategy": getattr(strategy_result, "rhetorical_strategy", "logos"),
        "logical_structure": getattr(strategy_result, "logical_structure", "deductive"),
        "factual_strategy": getattr(strategy_result, "factual_strategy", "verify and integrate data from credible sources"),
        "counterargument_strategy": getattr(strategy_result, "counterargument_strategy", "anticipate objections and provide rebuttals"),
        "contextual_adaptation": getattr(strategy_result, "contextual_adaptation", "tailor argument based on audience profile"),
    })

    state["argument"] = {
        "argument_draft": argument_result.argument_draft,
        "rhetorical_strategy": argument_result.rhetorical_strategy,
        "logical_structure": argument_result.logical_structure,
        "factual_strategy": argument_result.factual_strategy,
        "counterargument_strategy": argument_result.counterargument_strategy,
        "contextual_adaptation": argument_result.contextual_adaptation,
    }

    return state
