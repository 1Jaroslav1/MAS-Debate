"""Evaluator node for CoT (Chain of Thought) team members"""

from src.team_extended.common.evaluator import Argument
from src.team_extended.common.state import TeamMemberState
from src.team_extended.cot_team_member.evaluator.evaluator_factory import (
    CoTEvaluatorFactory,
)


def evaluator_node(state: TeamMemberState) -> TeamMemberState:
    af = state.get("af")
    if not af:
        raise ValueError("GoDsAF service (af) not found in state. Cannot perform GoDsAF evaluation.")
    
    argument_text = state["argument_creator_results"]["final_argument"]
    topic = state["topic"]

    evaluator = CoTEvaluatorFactory.create_multi_evaluator(
        llm=state["evaluation_llm"],
        godsaf_service=state.get("af"),
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

    return state

