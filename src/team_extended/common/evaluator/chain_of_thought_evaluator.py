"""
Chain of Thought based evaluator as alternative to GoDsAF
Uses a multi-step workflow with sequential LLM calls for comprehensive evaluation
"""
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, START, END
from src.hub import gpt_4o_mini
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.evaluator.model import EvaluationResult, EvaluationScore, UnifiedArgumentEvaluation
from src.team_extended.common.evaluator.evaluator_interface import ArgumentEvaluatorInterface
from src.team_extended.common.evaluator.model import Argument, EvaluationScore
from src.reasoning.miner.argument_miner import argument_parser_node
from src.team_extended.common.evaluator.godsaf.godsaf_evaluator import GoDsAFArgumentEvaluator
from src.team_extended.common.team_member import StrategyRecommendation


class ChainOfThoughtEvaluationState(TypedDict):
    """State for chain-of-thought evaluation workflow"""
    # Input
    topic: str
    team_name: str
    member_profile: Any
    team_focus: Any
    candidate_argument: str
    
    # Intermediate results
    initial_analysis: str
    evidence_evaluation: str
    logical_analysis: str
    persuasiveness_analysis: str
    strategic_analysis: str
    improvement_analysis: str
    
    # Final result
    evaluation_result: UnifiedArgumentEvaluation


def step1_initial_analysis(state: ChainOfThoughtEvaluationState) -> ChainOfThoughtEvaluationState:
    """Step 1: Initial argument analysis"""
    topic = state["topic"]
    team_name = state["team_name"]
    member_profile = state["member_profile"]
    team_focus = state["team_focus"]
    candidate_argument = state["candidate_argument"]
    
    prompt = f"""
        You are an expert evaluator performing the first step of a comprehensive argument evaluation.

        TOPIC: {topic}
        TEAM: {team_name}
        TEAM TYPE: {team_focus.team_type}
        PERSPECTIVE: {team_focus.perspective_description}

        MEMBER PROFILE:
        - Name: {member_profile.name}
        - Role: {member_profile.current_role}
        - Expertise: {', '.join(member_profile.expertise_domains)}
        - Thinking Style: {member_profile.thinking_style}
        - Core Values: {', '.join(member_profile.core_values)}

        ARGUMENT TO EVALUATE:
        {candidate_argument}

        STEP 1 - INITIAL ANALYSIS:
        Please provide a comprehensive initial analysis covering:

        1. ARGUMENT IDENTIFICATION:
        - What is the main claim being made?
        - What are the supporting premises?
        - What is the conclusion?

        2. PERSPECTIVE ALIGNMENT:
        - How well does this argument align with your team's perspective?
        - Does it support your team's position effectively?
        - Are there any misalignments or contradictions?

        3. EVIDENCE OVERVIEW:
        - What types of evidence are presented?
        - Are the evidence sources credible?
        - Is there sufficient evidence to support the claims?

        4. INITIAL IMPRESSIONS:
        - What are the strongest aspects of this argument?
        - What are the most obvious weaknesses?
        - What is your overall first impression?

        Please provide a detailed analysis that will inform the subsequent evaluation steps.
    """

    response = gpt_4o_mini.invoke(prompt)
    analysis_text = response.content if hasattr(response, 'content') else str(response)
    
    state["initial_analysis"] = analysis_text
    print(f"🧠 Step 1 - Initial Analysis completed for {member_profile.name}")
    
    return state


def step2_evidence_evaluation(state: ChainOfThoughtEvaluationState) -> ChainOfThoughtEvaluationState:
    """Step 2: Evidence quality evaluation"""
    topic = state["topic"]
    member_profile = state["member_profile"]
    team_focus = state["team_focus"]
    candidate_argument = state["candidate_argument"]
    initial_analysis = state["initial_analysis"]
    
    prompt = f"""
        You are an expert evaluator performing evidence quality assessment.

        CONTEXT FROM STEP 1:
        {initial_analysis}

        TOPIC: {topic}
        ARGUMENT TO EVALUATE:
        {candidate_argument}

        MEMBER PROFILE:
        - Preferred Evidence Types: {', '.join(member_profile.preferred_evidence_types)}
        - Decision Making Style: {member_profile.decision_making_style}
        - Risk Tolerance: {member_profile.risk_tolerance}

        TEAM EVIDENCE PREFERENCES:
        {', '.join(team_focus.evidence_preferences)}

        STEP 2 - EVIDENCE EVALUATION:
        Based on the initial analysis, provide a detailed evidence assessment:

        1. EVIDENCE CREDIBILITY:
        - Rate the credibility of each piece of evidence (1-10)
        - Identify any questionable or weak evidence
        - Note any missing citations or sources

        2. EVIDENCE RELEVANCE:
        - How relevant is each piece of evidence to the main claim?
        - Does the evidence directly support the conclusion?
        - Are there any irrelevant or tangential points?

        3. EVIDENCE SUFFICIENCY:
        - Is there enough evidence to support the claims?
        - What additional evidence would strengthen the argument?
        - Are there any gaps in the evidence chain?

        4. EVIDENCE QUALITY SCORE:
        - Provide an overall evidence quality score (0-100)
        - Justify your scoring with specific examples
        - Identify the strongest and weakest evidence

        Please provide a comprehensive evidence evaluation.
    """

    response = gpt_4o_mini.invoke(prompt)
    evidence_text = response.content if hasattr(response, 'content') else str(response)
    
    state["evidence_evaluation"] = evidence_text
    print(f"🔍 Step 2 - Evidence Evaluation completed for {member_profile.name}")
    
    return state


