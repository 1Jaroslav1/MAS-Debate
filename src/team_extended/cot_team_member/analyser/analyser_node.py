"""
Chain-of-Thought analyser (reworked): recommends domain-goal pairs using all domains/goals
and previous arguments. Returns domain_goal_pairs for downstream nodes.
"""
import logging
import time
from typing import List
from src.team_extended.common.state import TeamMemberState
from pydantic import BaseModel, Field
from src.team_extended.common.metrics.execution_metrics import MetricsCollector
from src.team_extended.common.metrics.token_tracking import create_node_tracker, WorkflowNode

logger = logging.getLogger(__name__)

class RecommendedPair(BaseModel):
    domain: str = Field(description="Domain id (e.g., 'd_technology')")
    goal: str = Field(description="Goal id (e.g., 'g_safety')")
    priority: int = Field(description="Priority 1-100 (higher means more urgent)", ge=1, le=100)
    rationale: str = Field(description="Why this pair is recommended now")


class CoTAnalysisOutput(BaseModel):
    domain_goal_pairs: List[RecommendedPair] = Field(description="Recommended domain-goal pairs")
    notes: str | None = Field(default=None, description="Additional notes")


def analyser_node(state: TeamMemberState) -> TeamMemberState:
    """Generate recommended domain-goal pairs using LLM with structured output."""
    topic = state["topic"]
    team_name = state["team_name"]
    member_name = state["team_member_name"]
    af = state.get("af")
    llm = state.get("analyser_llm")

    domains = af.list_domains() if af else []
    goals = af.list_goals() if af else []

    logger.info(f"[ANALYSER NODE] Starting for member: {member_name}")

    token_tracker = create_node_tracker(WorkflowNode.ANALYSER)

    previous_args_text: List[str] = []
    try:
        for arg in af.get_arguments_by_team(team_name):
            previous_args_text.append(f"- {arg.name}: {arg.text}")
    except Exception:
        pass

    domains_block = "\n".join(
        [f"- {d.name}: {d.description} (salience {d.salience})" for d in domains]
    ) or "- general: General domain"

    def _format_goal(goal) -> str:
        pg_items = ", ".join([f"{dn}:{pv}" for dn, pv in sorted(goal.pg_values.items())])
        return f"- {goal.name}: {goal.description} | PG: {pg_items or 'none'}"

    goals_block = "\n".join([_format_goal(g) for g in goals]) or "- general_goal: General goal"

    prev_block = "\n".join(previous_args_text) or "- None"

    prompt = f"""
        You are a strategic debate analyst. Recommend the best domain-goal pairs to focus next.

        CONTEXT
        - Topic: {topic}
        - Team: {team_name}

        DOMAINS (ID: description, salience):
        {domains_block}

        GOALS (ID: description | PG values by domain):
        {goals_block}

        PREVIOUS TEAM ARGUMENTS:
        {prev_block}

        INSTRUCTIONS
        - Choose domain-goal pairs that maximize strategic coverage and impact now.
        - Use all available domains and goals; avoid duplicates.
        - Consider salience and PG alignment, and avoid pairs already well-covered by previous arguments unless needed.
        - Return 1-2 pairs with priority and a brief rationale.
        - IMPORTANT: Use only the exact domain and goal IDs provided above. Do NOT use numeric values or create new identifiers.
    """

    result = llm.with_structured_output(CoTAnalysisOutput, include_raw=True).invoke(prompt)

    output = result["parsed"]
    validated_pairs = []
    for pair in output.domain_goal_pairs:
        validated_domain = _validate_and_sanitize_identifier(pair.domain, "d")
        validated_goal = _validate_and_sanitize_identifier(pair.goal, "g")
        validated_pairs.append((validated_domain, validated_goal))
    
    if token_tracker:
        token_tracker.record_llm_call(result, phase_name="analyser node")

    state["analysis_result"] = {
        "domain_goal_pairs": validated_pairs
    }

    logger.info(f"🧠 CoT Analyser: recommended {len(output.domain_goal_pairs)} domain-goal pairs")

    node_usage = token_tracker.finalize()

    if "node_token_usage" not in state:
        state["node_token_usage"] = {}
    state["node_token_usage"][WorkflowNode.ANALYSER] = node_usage

    logger.info(f"[ANALYSER NODE] Completed for member: {member_name} - "
               f"Time: {node_usage.elapsed_time_seconds:.2f}s, "
               f"Tokens: {node_usage.total_tokens}")

    return state


def _validate_and_sanitize_identifier(identifier: str, prefix: str) -> str:
    """Validate and sanitize a single identifier to be safe for ASP parsing"""
    if not identifier or not isinstance(identifier, str):
        return f"{prefix}_general"
    
    sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(identifier))
    
    if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
        sanitized = f"{prefix}_{sanitized}"
    
    if not sanitized:
        sanitized = f"{prefix}_general"
    
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    
    if sanitized.isdigit():
        sanitized = f"{prefix}_{sanitized}"
    
    return sanitized
