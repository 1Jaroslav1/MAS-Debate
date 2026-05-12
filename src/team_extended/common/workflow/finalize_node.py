from dataclasses import asdict
import logging
from src.team_extended.common.metrics.token_tracking import NodeTokenUsage
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.metrics.execution_metrics import NodeExecutionMetrics

logger = logging.getLogger(__name__)


def finalize_node(state: TeamMemberState) -> TeamMemberState:
    """
    Finalize the argument by committing it to the AF service and capturing results.

    This node replaces the callback-based architecture by directly:
    1. Committing the candidate argument to the AF service
    2. Building a complete log entry with metrics
    3. Adding metrics to the MetricsAggregator
    4. Storing the log entry for team.py to capture
    """
    af = state.get("af")
    team_name = state.get("team_name", "unknown")
    member_name = state.get("team_member_name", "unknown")
    round_num = state.get("round", 0)

    # Get the candidate before applying (to access its details)
    candidate_id = af.current_candidate_id
    if not candidate_id or candidate_id not in af.candidate_arguments:
        logger.warning(f"[FINALIZE NODE] No candidate argument found for {member_name}")
        return state

    candidate = af.candidate_arguments[candidate_id]

    # Apply the candidate argument (commits to framework)
    af.apply_candidate_argument()

    # Get the committed argument details
    # Note: apply_candidate_argument() may modify the name, so we need to find it
    committed_arg = af.arguments.get(candidate.name)
    if not committed_arg:
        # Try to find by original name or similar
        for arg_name, arg in af.arguments.items():
            if arg.text == candidate.text and arg.team == candidate.team:
                committed_arg = arg
                break

    if not committed_arg:
        logger.error(f"[FINALIZE NODE] Could not find committed argument for {member_name}")
        return state

    # Build the base log entry with argument details
    log_entry = {
        "round": round_num,
        "team": team_name,
        "member_name": member_name,
        "argument_name": candidate.name,
        "domains": sorted(list(candidate.domains)),
        "goals": {k: sorted(list(v)) for k, v in candidate.goals.items()},
        "attacks": sorted(list(candidate.attacks)),
        "text": candidate.text,
    }

    # Add iteration history if available
    iteration_history = state.get("iteration_history")
    if iteration_history:
        log_entry["iteration_history"] = iteration_history
        logger.info(f"[FINALIZE NODE] Added iteration history with {len(iteration_history)} iterations")

    # Add node execution metrics
    node_metrics = state.get("node_token_usage", {})
    if node_metrics:
        # Convert NodeExecutionMetrics to summary dicts
        node_token_breakdown = {}
        for node_name, metrics in node_metrics.items():
            if isinstance(metrics, NodeTokenUsage):
                node_token_breakdown[node_name] = metrics.to_dict()
            else:
                node_token_breakdown[node_name] = metrics

        log_entry["node_token_breakdown"] = node_token_breakdown

        # Calculate totals
        total_tokens = sum(
            m.total_tokens if isinstance(m, NodeTokenUsage) else m.get("total_tokens", 0)
            for m in node_metrics.values()
        )
        total_time = sum(
            m.elapsed_time_seconds if isinstance(m, NodeTokenUsage) else m.get("elapsed_time_seconds", 0.0)
            for m in node_metrics.values()
        )

        logger.info(f"[FINALIZE NODE] Added node execution metrics: Time={total_time:.2f}s, Tokens={total_tokens}")

        # Add metrics to the MetricsAggregator
        metrics_aggregator = state.get("metrics_aggregator")
        if metrics_aggregator:
            for node_name, metrics in node_metrics.items():
                metrics_obj = NodeExecutionMetrics(
                    team_name=team_name,
                    member_name=member_name,
                    round=round_num,
                    node_name=node_name,
                    input_tokens=metrics.input_tokens,
                    output_tokens=metrics.output_tokens,
                    total_tokens=metrics.total_tokens,
                    elapsed_time_seconds=metrics.elapsed_time_seconds,
                    llm_call_count=metrics.llm_call_count,
                    sub_phases={k: asdict(v) for k, v in metrics.sub_phases.items()}
                )
                metrics_aggregator.add_metrics(metrics_obj)

    evaluation_result = state.get("evaluator_results")
    if evaluation_result and hasattr(evaluation_result, 'evaluator_records'):
        log_entry["evaluation_log"] = {
            "overall_score": evaluation_result.overall_score,
            "final_result": evaluation_result.final_result.value,
            "evaluator_records": [
                {
                    "evaluator_name": record.evaluator_name,
                    "overall_score": record.overall_score,
                    "dimensions": [
                        {
                            "dimension": dim.dimension,
                            "score": dim.score,
                            "justification": dim.justification
                        }
                        for dim in record.dimensions
                    ],
                    "feedback": record.feedback,
                    "metadata": record.metadata,
                    "timestamp": record.timestamp.isoformat()
                }
                for record in evaluation_result.evaluator_records
            ],
            "strengths": evaluation_result.strengths,
            "weaknesses": evaluation_result.weaknesses,
            "improvement_suggestions": evaluation_result.improvement_suggestions,
            "timestamp": evaluation_result.evaluation_timestamp.isoformat()
        }
        logger.info(f"[FINALIZE NODE] Added evaluation log with {len(evaluation_result.evaluator_records)} evaluator records")

    logger.info(f"[FINALIZE NODE] Candidate {committed_arg.name} was applied for {member_name}")

    # Store the log entry in state for team.py to capture
    state["finalized_argument_log_entry"] = log_entry

    return state