def step3_logical_analysis(state: ChainOfThoughtEvaluationState) -> ChainOfThoughtEvaluationState:
    """Step 3: Logical coherence analysis"""
    topic = state["topic"]
    member_profile = state["member_profile"]
    candidate_argument = state["candidate_argument"]
    initial_analysis = state["initial_analysis"]
    evidence_evaluation = state["evidence_evaluation"]
    
    prompt = f"""
        You are an expert evaluator performing logical analysis.

        CONTEXT FROM PREVIOUS STEPS:
        Initial Analysis: {initial_analysis}
        Evidence Evaluation: {evidence_evaluation}

        TOPIC: {topic}

        ARGUMENT TO EVALUATE:
        {candidate_argument}

        MEMBER PROFILE:
        - Thinking Style: {member_profile.thinking_style}
        - Philosophical Stance: {member_profile.philosophical_stance}
        - Decision Making Style: {member_profile.decision_making_style}

        STEP 3 - LOGICAL ANALYSIS:
        Provide a detailed logical coherence assessment:

        1. LOGICAL STRUCTURE:
        - Map out the logical flow of the argument
        - Identify the logical connections between premises and conclusion
        - Note any logical gaps or weak links

        2. FALLACY DETECTION:
        - Look for common logical fallacies
        - Identify any reasoning errors
        - Note any unsupported leaps in logic

        3. PREMISE VALIDITY:
        - Evaluate the truth value of each premise
        - Check for hidden assumptions
        - Identify any questionable premises

        4. CONCLUSION VALIDITY:
        - Does the conclusion follow logically from the premises?
        - Is the conclusion well-supported?
        - Are there alternative conclusions possible?

        5. LOGICAL COHERENCE SCORE:
        - Provide an overall logical coherence score (0-100)
        - Justify your scoring with specific examples
        - Identify the strongest and weakest logical elements

        Please provide a comprehensive logical analysis.
    """

    response = gpt_4o_mini.invoke(prompt)
    logical_text = response.content if hasattr(response, 'content') else str(response)
    
    state["logical_analysis"] = logical_text
    print(f"⚖️ Step 3 - Logical Analysis completed for {member_profile.name}")
    
    return state


def step4_persuasiveness_analysis(state: ChainOfThoughtEvaluationState) -> ChainOfThoughtEvaluationState:
    """Step 4: Persuasiveness assessment"""
    topic = state["topic"]
    member_profile = state["member_profile"]
    team_focus = state["team_focus"]
    candidate_argument = state["candidate_argument"]
    previous_analyses = f"Initial: {state['initial_analysis']}\nEvidence: {state['evidence_evaluation']}\nLogical: {state['logical_analysis']}"
    
    prompt = f"""
        You are an expert evaluator assessing argument persuasiveness.

        CONTEXT FROM PREVIOUS STEPS:
        {previous_analyses}

        TOPIC: {topic}

        ARGUMENT TO EVALUATE:
        {candidate_argument}

        MEMBER PROFILE:
        - Communication Style: {member_profile.communication_style}
        - Argumentation Preference: {member_profile.argumentation_preference}
        - Rhetorical Emphasis: {team_focus.rhetorical_emphasis}

        TEAM FOCUS:
        - Focus Keywords: {', '.join(team_focus.focus_keywords)}
        - Avoid Keywords: {', '.join(team_focus.avoid_keywords)}
        - Counterargument Strategy: {team_focus.counterargument_strategy}

        STEP 4 - PERSUASIVENESS ANALYSIS:
        Evaluate the argument's persuasive power:

        1. AUDIENCE APPEAL:
        - How compelling would this be for your target audience?
        - Does it address audience concerns and values?
        - Is the tone and style appropriate?

        2. EMOTIONAL IMPACT:
        - What emotional appeals are used?
        - Are they effective and appropriate?
        - Do they complement or undermine the logical structure?

        3. RHETORICAL EFFECTIVENESS:
        - How well does it use rhetorical techniques?
        - Is the language clear and compelling?
        - Does it avoid problematic terms from your avoid list?

        4. COUNTERARGUMENT HANDLING:
        - How well does it address potential objections?
        - Does it follow your team's counterargument strategy?
        - Are there missed opportunities to strengthen the position?

        5. PERSUASIVENESS SCORE:
        - Provide an overall persuasiveness score (0-100)
        - Justify your scoring with specific examples
        - Identify the most and least persuasive elements

        Please provide a comprehensive persuasiveness analysis.
    """

    response = gpt_4o_mini.invoke(prompt)
    persuasiveness_text = response.content if hasattr(response, 'content') else str(response)
    
    state["persuasiveness_analysis"] = persuasiveness_text
    print(f"💬 Step 4 - Persuasiveness Analysis completed for {member_profile.name}")
    
    return state


