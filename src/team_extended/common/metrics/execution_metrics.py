"""
Execution metrics tracking for argument creation workflow.

This module provides time and token tracking capabilities for measuring
the performance and cost of argument creation by team members.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


class ExecutionMetrics(BaseModel):
    """Metrics for a single execution (e.g., one workflow invocation)"""

    # Time metrics
    start_time: float = Field(description="Start timestamp (seconds since epoch)")
    end_time: Optional[float] = Field(default=None, description="End timestamp (seconds since epoch)")
    elapsed_time_seconds: float = Field(default=0.0, description="Total execution time in seconds")

    # Token metrics
    input_tokens: int = Field(default=0, description="Total input tokens consumed")
    output_tokens: int = Field(default=0, description="Total output tokens generated")
    total_tokens: int = Field(default=0, description="Total tokens (input + output)")

    # Cost estimation (can be calculated based on model pricing)
    estimated_cost_usd: float = Field(default=0.0, description="Estimated cost in USD")

    # Breakdown by component
    component_metrics: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metrics broken down by workflow component (e.g., context_analysis, argument_construction)"
    )

    def finalize(self):
        """Finalize metrics calculation"""
        if self.end_time is None:
            self.end_time = time.time()
        self.elapsed_time_seconds = self.end_time - self.start_time
        self.total_tokens = self.input_tokens + self.output_tokens

    def add_component_metrics(self, component_name: str, input_tokens: int, output_tokens: int, elapsed_time: float):
        """Add metrics for a specific component"""
        self.component_metrics[component_name] = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "elapsed_time_seconds": elapsed_time
        }
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def calculate_cost(self, input_token_price: float = 0.000003, output_token_price: float = 0.000015):
        """
        Calculate estimated cost based on token usage.
        Default prices are for Claude Sonnet 4.5 (as of Jan 2025):
        - Input: $3 per million tokens = $0.000003 per token
        - Output: $15 per million tokens = $0.000015 per token
        """
        self.estimated_cost_usd = (
            self.input_tokens * input_token_price +
            self.output_tokens * output_token_price
        )
        return self.estimated_cost_usd


class NodeExecutionMetrics(BaseModel):
    """Metrics for a single node execution"""

    team_name: str = Field(description="Name of the team")
    member_name: str = Field(description="Name of the team member")
    round: int = Field(description="Round number")
    node_name: str = Field(description="Name of the node (e.g., 'analyser', 'knowledge_retrieval', 'argument_creator', 'evaluator')")

    # Token metrics
    input_tokens: int = Field(default=0, description="Input tokens consumed")
    output_tokens: int = Field(default=0, description="Output tokens generated")
    total_tokens: int = Field(default=0, description="Total tokens (input + output)")

    # Time metrics
    elapsed_time_seconds: float = Field(default=0.0, description="Execution time in seconds")

    # Optional: LLM call count for debugging
    llm_call_count: int = Field(default=0, description="Number of LLM calls made")

    # Optional: Sub-phases within the node (if needed)
    sub_phases: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Optional breakdown of sub-phases within this node"
    )

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of node metrics"""
        summary = {
            "team_name": self.team_name,
            "member_name": self.member_name,
            "round": self.round,
            "node_name": self.node_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "elapsed_time_seconds": self.elapsed_time_seconds,
            "llm_call_count": self.llm_call_count,
        }

        if self.sub_phases:
            summary["sub_phases"] = self.sub_phases

        return summary


