"""
Tree of Thoughts Candidate Creator Node

For ToT architecture, this node creates candidate from variations:
- If evaluation is ON: Creates initial candidate from first variation (evaluator updates later)
- If evaluation is OFF: Uses LLM to select best variation from all available
"""

import logging
import json
from typing import Dict, List, Any
from langchain_core.prompts import PromptTemplate

from src.reasoning.miner.argument_miner import Argument
from src.team_extended.common.evaluator.godsaf.godsaf_evaluator import AttackRecommendation
from src.team_extended.common.state import TeamMemberState
from src.reasoning.godsaf.godsaf_service import CandidateArgument
from src.reasoning.miner.parser_utils import parse_argument
from src.team_extended.common.team_member import StrategyRecommendation
from src.team_extended.common.metrics.token_tracking import WorkflowNode, create_node_tracker

logger = logging.getLogger(__name__)


def candidate_creator_node(state: TeamMemberState) -> TeamMemberState:
    """
    ToT-specific candidate creator that works with argument variations.

    This creates an initial candidate from the first variation. The evaluator
    will later update the candidate with the best selected variation.

    For ToT, state contains:
    - state["tot_argument_variations"]: List of variation dicts with structure:
        {
            "variation_id": str,
            "branch_id": str,
            "strategy": str,
            "strategy_name": str,
            "argument_text": str,  # The actual argument
            "domain_goal_pairs": List[Tuple[str, str]],
            "full_state": Dict  # Contains "final_argument" and other data
        }
    """
    member_name = state.get("team_member_name", "unknown")
    team_name = state.get("team_name", "unknown")
    af = state.get("af")

    logger.info(f"[ToT CANDIDATE CREATOR] Starting for {member_name}")

    # Create token tracker for this node
    token_tracker = create_node_tracker(WorkflowNode.CANDIDATE_CREATOR)

    if not af:
        logger.error(f"[ToT CANDIDATE CREATOR] No GoDsAF service found for {member_name}")
        return state

    # Get argument variations
    variations = state.get("tot_argument_variations", [])

    if not variations:
        logger.error(f"[ToT CANDIDATE CREATOR] No argument variations found for {member_name}")
        return state

    candidate_id = state.get("candidate_id")
    if not candidate_id:
        logger.error(f"[ToT CANDIDATE CREATOR] No candidate_id found")
        return state

    selected_variation = _select_best_variation_with_llm(
        variations=variations,
        topic=state.get("topic", ""),
        llm=state.get("argument_creation_llm"),
        token_tracker=token_tracker
    )
    logger.info(f"[ToT CANDIDATE CREATOR] LLM selected variation: {selected_variation.get('variation_id')}") 

    # Extract argument text from selected variation
    argument_text = selected_variation.get("argument_text", "")

    if not argument_text:
        # Fallback: try to get from full_state
        full_state = selected_variation.get("full_state", {})
        argument_text = full_state.get("final_argument", "")

    if not argument_text:
        logger.error(f"[ToT CANDIDATE CREATOR] No argument text in selected variation")
        return state

    logger.info(f"[ToT CANDIDATE CREATOR] Creating candidate from variation: {selected_variation.get('variation_id')}")

    try:
        domains = af.list_domains()
        goals = af.list_goals()
        existing_names = af.get_argument_names()
        topic = state["topic"]
        strategy_recommendation = state.get("strategy_recommendation")

        # Parse the argument to extract domains, goals, and structure
        # This uses LLM internally and we need to track tokens
        parsed_arg: Argument = parse_argument(
            topic=topic,
            argument=argument_text,
            domains=domains,
            goals=goals,
            existing_arguments=list(existing_names),
            domain_lookup=lambda d: af.get_domain(d)
        )

        # Note: parse_argument may use LLM but doesn't expose token usage
        # We'll track what we can here

        # Handle name conflicts
        original_name = parsed_arg.name
        if original_name in existing_names:
            base_name = original_name
            max_suffix = 0

            for existing_name in existing_names:
                if existing_name.startswith(base_name + "_"):
                    try:
                        suffix = int(existing_name[len(base_name + "_"):])
                        max_suffix = max(max_suffix, suffix)
                    except ValueError:
                        continue

            parsed_arg.name = f"{base_name}_{max_suffix + 1}"

        # Detect potential attacks
        attacks_set = set()
        if strategy_recommendation:
            attack_recommendations = detect_potential_attacks(
                af, parsed_arg, team_name, strategy_recommendation
            )

            attacks_set = {
                rec.target_argument for rec in attack_recommendations
                if rec.confidence >= 0.4
            }

        # Create initial candidate (will be updated by evaluator with best variation)
        candidate = CandidateArgument(
            name=parsed_arg.name,
            text=argument_text,
            team=team_name,
            domains=set(parsed_arg.domains),
            goals={gm.goal: set(gm.domains) for gm in parsed_arg.goals},
            attacks=attacks_set
        )

        # Store candidate in GoDsAF service
        af.set_candidate_argument(candidate_id, candidate)

        logger.info(f"[ToT CANDIDATE CREATOR] Created initial candidate: {parsed_arg.name} (will be updated by evaluator)")

    except Exception as e:
        logger.error(f"[ToT CANDIDATE CREATOR] Failed to create candidate for {member_name}: {e}")
        import traceback
        traceback.print_exc()

    # Finalize token tracker
    node_usage = token_tracker.finalize()

    # Store node token usage
    if "node_token_usage" not in state:
        state["node_token_usage"] = {}
    state["node_token_usage"][WorkflowNode.CANDIDATE_CREATOR] = node_usage

    logger.info(f"[ToT CANDIDATE CREATOR] Completed for {member_name} - "
               f"Time: {node_usage.elapsed_time_seconds:.2f}s, "
               f"Tokens: {node_usage.total_tokens}")

    return state