def step5_strategic_analysis(state: ChainOfThoughtEvaluationState) -> ChainOfThoughtEvaluationState:
    """Step 5: Strategic value assessment"""
    topic = state["topic"]
    member_profile = state["member_profile"]
    team_focus = state["team_focus"]
    candidate_argument = state["candidate_argument"]
    previous_analyses = f"Initial: {state['initial_analysis']}\nEvidence: {state['evidence_evaluation']}\nLogical: {state['logical_analysis']}\nPersuasiveness: {state['persuasiveness_analysis']}"
    
    prompt = f"""
        You are an expert evaluator assessing strategic value.

        CONTEXT FROM PREVIOUS STEPS:
        {previous_analyses}

        TOPIC: {topic}

        ARGUMENT TO EVALUATE:
        {candidate_argument}

        MEMBER PROFILE:
        - Current Role: {member_profile.current_role}
        - Communication Style: {member_profile.communication_style}
        - Argumentation Preference: {member_profile.argumentation_preference}
        - Rhetorical Emphasis: {team_focus.rhetorical_emphasis}
        - Risk Tolerance: {member_profile.risk_tolerance}

        TEAM FOCUS:
        - Priority Aspects: {', '.join(team_focus.priority_aspects)}
        - Interests and Concerns: {', '.join(team_focus.interests_and_concerns)}
        - Typical Arguments: {', '.join(team_focus.typical_arguments)}

        STEP 5 - STRATEGIC ANALYSIS:
        Evaluate the argument's strategic value:

        1. TEAM ALIGNMENT:
        - How well does this advance your team's position?
        - Does it address your priority aspects effectively?
        - Does it align with your typical argumentation style?

        2. COMPETITIVE ADVANTAGE:
        - What advantages does this argument provide?
        - How might it differentiate you from opponents?
        - What unique value does it offer?

        3. RISK ASSESSMENT:
        - What are the potential risks of using this argument?
        - How might opponents counter it?
        - What vulnerabilities does it expose?

        4. OPPORTUNITY ANALYSIS:
        - What opportunities does this argument create?
        - How can it be leveraged for maximum impact?
        - What follow-up arguments does it enable?

        5. STRATEGIC VALUE SCORE:
        - Provide an overall strategic value score (0-100)
        - Justify your scoring with specific examples
        - Identify the most and least strategic elements

        Please provide a comprehensive strategic analysis.
    """

    response = gpt_4o_mini.invoke(prompt)
    strategic_text = response.content if hasattr(response, 'content') else str(response)
    
    state["strategic_analysis"] = strategic_text
    print(f"🎯 Step 5 - Strategic Analysis completed for {member_profile.name}")
    
    return state


def step6_improvement_analysis(state: ChainOfThoughtEvaluationState) -> ChainOfThoughtEvaluationState:
    """Step 6: Improvement recommendations"""
    topic = state["topic"]
    member_profile = state["member_profile"]
    team_focus = state["team_focus"]
    candidate_argument = state["candidate_argument"]
    all_analyses = f"""
        Initial Analysis: {state['initial_analysis']}
        Evidence Evaluation: {state['evidence_evaluation']}
        Logical Analysis: {state['logical_analysis']}
        Persuasiveness Analysis: {state['persuasiveness_analysis']}
        Strategic Analysis: {state['strategic_analysis']}
        """
            
    prompt = f"""
        You are an expert evaluator providing improvement recommendations.

        CONTEXT FROM ALL PREVIOUS STEPS:
        {all_analyses}

        TOPIC: {topic}

        ARGUMENT TO EVALUATE:
        {candidate_argument}

        MEMBER PROFILE:
        - Name: {member_profile.name}
        - Expertise: {', '.join(member_profile.expertise_domains)}
        - Typical Counterargument Approach: {member_profile.typical_counterargument_approach}

        TEAM FOCUS:
        - Counterargument Strategy: {team_focus.counterargument_strategy}
        - Evidence Preferences: {', '.join(team_focus.evidence_preferences)}

        STEP 6 - IMPROVEMENT ANALYSIS:
        Based on all previous analyses, provide comprehensive improvement recommendations:

        1. CRITICAL IMPROVEMENTS:
        - What are the most important changes needed?
        - Which issues must be addressed for the argument to be effective?
        - What are the deal-breakers that need fixing?

        2. STRENGTHENING OPPORTUNITIES:
        - How can the strongest elements be enhanced further?
        - What additional evidence would be most valuable?
        - How can the logical structure be improved?

        3. STRATEGIC ENHANCEMENTS:
        - How can the argument be made more strategically valuable?
        - What tactical improvements would increase impact?
        - How can it better align with team objectives?

        4. RISK MITIGATION:
        - How can identified risks be minimized?
        - What defensive elements should be added?
        - How can vulnerabilities be addressed?

        5. IMPLEMENTATION PRIORITIES:
        - Rank improvements by priority and impact
        - Suggest specific, actionable changes
        - Identify quick wins vs. major overhauls

        Please provide detailed, actionable improvement recommendations.
    """

    response = gpt_4o_mini.invoke(prompt)
    improvement_text = response.content if hasattr(response, 'content') else str(response)
    
    state["improvement_analysis"] = improvement_text
    print(f"🔧 Step 6 - Improvement Analysis completed for {member_profile.name}")
    
    return state