# Keep ArgumentCreationMetrics for backward compatibility but mark as deprecated
class ArgumentCreationMetrics(BaseModel):
    """DEPRECATED: Use NodeExecutionMetrics instead. Kept for backward compatibility."""

    member_name: str = Field(description="Name of the team member")
    team_name: str = Field(description="Name of the team")
    iteration_number: int = Field(description="Iteration number")

    # Overall metrics
    total_execution_metrics: ExecutionMetrics = Field(description="Total metrics for entire process")

    # Phase-specific metrics
    knowledge_retrieval_metrics: Optional[ExecutionMetrics] = Field(
        default=None, description="Metrics for knowledge retrieval phase"
    )
    context_analysis_metrics: Optional[ExecutionMetrics] = Field(
        default=None, description="Metrics for context analysis phase"
    )
    argument_construction_metrics: Optional[ExecutionMetrics] = Field(
        default=None, description="Metrics for argument construction phase"
    )
    evaluation_metrics: Optional[ExecutionMetrics] = Field(
        default=None, description="Metrics for evaluation phase"
    )

    # Node-level token breakdown (NEW)
    node_token_breakdown: Optional[Dict[str, Any]] = Field(
        default=None, description="Per-node token usage breakdown"
    )

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        summary = {
            "member_name": self.member_name,
            "team_name": self.team_name,
            "iteration_number": self.iteration_number,
            "total_time_seconds": self.total_execution_metrics.elapsed_time_seconds,
            "total_tokens": self.total_execution_metrics.total_tokens,
            "input_tokens": self.total_execution_metrics.input_tokens,
            "output_tokens": self.total_execution_metrics.output_tokens,
            "estimated_cost_usd": self.total_execution_metrics.estimated_cost_usd,
            "breakdown": {
                "knowledge_retrieval": self._phase_summary(self.knowledge_retrieval_metrics),
                "context_analysis": self._phase_summary(self.context_analysis_metrics),
                "argument_construction": self._phase_summary(self.argument_construction_metrics),
                "evaluation": self._phase_summary(self.evaluation_metrics),
            }
        }

        # Add node-level breakdown if available
        if self.node_token_breakdown:
            summary["node_token_breakdown"] = self.node_token_breakdown

        return summary

    def _phase_summary(self, metrics: Optional[ExecutionMetrics]) -> Optional[Dict[str, Any]]:
        """Get summary for a specific phase"""
        if metrics is None:
            return None
        return {
            "time_seconds": metrics.elapsed_time_seconds,
            "tokens": metrics.total_tokens,
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
        }


class TokenTrackingCallback(BaseCallbackHandler):
    """Callback handler to track token usage during LLM calls"""

    def __init__(self):
        super().__init__()
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
        self.calls: List[Dict[str, Any]] = []

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Track tokens when LLM call completes"""
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.call_count += 1

            self.calls.append({
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            })

            logger.debug(f"[TOKEN TRACKING] LLM call #{self.call_count}: "
                        f"input={input_tokens}, output={output_tokens}, total={input_tokens + output_tokens}")

    def get_total_tokens(self) -> tuple[int, int, int]:
        """Get total tokens: (input, output, total)"""
        total = self.total_input_tokens + self.total_output_tokens
        return self.total_input_tokens, self.total_output_tokens, total

    def reset(self):
        """Reset the token counters"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
        self.calls = []


class MetricsCollector:
    """Collects metrics during node execution"""

    def __init__(self, member_name: str, team_name: str, node_name: str, round: int = 0):
        self.member_name = member_name
        self.team_name = team_name
        self.node_name = node_name
        self.round = round

        # Start time
        self.start_time = time.time()

        # Token tracking callback
        self.token_callback = TokenTrackingCallback()

        # Sub-phase tracking (optional)
        self.sub_phases: Dict[str, Dict[str, Any]] = {}
        self.current_phase_start: Optional[float] = None

        logger.info(f"[METRICS COLLECTOR] Initialized for {member_name}/{node_name} (Team: {team_name}, Round: {round})")

    def start_sub_phase(self, phase_name: str):
        """Start tracking a sub-phase within the node"""
        self.current_phase_start = time.time()
        logger.info(f"[METRICS COLLECTOR] Started sub-phase: {phase_name}")

    def end_sub_phase(self, phase_name: str, input_tokens: int = 0, output_tokens: int = 0):
        """End tracking a sub-phase"""
        if self.current_phase_start:
            elapsed = time.time() - self.current_phase_start
            self.sub_phases[phase_name] = {
                "phase_name": phase_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "timestamp": self.current_phase_start
            }
            logger.info(f"[METRICS COLLECTOR] Ended sub-phase: {phase_name} - "
                       f"Time: {elapsed:.2f}s, Tokens: {input_tokens + output_tokens}")
            self.current_phase_start = None

    def finalize(self) -> NodeExecutionMetrics:
        """Finalize and return node metrics"""
        end_time = time.time()
        elapsed_time = end_time - self.start_time

        # Get token totals from callback
        input_tokens, output_tokens, total_tokens = self.token_callback.get_total_tokens()

        # Create node metrics object
        metrics = NodeExecutionMetrics(
            team_name=self.team_name,
            member_name=self.member_name,
            round=self.round,
            node_name=self.node_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            elapsed_time_seconds=elapsed_time,
            llm_call_count=self.token_callback.call_count,
            sub_phases=self.sub_phases if self.sub_phases else None
        )

        logger.info(f"[METRICS COLLECTOR] Finalized metrics for {self.member_name}/{self.node_name}: "
                   f"Time={elapsed_time:.2f}s, Tokens={total_tokens}")

        return metrics


