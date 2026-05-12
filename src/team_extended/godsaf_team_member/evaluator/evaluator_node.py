import logging
from src.team_extended.common.evaluator import Argument
from src.team_extended.common.metrics.token_tracking import WorkflowNode, create_node_tracker
from src.team_extended.common.state import TeamMemberState
from src.team_extended.godsaf_team_member.evaluator.evaluator_factory import (
    GoDsAFEvaluatorFactory,
)

logger = logging.getLogger(__name__)

def evaluator_node(state: TeamMemberState) -> TeamMemberState:
    af = state["af"]
    member_name = state["team_member_name"]
    logger.info(f"[EVALUATOR NODE] Starting for member: {member_name}")

    token_tracker = create_node_tracker(WorkflowNode.EVALUATOR)

    if not af:
        raise ValueError("GoDsAF service (af) not found in state. Cannot perform GoDsAF evaluation.")

    argument_text = state["argument_creator_results"]["final_argument"]
    topic = state["topic"]

    evaluator = GoDsAFEvaluatorFactory.create_multi_evaluator(
        llm=state["evaluation_llm"],
        godsaf_service=af,
        config=state["evaluation_config"],
    )

    new_argument = Argument(
        text=argument_text,
        topic=topic,
        team_type=state["argument_creator_results"]["context"].team_focus.team_type,
        team_perspective=state["argument_creator_results"]["context"].team_focus.perspective_description,
        viewpoint_orientation=state["argument_creator_results"]["context"].team_focus.viewpoint_orientation,
    )

    eval_params = {
        "team_name": state["team_name"],
        "strategy_recommendation": state["strategy_recommendation"],
        "candidate_id": state["candidate_id"],
    }

    result = evaluator.evaluate_argument(new_argument, **eval_params)

    state["evaluator_results"] = result

    node_usage = token_tracker.finalize()
    if "node_token_usage" not in state:
        state["node_token_usage"] = {}
    state["node_token_usage"][WorkflowNode.EVALUATOR] = node_usage

    logger.info(f"[EVALUATOR NODE] Completed for member: {member_name} - "
               f"Time: {node_usage.elapsed_time_seconds:.2f}s, "
               f"Tokens: {node_usage.total_tokens}")

    return state

