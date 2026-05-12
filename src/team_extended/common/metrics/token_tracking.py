"""
Token tracking utilities following SOLID principles.

This module provides a centralized, reusable way to track token usage
across all workflow nodes (analyser, knowledge_retrieval, argument_creator, evaluator).
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowNode(str, Enum):
    """Enum for workflow node names - ensures consistency"""
    ANALYSER = "analyser"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    CANDIDATE_CREATOR = "candidate_creator"
    ARGUMENT_CREATOR = "argument_creator"
    EVALUATOR = "evaluator"


@dataclass
class SubPhaseTokenUsage:
    """Token usage for a sub-phase within a node"""
    phase_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "phase_name": self.phase_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "timestamp": self.timestamp
        }


@dataclass
class NodeTokenUsage:
    """Token usage for a complete workflow node"""
    node_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    start_time: float = 0
    end_time: float = 0
    elapsed_time_seconds: float = 0
    sub_phases: Dict[str, SubPhaseTokenUsage] = field(default_factory=dict)
    llm_call_count: int = 0

    def add_sub_phase(self, phase: SubPhaseTokenUsage):
        """Add a sub-phase and update totals"""
        self.sub_phases[phase.phase_name] = phase
        self.input_tokens += phase.input_tokens
        self.output_tokens += phase.output_tokens
        self.total_tokens += phase.total_tokens
        self.llm_call_count += 1

    def add_tokens(self, input_tokens: int, output_tokens: int):
        """Add tokens directly (for nodes without sub-phases)"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += (input_tokens + output_tokens)
        self.llm_call_count += 1

    def finalize(self):
        """Finalize timing and recalculate totals"""
        if self.end_time == 0:
            self.end_time = time.time()
        if self.start_time > 0:
            self.elapsed_time_seconds = self.end_time - self.start_time

        # Recalculate total_tokens to ensure consistency
        self.total_tokens = self.input_tokens + self.output_tokens

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "node_name": self.node_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "elapsed_time_seconds": self.elapsed_time_seconds,
            "llm_call_count": self.llm_call_count
        }

        if self.sub_phases:
            result["sub_phases"] = {
                name: phase.to_dict()
                for name, phase in self.sub_phases.items()
            }

        return result


# SOLID: Interface Segregation Principle - separate interface for token extraction
class TokenUsageExtractor(ABC):
    """Abstract base class for extracting token usage from LLM responses"""

    @abstractmethod
    def extract(self, response: Any) -> tuple[int, int, int]:
        """
        Extract token usage from LLM response.

        Returns:
            tuple: (input_tokens, output_tokens, total_tokens)
        """
        pass


class StructuredOutputTokenExtractor(TokenUsageExtractor):
    """
    Extract tokens from structured output with include_raw=True.

    SOLID: Single Responsibility - only handles structured output extraction
    """

    def extract(self, response: Any) -> tuple[int, int, int]:
        """
        Extract from response with format: {"parsed": ..., "raw": AIMessage}
        """
        try:
            if isinstance(response, dict) and "raw" in response:
                raw_response = response["raw"]
                return self._extract_from_raw(raw_response)
            else:
                logger.warning("[TOKEN EXTRACTOR] Response is not a structured output dict with 'raw' key")
                return (0, 0, 0)
        except Exception as e:
            logger.error(f"[TOKEN EXTRACTOR] Error extracting tokens: {e}")
            return (0, 0, 0)

    def _extract_from_raw(self, raw_response: Any) -> tuple[int, int, int]:
        """Extract from raw AIMessage"""
        if hasattr(raw_response, 'usage_metadata') and raw_response.usage_metadata:
            usage = raw_response.usage_metadata
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
            return (input_tokens, output_tokens, total_tokens)
        return (0, 0, 0)


class StandardTokenExtractor(TokenUsageExtractor):
    """
    Extract tokens from standard LLM response (AIMessage).

    SOLID: Single Responsibility - only handles standard response extraction
    """

    def extract(self, response: Any) -> tuple[int, int, int]:
        """Extract from AIMessage directly"""
        try:
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
                return (input_tokens, output_tokens, total_tokens)
            return (0, 0, 0)
        except Exception as e:
            logger.error(f"[TOKEN EXTRACTOR] Error extracting tokens: {e}")
            return (0, 0, 0)