class MetricsAggregator:
    """Aggregates metrics across multiple nodes and team members"""

    def __init__(self):
        self.all_metrics: List[NodeExecutionMetrics] = []

    def add_metrics(self, metrics: NodeExecutionMetrics):
        """Add metrics from a single node execution"""
        self.all_metrics.append(metrics)
        logger.info(f"[METRICS AGGREGATOR] Added metrics for {metrics.member_name}/{metrics.node_name} "
                   f"(Total nodes tracked: {len(self.all_metrics)})")

    def get_team_summary(self, team_name: str) -> Dict[str, Any]:
        """Get aggregated metrics for a specific team"""
        team_metrics = [m for m in self.all_metrics if m.team_name == team_name]

        if not team_metrics:
            return {"team_name": team_name, "total_nodes": 0}

        total_time = sum(m.elapsed_time_seconds for m in team_metrics)
        total_tokens = sum(m.total_tokens for m in team_metrics)
        total_input = sum(m.input_tokens for m in team_metrics)
        total_output = sum(m.output_tokens for m in team_metrics)

        return {
            "team_name": team_name,
            "total_nodes": len(team_metrics),
            "total_time_seconds": total_time,
            "total_tokens": total_tokens,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "average_time_per_node": total_time / len(team_metrics) if team_metrics else 0,
            "average_tokens_per_node": total_tokens / len(team_metrics) if team_metrics else 0,
            "members": list(set(m.member_name for m in team_metrics)),
            "nodes": list(set(m.node_name for m in team_metrics))
        }

    def get_member_summary(self, member_name: str) -> Dict[str, Any]:
        """Get aggregated metrics for a specific member"""
        member_metrics = [m for m in self.all_metrics if m.member_name == member_name]

        if not member_metrics:
            return {"member_name": member_name, "total_nodes": 0}

        total_time = sum(m.elapsed_time_seconds for m in member_metrics)
        total_tokens = sum(m.total_tokens for m in member_metrics)
        total_input = sum(m.input_tokens for m in member_metrics)
        total_output = sum(m.output_tokens for m in member_metrics)

        return {
            "member_name": member_name,
            "team_name": member_metrics[0].team_name if member_metrics else None,
            "total_nodes": len(member_metrics),
            "total_time_seconds": total_time,
            "total_tokens": total_tokens,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "nodes": list(set(m.node_name for m in member_metrics)),
            "rounds": list(set(m.round for m in member_metrics))
        }

    def get_full_summary(self) -> Dict[str, Any]:
        """Get complete summary of all tracked metrics"""
        if not self.all_metrics:
            return {"total_nodes": 0}

        total_time = sum(m.elapsed_time_seconds for m in self.all_metrics)
        total_tokens = sum(m.total_tokens for m in self.all_metrics)
        total_input = sum(m.input_tokens for m in self.all_metrics)
        total_output = sum(m.output_tokens for m in self.all_metrics)

        teams = list(set(m.team_name for m in self.all_metrics))
        members = list(set(m.member_name for m in self.all_metrics))

        return {
            "total_nodes": len(self.all_metrics),
            "total_time_seconds": total_time,
            "total_tokens": total_tokens,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "teams": [self.get_team_summary(team) for team in teams],
            "members": [self.get_member_summary(member) for member in members],
            "all_node_metrics": [m.get_summary() for m in self.all_metrics]
        }