def step7_final_synthesis(state: ChainOfThoughtEvaluationState) -> ChainOfThoughtEvaluationState:
    """Step 7: Final synthesis and scoring"""
    member_profile = state["member_profile"]
    candidate_argument = state["candidate_argument"]
    
    all_analyses = f"""
        Initial Analysis: {state['initial_analysis']}
        Evidence Evaluation: {state['evidence_evaluation']}
        Logical Analysis: {state['logical_analysis']}
        Persuasiveness Analysis: {state['persuasiveness_analysis']}
        Strategic Analysis: {state['strategic_analysis']}
        Improvement Analysis: {state['improvement_analysis']}
        """
            
    prompt = f"""
        You are an expert evaluator providing the final synthesis and scoring.

        CONTEXT FROM ALL PREVIOUS STEPS:
        {all_analyses}

        ARGUMENT TO EVALUATE:
        {candidate_argument}

        MEMBER PROFILE:
        - Name: {member_profile.name}
        - Core Values: {', '.join(member_profile.core_values)}
        - Philosophical Stance: {member_profile.philosophical_stance}

        STEP 7 - FINAL SYNTHESIS:
        Based on all previous analyses, provide the final evaluation:

        1. OVERALL ASSESSMENT:
        - Synthesize all previous analyses into a coherent evaluation
        - Identify the key strengths and weaknesses
        - Provide an overall quality assessment

        2. DETAILED SCORING:
        - Evidence Quality: Score (0-100) with justification
        - Logical Coherence: Score (0-100) with justification  
        - Persuasiveness: Score (0-100) with justification
        - Strategic Value: Score (0-100) with justification
        - Overall Score: Weighted average (0-100)

        3. FINAL RECOMMENDATION:
        - EXCELLENT (80-100): Use as-is, minor tweaks only
        - GOOD (70-79): Use with moderate improvements
        - ACCEPTABLE (60-69): Use with significant improvements
        - POOR (40-59): Major revision needed
        - REJECT (0-39): Not suitable for use

        4. KEY STRENGTHS:
        - List the top 3-5 strengths
        - Explain why they are valuable

        5. CRITICAL WEAKNESSES:
        - List the top 3-5 weaknesses
        - Explain why they are problematic

        6. IMPROVEMENT PRIORITIES:
        - List the top 3-5 improvement recommendations
        - Explain their expected impact

        Please provide a comprehensive final evaluation with specific scores and clear recommendations.
    """

    response = gpt_4o_mini.invoke(prompt)
    final_text = response.content if hasattr(response, 'content') else str(response)
    
    # Create evaluation result from the final synthesis
    evaluation_result = _create_evaluation_result_from_synthesis(final_text, all_analyses, candidate_argument)
    
    state["evaluation_result"] = evaluation_result
    print(f"🎯 Step 7 - Final Synthesis completed for {member_profile.name}")
    print(f"   Overall Score: {evaluation_result.overall_score:.1f}/100")
    print(f"   Final Result: {evaluation_result.final_result.value}")
    
    return state


def create_chain_of_thought_evaluation_workflow() -> StateGraph:
    """Create the chain-of-thought evaluation workflow"""
    workflow = StateGraph(ChainOfThoughtEvaluationState)
    
    workflow.add_node("step1_initial_analysis", step1_initial_analysis)
    workflow.add_node("step2_evidence_evaluation", step2_evidence_evaluation)
    workflow.add_node("step3_logical_analysis", step3_logical_analysis)
    workflow.add_node("step4_persuasiveness_analysis", step4_persuasiveness_analysis)
    workflow.add_node("step5_strategic_analysis", step5_strategic_analysis)
    workflow.add_node("step6_improvement_analysis", step6_improvement_analysis)
    workflow.add_node("step7_final_synthesis", step7_final_synthesis)
    

    workflow.add_edge(START, "step1_initial_analysis")
    workflow.add_edge("step1_initial_analysis", "step2_evidence_evaluation")
    workflow.add_edge("step2_evidence_evaluation", "step3_logical_analysis")
    workflow.add_edge("step3_logical_analysis", "step4_persuasiveness_analysis")
    workflow.add_edge("step4_persuasiveness_analysis", "step5_strategic_analysis")
    workflow.add_edge("step5_strategic_analysis", "step6_improvement_analysis")
    workflow.add_edge("step6_improvement_analysis", "step7_final_synthesis")
    workflow.add_edge("step7_final_synthesis", END)
    
    return workflow.compile()


def chain_of_thought_evaluator_node(state: TeamMemberState) -> TeamMemberState:
    """
    Chain of thought based evaluator that replaces GoDsAF evaluation
    Uses a 7-step workflow with sequential LLM calls for comprehensive evaluation
    """
    topic = state["topic"]
    team_name = state["team_name"]
    member_profile = state["knowledge_retrival_context"].member_profile
    team_focus = state["knowledge_retrival_context"].team_focus
    candidate_argument = state["argument_creator_results"]["final_argument"]
    
    # Create initial state for the chain-of-thought workflow
    initial_eval_state = ChainOfThoughtEvaluationState(
        topic=topic,
        team_name=team_name,
        member_profile=member_profile,
        team_focus=team_focus,
        candidate_argument=candidate_argument,
        initial_analysis="",
        evidence_evaluation="",
        logical_analysis="",
        persuasiveness_analysis="",
        strategic_analysis="",
        improvement_analysis="",
        evaluation_result=None
    )
    
    # Run the chain-of-thought evaluation workflow
    workflow = create_chain_of_thought_evaluation_workflow()
    final_eval_state = workflow.invoke(initial_eval_state)
    
    # Update the original state with the evaluation result
    evaluation_result = final_eval_state["evaluation_result"]
    evaluation_result.topic = topic  # Set the topic
    state["evaluator_results"] = evaluation_result
    
    # # Save argument to godsaf service if available (for audience voting)
    # if state.get("af") and state.get("candidate_id"):
    #     _save_argument_to_godsaf_from_state(state, candidate_argument, team_name, topic)
    
    print(f"🔍 Chain of Thought Evaluation completed for {member_profile.name}")
    print(f"   Overall Score: {evaluation_result.overall_score:.1f}/100")
    print(f"   Final Result: {evaluation_result.final_result.value}")
    
    return state