def detect_potential_attacks(
    af,
    parsed_arg: Argument,
    team_name: str,
    strategy_rec: StrategyRecommendation
) -> List[AttackRecommendation]:
    """
    Detect potential attack targets for the new argument.

    Uses multiple criteria:
    1. Domain overlap (arguments compete in same domains)
    2. Goal conflict (opposing teams targeting same goals)
    3. Strategic value (high-APS opponent arguments)
    4. Coverage competition (arguments that fulfill similar UGNs)
    """
    recommendations = []
    current_results = af.solve()

    arg_domains = set(parsed_arg.domains)
    arg_goals = set(gm.goal for gm in parsed_arg.goals)

    # Get all opponent arguments
    opponent_args = {
        name: arg for name, arg in af.arguments.items()
        if arg.team != team_name
    }

    # Calculate actual max APS for proper normalization
    all_aps_values = [current_results["aps"].get(name, 0) for name in opponent_args.keys()]
    max_aps = max(all_aps_values) if all_aps_values and max(all_aps_values) > 0 else 1

    for target_name, target_arg in opponent_args.items():
        confidence = 0.0
        reasons = []
        strategic_value = 0.0

        # Criterion 1: Domain overlap
        domain_overlap = arg_domains.intersection(target_arg.domains)
        if domain_overlap:
            max_domains = max(len(arg_domains), len(target_arg.domains))
            overlap_ratio = len(domain_overlap) / max_domains if max_domains > 0 else 0
            confidence += overlap_ratio * 0.5
            reasons.append(f"Competes in domains: {', '.join(domain_overlap)}")

        # Criterion 2: Goal conflict
        target_goals = set(target_arg.goals.keys())
        goal_overlap = arg_goals.intersection(target_goals)
        if goal_overlap:
            max_goals = max(len(arg_goals), len(target_goals))
            goal_ratio = len(goal_overlap) / max_goals if max_goals > 0 else 0
            confidence += goal_ratio * 0.4
            reasons.append(f"Conflicts on goals: {', '.join(goal_overlap)}")

        # Criterion 3: Strategic value
        target_aps = current_results["aps"].get(target_name, 0)
        if target_aps > 0:
            aps_factor = min(target_aps / max_aps, 1.0)
            confidence += aps_factor * 0.3
            strategic_value = target_aps
            reasons.append(f"High-value target (APS: {target_aps})")

        # Criterion 4: UGN competition
        if _competes_for_ugn(parsed_arg, target_arg, strategy_rec):
            confidence += 0.2
            reasons.append("Competes for critical UGN coverage")

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

        # Only recommend if there's some basis for attack
        if confidence > 0.1:
            recommendations.append(AttackRecommendation(
                target_argument=target_name,
                confidence=confidence,
                reason="; ".join(reasons),
                strategic_value=strategic_value
            ))

    # Sort by confidence and strategic value
    recommendations.sort(
        key=lambda x: (x.confidence, x.strategic_value),
        reverse=True
    )

    return recommendations


