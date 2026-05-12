import logging
import traceback
import uuid
from typing import Optional
from src.reasoning.godsaf.godsaf_service import GoDsAFService
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.evaluator.model import EvaluationNodeConfig, EvaluationResult
from langgraph.graph import END

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 2


def format_evaluation_feedback(evaluation_results) -> str:
    feedback_parts = []
    
    feedback_parts.append(f"Overall Evaluation: {evaluation_results.final_result.value}")
    feedback_parts.append(f"Overall Score: {evaluation_results.overall_score:.1f}/100")
    
    if evaluation_results.strengths:
        feedback_parts.append("\nStrengths:")
        for strength in evaluation_results.strengths:
            feedback_parts.append(f"- {strength}")
    
    if evaluation_results.weaknesses:
        feedback_parts.append("\nWeaknesses:")
        for weakness in evaluation_results.weaknesses:
            feedback_parts.append(f"- {weakness}")
    
    if evaluation_results.improvement_suggestions:
        feedback_parts.append("\nImprovement Suggestions:")
        for suggestion in evaluation_results.improvement_suggestions:
            feedback_parts.append(f"- {suggestion}")
    
    if evaluation_results.strategic_recommendations:
        feedback_parts.append("\nStrategic Recommendations:")
        for recommendation in evaluation_results.strategic_recommendations:
            feedback_parts.append(f"- {recommendation}")
    
    if evaluation_results.rejection_factors:
        feedback_parts.append("\nKey Issues to Address:")
        for factor in evaluation_results.rejection_factors:
            feedback_parts.append(f"- {factor}")
    
    return "\n".join(feedback_parts)

def should_run_knowledge_retrieval(state: TeamMemberState) -> str:
    knowledge_node_config: EvaluationNodeConfig = state.get("knowledge_node_config")
    warnings = knowledge_node_config.validate_config()
    for warning in warnings:
        print(f"⚠️  Knowledge config warning: {warning}")

    if not knowledge_node_config.active:
        print(f"⏭️  Knowledge disabled for {state['team_member_name']}, skipping to finalization")
        return "skip_knowledge_retrieval"

    return "run_knowledge_retrieval"

def should_run_evaluation(state: TeamMemberState) -> str:
    """Determine if evaluation should run based on configuration"""
    evaluation_node_config: EvaluationNodeConfig = state.get("evaluation_node_config")

    warnings = evaluation_node_config.validate_config()
    for warning in warnings:
        print(f"⚠️  Evaluation config warning: {warning}")

    if not evaluation_node_config.active:
        print(f"⏭️  Evaluation disabled for {state['team_member_name']}, skipping to finalization")
        return "skip_evaluation"

    return "run_evaluation"