def _create_evaluation_result_from_synthesis(final_text: str, all_analyses: str, candidate_argument: str) -> UnifiedArgumentEvaluation:
    """Create evaluation result from the final synthesis text"""

    # Extract scores using improved parsing
    scores = _extract_scores_from_synthesis(final_text)

    # Extract strengths and weaknesses
    strengths = _extract_strengths_from_synthesis(final_text)
    weaknesses = _extract_weaknesses_from_synthesis(final_text)

    # Extract improvement suggestions
    improvement_suggestions = _extract_improvement_suggestions_from_synthesis(final_text)

    # Extract strategic recommendations
    strategic_recommendations = _extract_strategic_recommendations_from_synthesis(final_text)

    # Extract rejection factors
    rejection_factors = _extract_rejection_factors_from_synthesis(final_text)

    # Calculate overall score
    overall_score = scores.get('overall', sum(scores.values()) / len(scores) if scores else 50.0)

    # Determine final result
    if overall_score >= 80:
        final_result = EvaluationResult.EXCELLENT
    elif overall_score >= 70:
        final_result = EvaluationResult.GOOD
    elif overall_score >= 60:
        final_result = EvaluationResult.FAIR
    elif overall_score >= 40:
        final_result = EvaluationResult.POOR
    else:
        final_result = EvaluationResult.REJECT

    # Create EvaluationScore objects from the extracted scores
    individual_scores = []
    for dimension, score in scores.items():
        if dimension != 'overall':  # Skip overall, it's stored separately
            individual_scores.append(EvaluationScore(
                evaluator_name="Chain_of_Thought_Evaluator",
                dimension=dimension,
                score=score,
                raw_score=score,
                justification=f"Extracted from chain-of-thought {dimension} analysis",
                confidence=0.9
            ))

    return UnifiedArgumentEvaluation(
        argument_text=candidate_argument,
        topic="",  # Will be set by caller
        overall_score=overall_score,
        final_result=final_result,
        individual_scores=individual_scores,
        strengths=strengths,
        weaknesses=weaknesses,
        improvement_suggestions=improvement_suggestions,
        strategic_recommendations=strategic_recommendations,
        rejection_factors=rejection_factors,
        evaluation_summary=final_text
    )


def _extract_scores_from_synthesis(final_text: str) -> Dict[str, float]:
    """Extract numerical scores from final synthesis text"""
    scores = {}
    lines = final_text.split('\n')
    
    # Look for score patterns in the detailed scoring section
    for line in lines:
        line = line.strip()
        if ':' in line and any(keyword in line.lower() for keyword in ['score', 'quality', 'coherence', 'persuasiveness', 'strategic', 'overall']):
            # Try to extract numerical scores
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', line)
            if numbers:
                score_value = float(numbers[0])
                if 'evidence' in line.lower() or 'quality' in line.lower():
                    scores['evidence_quality'] = score_value
                elif 'logical' in line.lower() or 'coherence' in line.lower():
                    scores['logical_coherence'] = score_value
                elif 'persuasive' in line.lower():
                    scores['persuasiveness'] = score_value
                elif 'strategic' in line.lower():
                    scores['strategic_value'] = score_value
                elif 'overall' in line.lower():
                    scores['overall'] = score_value
    
    # If no scores found, create default scores based on text analysis
    if not scores:
        scores = _create_default_scores_from_synthesis(final_text)
    
    return scores


def _create_default_scores_from_synthesis(final_text: str) -> Dict[str, float]:
    """Create default scores based on final synthesis text analysis"""
    scores = {}
    text_lower = final_text.lower()
    
    # Evidence quality
    if 'excellent evidence' in text_lower or 'strong evidence' in text_lower:
        scores['evidence_quality'] = 85.0
    elif 'good evidence' in text_lower or 'solid evidence' in text_lower:
        scores['evidence_quality'] = 75.0
    elif 'weak evidence' in text_lower or 'insufficient evidence' in text_lower:
        scores['evidence_quality'] = 45.0
    else:
        scores['evidence_quality'] = 65.0
    
    # Logical coherence
    if 'logically sound' in text_lower or 'well-reasoned' in text_lower:
        scores['logical_coherence'] = 85.0
    elif 'logical' in text_lower and 'good' in text_lower:
        scores['logical_coherence'] = 75.0
    elif 'logical flaw' in text_lower or 'fallacy' in text_lower:
        scores['logical_coherence'] = 45.0
    else:
        scores['logical_coherence'] = 65.0
    
    # Persuasiveness
    if 'very persuasive' in text_lower or 'highly compelling' in text_lower:
        scores['persuasiveness'] = 85.0
    elif 'persuasive' in text_lower or 'compelling' in text_lower:
        scores['persuasiveness'] = 75.0
    elif 'not persuasive' in text_lower or 'weak argument' in text_lower:
        scores['persuasiveness'] = 45.0
    else:
        scores['persuasiveness'] = 65.0
    
    # Strategic value
    if 'strategically valuable' in text_lower or 'excellent strategy' in text_lower:
        scores['strategic_value'] = 85.0
    elif 'strategic' in text_lower and 'good' in text_lower:
        scores['strategic_value'] = 75.0
    elif 'strategic weakness' in text_lower or 'poor strategy' in text_lower:
        scores['strategic_value'] = 45.0
    else:
        scores['strategic_value'] = 65.0
    
    # Overall score
    scores['overall'] = sum(scores.values()) / len(scores)
    
    return scores


