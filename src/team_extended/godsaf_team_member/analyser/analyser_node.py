import logging
import time
from src.team_extended.common.state import TeamMemberState
from src.team_extended.common.analyser.godsaf_analyser import GoDsAFAnalysisNode
from src.team_extended.common.metrics.execution_metrics import MetricsCollector
from src.team_extended.common.metrics.token_tracking import create_node_tracker, WorkflowNode

logger = logging.getLogger(__name__)

def analyser_node(state: TeamMemberState) -> TeamMemberState:
    af = state["af"]
    member_name = state["team_member_name"]
    logger.info(f"[ANALYSER NODE] Starting for member: {member_name}")

    token_tracker = create_node_tracker(WorkflowNode.ANALYSER)

    if not af:
        raise ValueError("GoDsAF service (af) not found in state. Cannot perform GoDsAF analysis.")

    analyzer = GoDsAFAnalysisNode(af)
    strategy_recommendation = analyzer.analyze_team_strategy(state["team_name"])

    state["strategy_recommendation"] = strategy_recommendation

    node_usage = token_tracker.finalize()

    if "node_token_usage" not in state:
        state["node_token_usage"] = {}
    state["node_token_usage"][WorkflowNode.ANALYSER] = node_usage

    logger.info(f"[ANALYSER NODE] Completed for member: {member_name} - "
               f"Time: {node_usage.elapsed_time_seconds:.2f}s, "
               f"Tokens: {node_usage.total_tokens}")

    return state