def should_rerun_argumentation(state: TeamMemberState):
    current_iteration = state.get("iteration_number", 0)
    max_iterations = state.get("argument_creation_context").max_iterations if state.get("argument_creation_context") else MAX_ITERATIONS

    if "iteration_history" not in state:
        state["iteration_history"] = []

    evaluation_results = state.get("evaluator_results")
    argument_text = state.get("argument_creator_results", {}).get("final_argument", "")

    # Extract strategic scores from GoDsAF evaluator metadata if available
    strategic_alignment_score = None
    ugn_coverage_score = None
    addresses_primary_ugn = None
    addresses_secondary_ugn = None

    if evaluation_results and hasattr(evaluation_results, "evaluator_records"):
        for record in evaluation_results.evaluator_records:
            if record.evaluator_name == "GoDsAF_Strategic_Evaluator" and record.metadata:
                metadata = record.metadata
                if "original_evaluation" in metadata:
                    original_eval = metadata["original_evaluation"]
                    strategic_alignment_score = getattr(original_eval, "strategic_alignment_score", None)
                    ugn_coverage_score = getattr(original_eval, "ugn_coverage_score", None)
                    addresses_primary_ugn = getattr(original_eval, "addresses_primary_ugn", None)
                    addresses_secondary_ugn = getattr(original_eval, "addresses_secondary_ugn", None)
                else:
                    # Fallback to metadata fields
                    addresses_primary_ugn = metadata.get("addresses_primary_ugn", None)
                    addresses_secondary_ugn = metadata.get("addresses_secondary_ugn", None)
                break

    iteration_record = {
        "iteration": current_iteration,
        "argument_text": argument_text,
        "evaluation_results": {
            "overall_score": evaluation_results.overall_score if evaluation_results else 0,
            "final_result": evaluation_results.final_result.value if evaluation_results else "unknown",
            "strategic_alignment_score": strategic_alignment_score,
            "ugn_coverage_score": ugn_coverage_score,
            "addresses_primary_ugn": addresses_primary_ugn,
            "addresses_secondary_ugn": addresses_secondary_ugn,
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
                    "feedback": record.feedback
                }
                for record in evaluation_results.evaluator_records
            ] if evaluation_results and hasattr(evaluation_results, "evaluator_records") else [],
            "strengths": evaluation_results.strengths if evaluation_results else [],
            "weaknesses": evaluation_results.weaknesses if evaluation_results else [],
            "improvement_suggestions": evaluation_results.improvement_suggestions if evaluation_results else []
        },
        "accepted": False
    }

    state["iteration_history"].append(iteration_record)

    print(f"\n{'='*80}")
    print(f"ITERATION {current_iteration}/{max_iterations} EVALUATION SUMMARY")
    print(f"{'='*80}")
    print(f"Overall Score: {evaluation_results.overall_score:.1f}/100")
    print(f"Result: {evaluation_results.final_result.value.upper()}")

    if strategic_alignment_score is not None:
        print(f"Strategic Alignment: {strategic_alignment_score:.1f}/100")
    if ugn_coverage_score is not None:
        print(f"UGN Coverage: {ugn_coverage_score:.1f}/100")
    if addresses_primary_ugn is not None:
        print(f"Addresses Primary UGN: {addresses_primary_ugn}")

    if evaluation_results and evaluation_results.improvement_suggestions:
        print(f"\nImprovement Suggestions:")
        for suggestion in evaluation_results.improvement_suggestions[:3]:
            print(f"  - {suggestion}")

    should_accept = evaluation_results.final_result.value in [EvaluationResult.EXCELLENT.value, EvaluationResult.GOOD.value]

    if should_accept or current_iteration >= max_iterations - 1:
        if should_accept:
            print(f"\n✓ ARGUMENT ACCEPTED (Score: {evaluation_results.overall_score:.1f})")
        else:
            print(f"\n⚠ MAX ITERATIONS REACHED - Accepting best argument")

        state["iteration_history"][-1]["accepted"] = True

        print(f"{'='*80}\n")
        return "end"
    else:
        print(f"\n✗ ARGUMENT REJECTED - Starting iteration {current_iteration + 2}")
        print(f"{'='*80}\n")

        state["iteration_number"] = current_iteration + 1

        context = state["argument_creation_context"]
        if evaluation_results:
            context.reviewer_feedback = format_evaluation_feedback(evaluation_results)

        return "argument_creator"


def ensure_session_id(initial_state: TeamMemberState) -> None:
    if "knowledge_retrival_context" in initial_state and initial_state["knowledge_retrival_context"]:
        if not initial_state["knowledge_retrival_context"].session_id:
            initial_state["knowledge_retrival_context"].session_id = str(uuid.uuid4())
    
    if not initial_state["argument_creation_context"].session_id:
        initial_state["argument_creation_context"].session_id = str(uuid.uuid4())


def execute_workflow_with_error_handling(
    workflow,
    initial_state: TeamMemberState,
    workflow_name: str = "workflow"
) -> TeamMemberState:
    try:
        final_state = workflow.invoke(initial_state)

        # Aggregate node token usage if present
        if "node_token_usage" in final_state:
            from src.team_extended.common.metrics.token_tracking import TokenUsageAggregator

            aggregator = TokenUsageAggregator()

            # Add each node's usage
            for node_name, node_usage in final_state["node_token_usage"].items():
                aggregator.add_node_usage(node_usage)

            # Validate totals
            if aggregator.validate():
                logger.info(f"[WORKFLOW] Token validation passed for {workflow_name}")
            else:
                logger.warning(f"[WORKFLOW] Token validation failed for {workflow_name}")

            # Store aggregator
            final_state["token_aggregator"] = aggregator

            # Update execution metrics with node breakdown
            if "execution_metrics" in final_state:
                summary = aggregator.get_summary()
                final_state["execution_metrics"].node_token_breakdown = summary["node_breakdown"]

                logger.info(f"[WORKFLOW] {workflow_name} total tokens: {summary['total_tokens']}")

        return final_state
    except RuntimeError as e:
        if "parsing failed" in str(e) or "grounding stopped because of errors" in str(e):
            print(f"Warning: {workflow_name} workflow failed due to parsing/grounding error. Returning initial state. Error: {e}")
            return initial_state
        else:
            raise
    except Exception as e:
        print(f"Warning: Unexpected error in {workflow_name} workflow execution. Returning initial state. Error: {e}")
        traceback.print_exc()

        return initial_state

