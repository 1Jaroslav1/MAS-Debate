import logging
from typing import Dict, List
from src.reasoning.miner.argument_miner import Argument
from src.team_extended.common.evaluator.godsaf.godsaf_evaluator import AttackRecommendation
from src.team_extended.common.state import TeamMemberState
from src.reasoning.godsaf.godsaf_service import CandidateArgument
from src.reasoning.miner.parser_utils import parse_argument
from src.team_extended.common.team_member import StrategyRecommendation

logger = logging.getLogger(__name__)


def candidate_creator_node(state: TeamMemberState) -> TeamMemberState:
    member_name = state.get("team_member_name", "unknown")
    team_name = state.get("team_name", "unknown")
    af = state.get("af")

    if not af:
        logger.error(f"[CANDIDATE CREATOR] No GoDsAF service found for {member_name}")
        return state

    argument_text = state.get("argument_creator_results", {}).get("final_argument", "")
    if not argument_text:
        logger.error(f"[CANDIDATE CREATOR] No argument text found for {member_name}")
        return state

    candidate_id = state.get("candidate_id")
    if not candidate_id:
        logger.error(f"[CANDIDATE CREATOR] No candidate_id found for {member_name}")
        return state

    logger.info(f"[CANDIDATE CREATOR] Creating candidate for {member_name}")

    try:
        domains = af.list_domains()
        goals = af.list_goals()
        existing_names = af.get_argument_names()
        topic = state["topic"]
        strategy_recommendation = None
        if strategy_recommendation in state:
            strategy_recommendation = state["strategy_recommendation"]

        parsed_arg: Argument = parse_argument(
            topic=topic,
            argument=argument_text,
            domains=domains,
            goals=goals,
            existing_arguments=list(existing_names),
            domain_lookup=lambda d: af.get_domain(d)
        )

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

        attacks_set = set()
        if strategy_recommendation:
            attack_recommendations = detect_potential_attacks(
                af, parsed_arg, team_name, strategy_recommendation
            )

            attacks_set = {
                rec.target_argument for rec in attack_recommendations
                if rec.confidence >= 0.4
            }


        candidate = CandidateArgument(
            name=parsed_arg.name,
            text=argument_text,
            team=team_name,
            domains=set(parsed_arg.domains),
            goals = {gm.goal: set(gm.domains) for gm in parsed_arg.goals},
            attacks=attacks_set
        )

        af.set_candidate_argument(candidate_id, candidate)

        logger.info(f"[CANDIDATE CREATOR] Created and stored candidate: {parsed_arg.name}")

    except Exception as e:
        logger.error(f"[CANDIDATE CREATOR] Failed to create candidate for {member_name}: {e}")
        import traceback
        traceback.print_exc()

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
        
        # Criterion 1: Domain overlap (fixed asymmetric calculation)
        domain_overlap = arg_domains.intersection(target_arg.domains)
        if domain_overlap:
            # Use symmetric overlap calculation
            max_domains = max(len(arg_domains), len(target_arg.domains))
            overlap_ratio = len(domain_overlap) / max_domains if max_domains > 0 else 0
            confidence += overlap_ratio * 0.5  # Increased weight
            reasons.append(f"Competes in domains: {', '.join(domain_overlap)}")
        
        # Criterion 2: Goal conflict (fixed asymmetric calculation)
        target_goals = set(target_arg.goals.keys())
        goal_overlap = arg_goals.intersection(target_goals)
        if goal_overlap:
            # Use symmetric overlap calculation
            max_goals = max(len(arg_goals), len(target_goals))
            goal_ratio = len(goal_overlap) / max_goals if max_goals > 0 else 0
            confidence += goal_ratio * 0.4  # Increased weight
            reasons.append(f"Conflicts on goals: {', '.join(goal_overlap)}")
        
        # Criterion 3: Strategic value (improved APS normalization)
        target_aps = current_results["aps"].get(target_name, 0)
        if target_aps > 0:
            # Use actual max APS instead of assumed 1000
            aps_factor = min(target_aps / max_aps, 1.0)
            confidence += aps_factor * 0.3  # Increased weight
            strategic_value = target_aps
            reasons.append(f"High-value target (APS: {target_aps})")
        
        # Criterion 4: UGN competition (increased weight)
        if _competes_for_ugn(parsed_arg, target_arg, strategy_rec):
            confidence += 0.2  # Increased from 0.1
            reasons.append("Competes for critical UGN coverage")
        
        # Cap confidence at 1.0 to prevent overflow
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