def _extract_strengths_from_synthesis(final_text: str) -> List[str]:
    """Extract strengths from final synthesis text"""
    strengths = []
    lines = final_text.split('\n')
    
    in_strengths_section = False
    for line in lines:
        line = line.strip()
        if 'strength' in line.lower() and ('key' in line.lower() or 'top' in line.lower()):
            in_strengths_section = True
            continue
        elif in_strengths_section and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
            strength = line.lstrip('-•*1234567890.').strip()
            if strength and len(strength) > 10:
                strengths.append(strength)
        elif in_strengths_section and line == '':
            in_strengths_section = False
    
    return strengths[:8]


def _extract_weaknesses_from_synthesis(final_text: str) -> List[str]:
    """Extract weaknesses from final synthesis text"""
    weaknesses = []
    lines = final_text.split('\n')
    
    in_weaknesses_section = False
    for line in lines:
        line = line.strip()
        if 'weakness' in line.lower() and ('critical' in line.lower() or 'key' in line.lower()):
            in_weaknesses_section = True
            continue
        elif in_weaknesses_section and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
            weakness = line.lstrip('-•*1234567890.').strip()
            if weakness and len(weakness) > 10:
                weaknesses.append(weakness)
        elif in_weaknesses_section and line == '':
            in_weaknesses_section = False
    
    return weaknesses[:8]


def _extract_improvement_suggestions_from_synthesis(final_text: str) -> List[str]:
    """Extract improvement suggestions from final synthesis text"""
    suggestions = []
    lines = final_text.split('\n')
    
    in_suggestions_section = False
    for line in lines:
        line = line.strip()
        if 'improvement' in line.lower() and ('priority' in line.lower() or 'recommendation' in line.lower()):
            in_suggestions_section = True
            continue
        elif in_suggestions_section and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
            suggestion = line.lstrip('-•*1234567890.').strip()
            if suggestion and len(suggestion) > 10:
                suggestions.append(suggestion)
        elif in_suggestions_section and line == '':
            in_suggestions_section = False
    
    return suggestions[:8]


def _extract_strategic_recommendations_from_synthesis(final_text: str) -> List[str]:
    """Extract strategic recommendations from final synthesis text"""
    recommendations = []
    lines = final_text.split('\n')
    
    in_strategy_section = False
    for line in lines:
        line = line.strip()
        if 'strategic' in line.lower() and 'recommendation' in line.lower():
            in_strategy_section = True
            continue
        elif in_strategy_section and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
            rec = line.lstrip('-•*1234567890.').strip()
            if rec and len(rec) > 10:
                recommendations.append(rec)
        elif in_strategy_section and line == '':
            in_strategy_section = False
    
    return recommendations[:6]


def _extract_rejection_factors_from_synthesis(final_text: str) -> List[str]:
    """Extract rejection factors from final synthesis text"""
    factors = []
    lines = final_text.split('\n')
    
    in_rejection_section = False
    for line in lines:
        line = line.strip()
        if 'reject' in line.lower() or 'critical' in line.lower() and 'weakness' in line.lower():
            in_rejection_section = True
            continue
        elif in_rejection_section and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
            factor = line.lstrip('-•*1234567890.').strip()
            if factor and len(factor) > 10:
                factors.append(factor)
        elif in_rejection_section and line == '':
            in_rejection_section = False
    
    return factors[:5]