def _competes_for_ugn(
    new_arg: Argument,
    existing_arg,
    strategy_rec: StrategyRecommendation
) -> bool:
    """Check if arguments compete for the same UGN coverage"""
    new_domains = set(new_arg.domains)
    new_goals = set(gm.goal for gm in new_arg.goals)

    existing_domains = existing_arg.domains
    existing_goals = set(existing_arg.goals.keys())

    # Check if both target the same primary UGN
    for ugn in strategy_rec.primary_ugns:
        new_covers = ugn.domain.name in new_domains and ugn.goal.name in new_goals
        existing_covers = ugn.domain.name in existing_domains and ugn.goal.name in existing_goals
        if new_covers and existing_covers:
            return True

    return False


def _select_best_variation_with_llm(
    variations: List[Dict[str, Any]],
    topic: str,
    llm,
    token_tracker
) -> Dict[str, Any]:
    """
    Use LLM to select the best argument variation when evaluation is disabled.

    This is called when ToT evaluation is OFF, so we need to pick the best
    variation without running full evaluation.

    Args:
        variations: List of argument variation dicts
        topic: The debate topic
        llm: Language model to use for selection
        token_tracker: Token tracker for recording LLM usage

    Returns:
        The selected best variation dict
    """
    if not variations:
        raise ValueError("No variations to select from")

    if len(variations) == 1:
        return variations[0]

    # Build prompt to compare variations
    prompt_template = PromptTemplate(
        template="""
        You are evaluating multiple argument variations for a debate on the topic: {topic}
        You have {num_variations} argument variations generated using different rhetorical strategies.

        VARIATIONS:
        {variations_text}

        TASK:
        Analyze each variation and select the BEST one based on:
        1. Persuasiveness and rhetorical strength
        2. Evidence quality and credibility
        3. Logical coherence and clarity
        4. Audience appeal and engagement
        5. Strategic effectiveness

        Return ONLY a JSON object with this format:
        {{
            "selected_variation_id": "the variation_id of the best argument",
            "reasoning": "brief explanation of why this variation is best (2-3 sentences)"
        }}

        JSON Response:""",
        input_variables=["topic", "num_variations", "variations_text"]
    )

    # Format variations for the prompt
    variations_text = ""
    for i, var in enumerate(variations, 1):
        variations_text += f"\n--- VARIATION {i} ---\n"
        variations_text += f"ID: {var.get('variation_id', 'unknown')}\n"
        variations_text += f"Strategy: {var.get('strategy', 'unknown')}\n"
        variations_text += f"Branch: {var.get('strategy_name', 'unknown')}\n"

        argument_text = var.get("argument_text", "")
        if not argument_text:
            full_state = var.get("full_state", {})
            argument_text = full_state.get("final_argument", "")

        # Truncate if too long
        if len(argument_text) > 1000:
            argument_text = argument_text[:1000] + "... [truncated]"

        variations_text += f"\nArgument:\n{argument_text}\n"

    # Invoke LLM
    chain = prompt_template | llm

    try:
        result = chain.invoke({
            "topic": topic,
            "num_variations": len(variations),
            "variations_text": variations_text
        })

        # Track token usage
        if token_tracker:
            wrapped_result = {"raw": result, "parsed": None}
            token_tracker.record_llm_call(wrapped_result, phase_name="variation_selection")

        # Extract content
        response_text = result.content if hasattr(result, "content") else str(result)

        # Parse JSON response
        import re
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            selection_data = json.loads(json_match.group())
            selected_id = selection_data.get("selected_variation_id", "")
            reasoning = selection_data.get("reasoning", "No reasoning provided")

            logger.info(f"[ToT CANDIDATE CREATOR] LLM selection reasoning: {reasoning}")

            # Find the variation with matching ID
            for var in variations:
                if var.get("variation_id") == selected_id:
                    return var

            logger.warning(f"[ToT CANDIDATE CREATOR] Selected ID '{selected_id}' not found, using first variation")

    except Exception as e:
        logger.error(f"[ToT CANDIDATE CREATOR] LLM selection failed: {e}")
        import traceback
        traceback.print_exc()

    # Fallback: return first variation
    logger.warning("[ToT CANDIDATE CREATOR] Falling back to first variation")
    return variations[0]
