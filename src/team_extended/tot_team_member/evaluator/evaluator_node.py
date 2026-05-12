"""
ToT Evaluator Node

Orchestrates the tree-of-thoughts evaluation process:
1. Quick scoring of all argument variations
2. Branch pruning based on scores
3. Deep evaluation of surviving branches
4. Tree search to select best argument
"""

import logging
from typing import List, Dict, Any

from src.team_extended.common.evaluator import Argument
from src.team_extended.common.state import TeamMemberState
from src.team_extended.tot_team_member.evaluator.evaluator_factory import ToTEvaluatorFactory
from src.team_extended.tot_team_member.evaluator.branch_manager import (
    BranchManager,
    BranchType,
    PruningStrategy,
    SearchAlgorithm
)
from src.reasoning.godsaf.godsaf_service import CandidateArgument
from src.reasoning.miner.parser_utils import parse_argument
from src.reasoning.miner.argument_miner import Argument as MinerArgument

logger = logging.getLogger(__name__)


def evaluator_node(state: TeamMemberState) -> TeamMemberState:
    """
    ToT Evaluator node that performs tree-based evaluation.

    Process:
    1. Create branch manager and add all argument variations
    2. Quick score all variations
    3. Prune low-scoring branches
    4. Deep evaluate surviving branches
    5. Search tree for best argument
    6. Store best argument in state
    """
    logger.info("[ToT EVALUATOR NODE] Starting tree-based evaluation")

    # Create ToT-specific multi-evaluator
    evaluator = ToTEvaluatorFactory.create_multi_evaluator(
        llm=state["evaluation_llm"],
        config=state["evaluation_config"],
        godsaf_service=state.get("af"),
    )

    # Extract ToT evaluator for quick scoring
    tot_evaluator = ToTEvaluatorFactory.get_tot_evaluator(evaluator)

    # Get ToT configuration (with defaults)
    tot_config = state.get("tot_config") or {}
    pruning_strategy = PruningStrategy(tot_config.get("pruning_strategy", "top_k"))
    argument_pruning_k = tot_config.get("argument_pruning_k", 5)
    search_algorithm = SearchAlgorithm(tot_config.get("search_algorithm", "best_first"))

    # Get all argument variations from argument creator
    variations = state.get("tot_argument_variations", [])

    if not variations:
        logger.warning("No argument variations found, falling back to single argument evaluation")
        return _evaluate_single_argument(state, evaluator)

    logger.info(f"Evaluating {len(variations)} argument variations")

    # Initialize branch manager
    branch_manager = BranchManager()

    # Add analysis branches (from analyser)
    analysis_branches = state.get("tot_analysis_branches", [])
    for branch_data in analysis_branches:
        branch_manager.add_branch(
            branch_id=branch_data["branch_id"],
            parent_id=None,
            branch_type=BranchType.ANALYSIS,
            data=branch_data,
            metadata={
                "strategy_name": branch_data["strategy_name"],
                "rationale": branch_data["strategy_rationale"]
            }
        )

    # Step 1: Add all argument variations as branches
    for variation in variations:
        # Create Argument object
        argument = Argument(
            text=variation["argument_text"],
            topic=state["topic"],
            team_type=state["argument_creation_context"].team_focus.team_type,
            team_perspective=state["argument_creation_context"].team_focus.perspective_description,
            viewpoint_orientation=state["argument_creation_context"].team_focus.viewpoint_orientation,
        )

        # Add as branch
        branch_manager.add_branch(
            branch_id=variation["variation_id"],
            parent_id=variation["branch_id"],  # Link to analysis branch
            branch_type=BranchType.ARGUMENT,
            data={
                "argument": argument,
                "variation": variation
            },
            metadata={
                "strategy": variation["strategy"],
                "strategy_name": variation.get("strategy_name", "Unknown")
            }
        )

    logger.info(f"Added {len(variations)} argument branches to tree")

    # Step 2: Quick score all argument branches
    logger.info("Quick scoring all argument variations...")

    if tot_evaluator:
        for branch_id, branch in branch_manager.branches.items():
            if branch.branch_type == BranchType.ARGUMENT:
                argument = branch.data["argument"]
                variation = branch.data["variation"]

                # Quick score
                quick_score = tot_evaluator.quick_evaluate(
                    argument=argument,
                    topic=state["topic"],
                    team_name=state["team_name"],
                    domain_goal_pairs=variation.get("domain_goal_pairs")
                )

                branch_manager.set_score(branch_id, quick_score)
                logger.debug(f"  {branch_id}: {quick_score:.1f}")
    else:
        logger.warning("ToT evaluator not found, using default scoring")
        for branch_id, branch in branch_manager.branches.items():
            if branch.branch_type == BranchType.ARGUMENT:
                branch_manager.set_score(branch_id, 50.0)

    # Step 3: Prune branches
    logger.info(f"Pruning branches (strategy={pruning_strategy.value}, keep_top_k={argument_pruning_k})")

    pruned_count = branch_manager.prune_branches(
        strategy=pruning_strategy,
        keep_top_k=argument_pruning_k,
        branch_type=BranchType.ARGUMENT
    )

    logger.info(f"Pruned {pruned_count} argument branches")

    # Step 4: Deep evaluate surviving branches
    active_arguments = branch_manager.get_active_branches(BranchType.ARGUMENT)
    logger.info(f"Deep evaluating {len(active_arguments)} surviving branches...")

    for branch in active_arguments:
        argument = branch.data["argument"]
        variation = branch.data["variation"]

        # Prepare evaluation parameters
        eval_params = {
            "team_name": state["team_name"],
            "strategy_recommendation": None,
            "existing_argument_names": state.get("af").get_argument_names() if state.get("af") else [],
            "candidate_id": state.get("candidate_id"),
            "analysis_result": state.get("analysis_result"),
        }

        # Run deep evaluation
        try:
            result = evaluator.evaluate_argument(argument, **eval_params)

            # Update branch score with deep evaluation score
            deep_score = result.overall_score
            branch_manager.set_score(branch.branch_id, deep_score)
            branch_manager.set_metadata(branch.branch_id, "deep_evaluation", result)

            logger.info(f"  {branch.branch_id}: deep_score={deep_score:.1f}")

        except Exception as e:
            logger.error(f"Deep evaluation failed for {branch.branch_id}: {e}")
            # Keep quick score if deep evaluation fails

    # Step 5: Tree search to find best argument
    logger.info(f"Searching tree (algorithm={search_algorithm.value})...")

    best_branch = branch_manager.search_tree(algorithm=search_algorithm)

    if not best_branch:
        logger.error("No best branch found, falling back to highest scorer")
        active = branch_manager.get_active_branches(BranchType.ARGUMENT)
        if active:
            best_branch = max(active, key=lambda b: b.score)
        else:
            logger.error("No active branches available!")
            return _evaluate_single_argument(state, evaluator)

    # Step 6: Store best argument in state
    best_argument = best_branch.data["argument"]
    best_variation = best_branch.data["variation"]
    best_evaluation = best_branch.metadata.get("deep_evaluation")

    logger.info(f"🏆 Selected best argument: {best_branch.branch_id} (score={best_branch.score:.1f})")

    # Update state with best argument
    state["argument_creator_results"] = best_variation["full_state"]
    state["evaluator_results"] = best_evaluation

    # Store ToT metadata
    state["tot_tree_metadata"] = branch_manager.get_statistics()
    state["tot_tree_metadata"]["best_path"] = branch_manager.get_best_path()
    state["tot_tree_metadata"]["best_branch_id"] = best_branch.branch_id
    state["tot_tree_metadata"]["best_score"] = best_branch.score

    # Step 7: Update candidate with best argument
    # For ToT, we need to recreate the candidate with the best selected variation
    _update_candidate_with_best_variation(state, best_variation, best_evaluation)

    # The finalization node will handle metadata preparation and commit
    # No longer setting _for_commit attributes here

    logger.info(f"[ToT EVALUATOR NODE] Completed - explored {state['tot_tree_metadata']['total_branches']} branches")

    return state