class ChainOfThoughtEvaluatorAdapter(ArgumentEvaluatorInterface):
    """Adapter to make chain-of-thought evaluator compatible with the evaluator interface"""
    
    def __init__(self, llm, weight: float = 0.4, godsaf_service=None):
        self.llm = llm
        self.weight = weight
        self.godsaf_service = godsaf_service
        self.evaluator_name = "Chain_of_Thought_Evaluator"
    
    def evaluator_name(self):
        return self.evaluator_name

    def weight(self):
        return self.weight

    def evaluate(self, argument: Argument, **kwargs) -> Dict[str, Any]:
        """Evaluate argument using chain-of-thought approach"""
        
        mock_state = {
            "topic": argument.topic,
            "team_name": kwargs.get("team_name", "unknown_team"),
            "knowledge_retrival_context": type('obj', (object,), {
                'member_profile': type('obj', (object,), {
                    'name': 'Chain of Thought Evaluator',
                    'current_role': 'Evaluator',
                    'expertise_domains': ['argumentation', 'evaluation', 'critical thinking'],
                    'thinking_style': 'analytical',
                    'core_values': ['accuracy', 'thoroughness', 'fairness'],
                    'philosophical_stance': 'pragmatic',
                    'preferred_evidence_types': ['research', 'data', 'expert opinion'],
                    'decision_making_style': 'evidence-based',
                    'risk_tolerance': 'moderate',
                    'communication_style': 'analytical',
                    'argumentation_preference': 'evidence-heavy',
                    'typical_counterargument_approach': 'systematic analysis'
                })(),
                'team_focus': type('obj', (object,), {
                    'team_type': 'evaluator',
                    'perspective_description': 'Comprehensive argument evaluation',
                    'priority_aspects': ['logical coherence', 'evidence quality', 'persuasiveness'],
                    'interests_and_concerns': ['argument effectiveness', 'logical soundness'],
                    'typical_arguments': ['evidence-based reasoning'],
                    'evidence_preferences': ['research studies', 'expert opinions', 'statistical data'],
                    'counterargument_strategy': 'systematic analysis',
                    'rhetorical_emphasis': 'logical',
                    'focus_keywords': ['evidence', 'logic', 'reasoning'],
                    'avoid_keywords': ['bias', 'fallacy', 'weakness']
                })()
            })(),
            "argument_creator_results": {
                "final_argument": argument.text
            },
            "af": self.godsaf_service,
            "candidate_id": kwargs.get("candidate_id")
        }
        
        result = chain_of_thought_evaluator_node(mock_state)
        evaluation_result = result["evaluator_results"]

        dimensions = evaluation_result.individual_scores if evaluation_result.individual_scores else []

        # If no scores were extracted, create default scores as fallback
        if not dimensions:
            default_scores = {
                'evidence_quality': 50.0,
                'logical_coherence': 50.0,
                'persuasiveness': 50.0,
                'strategic_value': 50.0
            }

            for dimension, score in default_scores.items():
                dimensions.append(EvaluationScore(
                    evaluator_name=self.evaluator_name,
                    dimension=dimension,
                    score=score,
                    raw_score=score,
                    justification=f"Default score - failed to extract from chain-of-thought analysis",
                    confidence=0.5
                ))

        return {
            "overall_score": evaluation_result.overall_score,
            "dimensions": dimensions,
            "feedback": {
                "positive": evaluation_result.strengths,
                "negative": evaluation_result.weaknesses,
                "improvements": evaluation_result.improvement_suggestions,
                "strategic": evaluation_result.strategic_recommendations
            },
            "metadata": {
                "evaluation_type": "chain_of_thought",
                "steps_completed": 7,
                "final_result": evaluation_result.final_result.value
            }
        }
    
    # def _save_argument_to_godsaf(self, argument: Argument, kwargs: Dict[str, Any]) -> None:
    #     """
    #     DEPRECATED: This method should not be used anymore.
    #     Candidate creation is now handled by candidate_creator_node.

    #     This method is kept for backward compatibility but logs a warning.
    #     """
    #     import logging
    #     logger = logging.getLogger(__name__)
    #     logger.warning(
    #         "[DEPRECATED] ChainOfThoughtEvaluatorAdapter._save_argument_to_godsaf is deprecated. "
    #         "Candidate creation is now handled by candidate_creator_node in the workflow."
    #     )
    #     print("⚠️ [DEPRECATED] _save_argument_to_godsaf called - candidate creation should be done by candidate_creator_node")

    #     # If this is still called for some reason, try to continue without breaking
    #     # In practice, this should never be called after refactoring
    #     try:
    #         # Extract parameters
    #         team_name = kwargs.get("team_name", "unknown_team")
    #         candidate_id = kwargs.get("candidate_id")
    #         existing_argument_names = kwargs.get("existing_argument_names", [])

    #         if not candidate_id:
    #             print("⚠️ Warning: No candidate_id provided, cannot save argument to godsaf service")
    #             return

    #         # Use centralized parser utility
    #         from agents.reasoning.miner.parser_utils import parse_argument

    #         # Get domains and goals from godsaf service
    #         domains = self.godsaf_service.list_domains()
    #         goals = self.godsaf_service.list_goals()

    #         parsed_arg_dict = parse_argument(
    #             topic=argument.topic,
    #             argument=argument.text,
    #             domains=domains,
    #             goals=goals,
    #             existing_arguments=existing_argument_names,
    #             domain_lookup=lambda d: self.godsaf_service.get_domain(d)
    #         )
            
    #         # Create a basic candidate argument for godsaf service
    #         from agents.reasoning.godsaf.godsaf_service import CandidateArgument

    #         # Use parsed domains and goals with validation
    #         domains = parsed_arg_dict.get("domains", ["general"])
    #         goals = parsed_arg_dict.get("goals", {"general_goal": ["general"]})

    #         # Validate and sanitize domains and goals to prevent ASP parsing errors
    #         domains = _validate_and_sanitize_identifiers(domains, "domain")
    #         goals = {_validate_and_sanitize_identifier(goal, "goal"):
    #                 [_validate_and_sanitize_identifier(domain, "domain") for domain in domain_list]
    #                 for goal, domain_list in goals.items()}
            
    #         # Recommend attacks using GoDsAF attack detector when possible
    #         attacks_set = set()
    #         try:
    #             evaluator = GoDsAFArgumentEvaluator(self.godsaf_service)
    #             strategy_rec = StrategyRecommendation(
    #                 team=team_name,
    #                 primary_ugns=[],
    #                 secondary_ugns=[],
    #                 analysis_summary="Chain-of-thought analysis mode"
    #             )
    #             parsed_for_detect = {
    #                 "domains": domains,
    #                 "goals": {g: set(ds) for g, ds in goals.items()},
    #             }
    #             attack_recommendations = evaluator._detect_potential_attacks(
    #                 parsed_for_detect, team_name, strategy_rec
    #             )
    #             attacks_set = {rec.target_argument for rec in attack_recommendations if rec.confidence >= 0.4}
    #         except Exception:
    #             attacks_set = set()

    #         # Validate and sanitize argument name
    #         arg_name = parsed_arg_dict.get("name", f"chain_of_thought_arg_{candidate_id}")
    #         arg_name = _validate_and_sanitize_identifier(arg_name, "a")
            
    #         candidate = CandidateArgument(
    #             name=arg_name,
    #             text=argument.text,
    #             team=team_name,
    #             domains=set(domains),
    #             goals={g: set(ds) for g, ds in goals.items()},
    #             attacks=attacks_set
    #         )
            
    #         # Save to godsaf service
    #         self.godsaf_service.set_candidate_argument(candidate_id, candidate)
    #         print(f"💾 Chain of Thought: Saved argument '{candidate.name}' to godsaf service for audience voting")
            
    #     except Exception as e:
    #         print(f"⚠️ Warning: Failed to save argument to godsaf service: {str(e)}")
    #         # Don't raise the exception to avoid breaking the evaluation