# SOLID: Single Responsibility - only tracks tokens for one node
class NodeTokenTracker:
    """
    Tracks token usage for a single workflow node.

    DRY: Reusable across all nodes
    SOLID: Single Responsibility - tracks one node
    """

    def __init__(self, node_name: str, extractor: Optional[TokenUsageExtractor] = None):
        """
        Initialize tracker for a specific node.

        Args:
            node_name: Name of the node (use WorkflowNode enum)
            extractor: Token extractor (defaults to StructuredOutputTokenExtractor)
        """
        self.node_usage = NodeTokenUsage(
            node_name=node_name,
            start_time=time.time()
        )
        self.extractor = extractor or StructuredOutputTokenExtractor()
        logger.info(f"[NODE TOKEN TRACKER] Initialized for node: {node_name}")

    def record_llm_call(self, response: Any, phase_name: Optional[str] = None):
        """
        Record token usage from an LLM call.

        Args:
            response: LLM response (structured output dict or AIMessage)
            phase_name: Optional sub-phase name
        """
        input_tokens, output_tokens, total_tokens = self.extractor.extract(response)

        if input_tokens == 0 and output_tokens == 0:
            logger.warning(f"[NODE TOKEN TRACKER] No tokens extracted from {self.node_usage.node_name}")
            return

        if phase_name:
            # Track as sub-phase
            sub_phase = SubPhaseTokenUsage(
                phase_name=phase_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens
            )
            self.node_usage.add_sub_phase(sub_phase)
            logger.info(f"[NODE TOKEN TRACKER] {self.node_usage.node_name}/{phase_name}: "
                       f"input={input_tokens}, output={output_tokens}, total={total_tokens}")
        else:
            # Track at node level
            self.node_usage.add_tokens(input_tokens, output_tokens)
            logger.info(f"[NODE TOKEN TRACKER] {self.node_usage.node_name}: "
                       f"input={input_tokens}, output={output_tokens}, total={total_tokens}")

    def finalize(self) -> NodeTokenUsage:
        """Finalize tracking and return usage data"""
        self.node_usage.finalize()
        logger.info(f"[NODE TOKEN TRACKER] Finalized {self.node_usage.node_name}: "
                   f"{self.node_usage.total_tokens} total tokens in "
                   f"{self.node_usage.elapsed_time_seconds:.2f}s")
        return self.node_usage


# SOLID: Single Responsibility - only aggregates tokens
class TokenUsageAggregator:
    """
    Aggregates token usage across all workflow nodes.

    DRY: Centralized aggregation logic
    SOLID: Single Responsibility - aggregation only
    """

    def __init__(self):
        self.node_usages: Dict[str, NodeTokenUsage] = {}

    def add_node_usage(self, node_usage: NodeTokenUsage):
        """Add usage data from a node"""
        self.node_usages[node_usage.node_name] = node_usage
        logger.info(f"[TOKEN AGGREGATOR] Added {node_usage.node_name}: {node_usage.total_tokens} tokens")

    def get_total_tokens(self) -> tuple[int, int, int]:
        """
        Get total tokens across all nodes.

        Returns:
            tuple: (total_input, total_output, total_tokens)
        """
        total_input = sum(usage.input_tokens for usage in self.node_usages.values())
        total_output = sum(usage.output_tokens for usage in self.node_usages.values())
        total = total_input + total_output
        return (total_input, total_output, total)

    def get_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed breakdown by node"""
        return {
            node_name: usage.to_dict()
            for node_name, usage in self.node_usages.items()
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get summary with totals and breakdown"""
        total_input, total_output, total = self.get_total_tokens()

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total,
            "total_llm_calls": sum(usage.llm_call_count for usage in self.node_usages.values()),
            "node_breakdown": self.get_breakdown()
        }

    def validate(self) -> bool:
        """
        Validate that token totals are consistent.

        Returns:
            bool: True if validation passes
        """
        total_input, total_output, total = self.get_total_tokens()
        calculated_total = total_input + total_output

        if total != calculated_total:
            logger.error(f"[TOKEN AGGREGATOR] Validation failed: "
                        f"total={total} != calculated={calculated_total}")
            return False

        logger.info(f"[TOKEN AGGREGATOR] Validation passed: {total} total tokens")
        return True


# DRY: Helper function to create tracker with correct extractor type
def create_node_tracker(
    node_name: str,
    use_structured_output: bool = True
) -> NodeTokenTracker:
    """
    Factory function to create node tracker with appropriate extractor.

    DRY: Centralized creation logic
    SOLID: Dependency Inversion - depends on abstraction (TokenUsageExtractor)

    Args:
        node_name: Name of the node
        use_structured_output: Whether node uses structured output (include_raw=True)

    Returns:
        NodeTokenTracker configured with appropriate extractor
    """
    extractor = (
        StructuredOutputTokenExtractor()
        if use_structured_output
        else StandardTokenExtractor()
    )
    return NodeTokenTracker(node_name, extractor)
