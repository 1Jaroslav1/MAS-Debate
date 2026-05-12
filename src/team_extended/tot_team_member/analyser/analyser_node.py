"""
Tree of Thoughts Analyser Node

Generates multiple diverse analysis strategies (branches) for domain-goal pair selection.
Each branch represents a different strategic approach to the debate.
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


class AnalysisBranch(BaseModel):
    """A single analysis branch with its own strategy"""
    branch_id: str = Field(description="Unique identifier for this branch (e.g., 'strategy_1', 'strategy_2')")
    strategy_name: str = Field(description="Name of the strategy (e.g., 'Evidence-Heavy', 'Emotional-Appeal')")
    domain_goal_pairs: List[RecommendedPair] = Field(description="Recommended domain-goal pairs for this strategy")
    strategy_rationale: str = Field(description="Overall rationale for this strategic approach")
    diversity_marker: str = Field(description="What makes this strategy unique/different from others")


class ToTAnalysisOutput(BaseModel):
    """Multiple diverse analysis branches"""
    branches: List[AnalysisBranch] = Field(description="List of diverse analysis strategies (3-5 branches)")
    overall_context: str = Field(description="Brief context about the debate situation")


def analyser_node(state: TeamMemberState) -> TeamMemberState:
    topic = state["topic"]
    team_name = state["team_name"]
    member_name = state["team_member_name"]
    af = state.get("af")
    llm = state.get("analyser_llm")

    # Get ToT configuration (with defaults)
    tot_config = state.get("tot_config") or {}
    num_branches = tot_config.get("num_analysis_branches", 3)

    domains = af.list_domains() if af else []
    goals = af.list_goals() if af else []

    logger.info(f"[ToT ANALYSER NODE] Starting for member: {member_name} (generating {num_branches} branches)")

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
        You are a strategic debate analyst using Tree of Thoughts reasoning.
        Generate {num_branches} DIVERSE strategic approaches for argument generation.

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
        Generate {num_branches} diverse analysis branches, each representing a DIFFERENT strategic approach:

        Strategy Examples:
        1. "Evidence-Heavy": Focus on domains/goals with strong empirical support
        2. "Emotional-Appeal": Focus on domains/goals that resonate emotionally
        3. "Counter-Attack": Focus on domains/goals that directly challenge opponents
        4. "Novel-Angle": Focus on less-explored domains/goals for uniqueness
        5. "Consolidation": Strengthen existing domain/goal coverage

        For EACH branch:
        - Assign a unique branch_id (strategy_1, strategy_2, etc.)
        - Give it a descriptive strategy_name
        - Recommend 1-3 domain-goal pairs that fit this strategy
        - Explain the strategy rationale (why this approach makes sense)
        - Specify what makes this branch diverse/unique (diversity_marker)

        CRITICAL:
        - Each branch must be MEANINGFULLY DIFFERENT from others
        - Use only the exact domain and goal IDs provided above
        - Ensure good coverage across different strategic angles
        - Consider both offensive and defensive strategies
    """

    result = llm.with_structured_output(ToTAnalysisOutput, include_raw=True).invoke(prompt)

    output = result["parsed"]

    all_branches = []

    logger.info(f"[🌳TOT ANALYSER] Num of branches  {len(output.branches)}")

    for branch in output.branches:
        validated_pairs = []
        for pair in branch.domain_goal_pairs:
            validated_domain = _validate_and_sanitize_identifier(pair.domain, "d")
            validated_goal = _validate_and_sanitize_identifier(pair.goal, "g")
            validated_pairs.append((validated_domain, validated_goal))

        branch_data = {
            "branch_id": branch.branch_id,
            "strategy_name": branch.strategy_name,
            "domain_goal_pairs": validated_pairs,
            "strategy_rationale": branch.strategy_rationale,
            "diversity_marker": branch.diversity_marker
        }
        all_branches.append(branch_data)

    if token_tracker:
        token_tracker.record_llm_call(result, phase_name="tot analyser node")

    state["tot_analysis_branches"] = all_branches

    if all_branches:
        state["analysis_result"] = {
            "domain_goal_pairs": all_branches[0]["domain_goal_pairs"]
        }


    logger.info(f"🌳 ToT Analyser: generated {len(output.branches)} diverse analysis branches")
    for branch in output.branches:
        logger.info(f"  - {branch.strategy_name}: {len(branch.domain_goal_pairs)} pairs")

    node_usage = token_tracker.finalize()

    if "node_token_usage" not in state:
        state["node_token_usage"] = {}
    state["node_token_usage"][WorkflowNode.ANALYSER] = node_usage

    logger.info(f"[ToT ANALYSER NODE] Completed for member: {member_name} - "
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