def _evaluate_single_argument(state: TeamMemberState, evaluator) -> TeamMemberState:
    """Fallback: evaluate single argument without tree search"""
    logger.info("Evaluating single argument (fallback mode)")

    # Create argument from the argument creator results
    new_argument = Argument(
        text=state["argument_creator_results"]["final_argument"],
        topic=state["topic"],
        team_type=state["argument_creator_results"]["context"].team_focus.team_type,
        team_perspective=state["argument_creator_results"]["context"].team_focus.perspective_description,
        viewpoint_orientation=state["argument_creator_results"]["context"].team_focus.viewpoint_orientation,
    )

    # Prepare evaluation parameters
    eval_params = {
        "team_name": state["team_name"],
        "strategy_recommendation": None,
        "existing_argument_names": state.get("af").get_argument_names() if state.get("af") else [],
        "candidate_id": state.get("candidate_id"),
        "analysis_result": state.get("analysis_result"),
    }

    # Run evaluation
    result = evaluator.evaluate_argument(new_argument, **eval_params)

    # Store results in state
    state["evaluator_results"] = result

    # The finalization node will handle metadata preparation and commit
    # No longer setting _for_commit attributes here

    return state


def _update_candidate_with_best_variation(
    state: TeamMemberState,
    best_variation: Dict[str, Any],
    best_evaluation: Any
) -> None:
    """
    Update the candidate in GoDsAF service with the best selected variation.

    For ToT, the candidate_creator runs before evaluation and creates a candidate
    from the first/default variation. After the evaluator selects the best variation,
    we need to update the candidate with the best argument.

    Args:
        state: The team member state
        best_variation: The best argument variation selected by tree search
        best_evaluation: The evaluation results for the best variation
    """
    af = state.get("af")
    if not af:
        logger.warning("[ToT EVALUATOR] No GoDsAF service found, cannot update candidate")
        return

    candidate_id = state.get("candidate_id")
    if not candidate_id:
        logger.warning("[ToT EVALUATOR] No candidate_id found, cannot update candidate")
        return

    # Extract best argument from variation structure
    # Variation has: argument_text, full_state["final_argument"], domain_goal_pairs, etc.
    best_argument_text = best_variation.get("argument_text", "")

    if not best_argument_text:
        # Fallback: try full_state
        full_state = best_variation.get("full_state", {})
        best_argument_text = full_state.get("final_argument", "")

    if not best_argument_text:
        logger.error("[ToT EVALUATOR] No argument text in best variation")
        return

    team_name = state.get("team_name", "unknown")

    logger.info(f"[ToT EVALUATOR] Updating candidate with best variation {best_variation.get('variation_id')} (score={best_evaluation.overall_score:.2f})")

    try:
        domains = af.list_domains()
        goals = af.list_goals()
        existing_names = af.get_argument_names()
        topic = state["topic"]

        # Parse the best argument
        parsed_arg: MinerArgument = parse_argument(
            topic=topic,
            argument=best_argument_text,
            domains=domains,
            goals=goals,
            existing_arguments=list(existing_names),
            domain_lookup=lambda d: af.get_domain(d)
        )

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

        # Get existing candidate to preserve attacks if any
        existing_candidate = af.get_current_candidate_argument()
        attacks_set = existing_candidate.attacks if existing_candidate else set()

        # Create updated candidate with best argument
        updated_candidate = CandidateArgument(
            name=parsed_arg.name,
            text=best_argument_text,
            team=team_name,
            domains=set(parsed_arg.domains),
            goals={gm.goal: set(gm.domains) for gm in parsed_arg.goals},
            attacks=attacks_set
        )

        # Update candidate in GoDsAF service
        af.set_candidate_argument(candidate_id, updated_candidate)

        logger.info(f"[ToT EVALUATOR] Successfully updated candidate '{parsed_arg.name}' with best variation")

    except Exception as e:
        logger.error(f"[ToT EVALUATOR] Failed to update candidate: {e}")
        import traceback
        traceback.print_exc()