# def _save_argument_to_godsaf_from_state(state: TeamMemberState, candidate_argument: str, team_name: str, topic: str) -> None:
#     """
#     DEPRECATED: This function should not be used anymore.
#     Candidate creation is now handled by candidate_creator_node.

#     This function is kept for backward compatibility but logs a warning.
#     """
#     import logging
#     logger = logging.getLogger(__name__)
#     logger.warning(
#         "[DEPRECATED] _save_argument_to_godsaf_from_state is deprecated. "
#         "Candidate creation is now handled by candidate_creator_node in the workflow."
#     )
#     print("⚠️ [DEPRECATED] _save_argument_to_godsaf_from_state called - candidate creation should be done by candidate_creator_node")

#     try:
#         godsaf_service = state.get("af")
#         candidate_id = state.get("candidate_id")
#         existing_argument_names = godsaf_service.get_argument_names() if godsaf_service else []

#         if not godsaf_service:
#             print("⚠️ Warning: No godsaf service available in state")
#             return

#         if not candidate_id:
#             print("⚠️ Warning: No candidate_id in state, cannot save argument to godsaf service")
#             return

#         # Use centralized parser utility
#         from agents.reasoning.miner.parser_utils import parse_argument

#         # Get domains and goals from godsaf service
#         domains = godsaf_service.list_domains()
#         goals = godsaf_service.list_goals()

#         parsed_arg_dict = parse_argument(
#             topic=topic,
#             argument=candidate_argument,
#             domains=domains,
#             goals=goals,
#             existing_arguments=existing_argument_names,
#             domain_lookup=lambda d: godsaf_service.get_domain(d)
#         )
        
#         # Create a basic candidate argument for godsaf service
#         from agents.reasoning.godsaf.godsaf_service import CandidateArgument

#         # Use parsed domains and goals with validation
#         domains = parsed_arg_dict.get("domains", ["general"])
#         goals = parsed_arg_dict.get("goals", {"general_goal": ["general"]})

#         # Validate and sanitize domains and goals to prevent ASP parsing errors
#         domains = _validate_and_sanitize_identifiers(domains, "domain")
#         goals = {_validate_and_sanitize_identifier(goal, "goal"):
#                 [_validate_and_sanitize_identifier(domain, "domain") for domain in domain_list]
#                 for goal, domain_list in goals.items()}
        
#         # Recommend attacks using GoDsAF attack detector when possible
#         attacks_set = set()
#         try:
#             evaluator = GoDsAFArgumentEvaluator(godsaf_service)
#             strategy_rec = StrategyRecommendation(
#                 team=team_name,
#                 primary_ugns=[],
#                 secondary_ugns=[],
#                 analysis_summary="Chain-of-thought analysis mode"
#             )
#             parsed_for_detect = {
#                 "domains": domains,
#                 "goals": {g: set(ds) for g, ds in goals.items()},
#             }
#             attack_recommendations = evaluator._detect_potential_attacks(
#                 parsed_for_detect, team_name, strategy_rec
#             )
#             attacks_set = {rec.target_argument for rec in attack_recommendations if rec.confidence >= 0.4}
#         except Exception:
#             attacks_set = set()

#         # Validate and sanitize argument name
#         arg_name = parsed_arg_dict.get("name", f"chain_of_thought_arg_{candidate_id}")
#         arg_name = _validate_and_sanitize_identifier(arg_name, "a")
        
#         candidate = CandidateArgument(
#             name=arg_name,
#             text=candidate_argument,
#             team=team_name,
#             domains=set(domains),
#             goals={g: set(ds) for g, ds in goals.items()},
#             attacks=attacks_set
#         )
        
#         # Save to godsaf service
#         godsaf_service.set_candidate_argument(candidate_id, candidate)
#         print(f"💾 Chain of Thought Node: Saved argument '{candidate.name}' to godsaf service for audience voting")
        
#     except Exception as e:
#         print(f"⚠️ Warning: Failed to save argument to godsaf service from state: {str(e)}")
#         # Don't raise the exception to avoid breaking the evaluation


# def _validate_and_sanitize_identifier(identifier: str, prefix: str) -> str:
#     """Validate and sanitize a single identifier to be safe for ASP parsing"""
#     if not identifier or not isinstance(identifier, str):
#         return f"{prefix}_general"
    
#     # Remove any non-alphanumeric characters except underscores
#     sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(identifier))
    
#     # Ensure it starts with a letter or underscore
#     if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
#         sanitized = f"{prefix}_{sanitized}"
    
#     # Ensure it's not empty after sanitization
#     if not sanitized:
#         sanitized = f"{prefix}_general"
    
#     # Limit length to prevent issues
#     if len(sanitized) > 50:
#         sanitized = sanitized[:50]
    
#     # Check if it's purely numeric (which causes ASP parsing errors)
#     if sanitized.isdigit():
#         sanitized = f"{prefix}_{sanitized}"
    
#     return sanitized


# def _validate_and_sanitize_identifiers(identifiers: list, prefix: str) -> list:
#     """Validate and sanitize a list of identifiers"""
#     if not identifiers:
#         return [f"{prefix}_general"]
    
#     sanitized = []
#     for identifier in identifiers:
#         sanitized_id = _validate_and_sanitize_identifier(identifier, prefix)
#         if sanitized_id not in sanitized:  # Avoid duplicates
#             sanitized.append(sanitized_id)
    
#     # Ensure we have at least one valid identifier
#     if not sanitized:
#         sanitized = [f"{prefix}_general"]
    
#     return sanitized
