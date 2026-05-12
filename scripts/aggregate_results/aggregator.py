"""
Architecture Metrics Aggregator

Class for tracking and aggregating metrics across multiple debates
for each architecture.
"""

import logging
import statistics
from typing import Dict, Any, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class ArchitectureMetricsAggregator:
    """
    Aggregates metrics across debates for each architecture.

    Tracks quality scores, token usage, execution time, and wins/losses
    for each architecture across multiple debate simulations.
    """

    def __init__(self):
        """Initialize the aggregator with empty metric storage."""
        # Dict of architecture -> list of values
        self.quality_scores: Dict[str, List[float]] = defaultdict(list)
        self.token_counts: Dict[str, List[int]] = defaultdict(list)
        self.time_seconds: Dict[str, List[float]] = defaultdict(list)
        self.wins: Dict[str, int] = defaultdict(int)
        self.total_debates: Dict[str, int] = defaultdict(int)

    def add_quality_score(self, architecture: str, score: float):
        """Add a quality score for an architecture."""
        if score is not None and 1.0 <= score <= 3.0:
            self.quality_scores[architecture].append(score)
        else:
            logger.warning(f"Invalid quality score {score} for {architecture}")

    def add_tokens(self, architecture: str, tokens: int):
        """Add token count for an architecture."""
        if tokens is not None and tokens > 0:
            self.token_counts[architecture].append(tokens)

    def add_time(self, architecture: str, time_sec: float):
        """Add execution time for an architecture."""
        if time_sec is not None and time_sec > 0:
            self.time_seconds[architecture].append(time_sec)

    def record_debate_outcome(
        self,
        prop_architecture: str,
        opp_architecture: str,
        winning_architecture: Optional[str]
    ):
        """
        Record the outcome of a debate.

        Args:
            prop_architecture: Architecture of proposition team
            opp_architecture: Architecture of opposition team
            winning_architecture: Architecture that won (or None for tie)
        """
        # Count participation
        self.total_debates[prop_architecture] += 1
        self.total_debates[opp_architecture] += 1

        # Count wins
        if winning_architecture == prop_architecture:
            self.wins[prop_architecture] += 1
        elif winning_architecture == opp_architecture:
            self.wins[opp_architecture] += 1
        # If tie or None, no wins recorded

    def calculate_aggregates(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate aggregate statistics for each architecture.

        Returns:
            Dict mapping architecture to aggregated metrics
        """
        aggregates = {}

        all_architectures = set(
            list(self.quality_scores.keys()) +
            list(self.token_counts.keys()) +
            list(self.time_seconds.keys()) +
            list(self.total_debates.keys())
        )

        for arch in all_architectures:
            arch_data = {}

            # Quality metrics
            if arch in self.quality_scores and self.quality_scores[arch]:
                scores = self.quality_scores[arch]
                arch_data['quality'] = {
                    'mean': statistics.mean(scores),
                    'std': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                    'min': min(scores),
                    'max': max(scores),
                    'count': len(scores)
                }
            else:
                arch_data['quality'] = None

            # Token metrics
            if arch in self.token_counts and self.token_counts[arch]:
                tokens = self.token_counts[arch]
                arch_data['tokens'] = {
                    'mean': statistics.mean(tokens),
                    'std': statistics.stdev(tokens) if len(tokens) > 1 else 0.0,
                    'min': min(tokens),
                    'max': max(tokens),
                    'count': len(tokens)
                }
            else:
                arch_data['tokens'] = None

            # Time metrics
            if arch in self.time_seconds and self.time_seconds[arch]:
                times = self.time_seconds[arch]
                arch_data['time_seconds'] = {
                    'mean': statistics.mean(times),
                    'std': statistics.stdev(times) if len(times) > 1 else 0.0,
                    'min': min(times),
                    'max': max(times),
                    'count': len(times)
                }
            else:
                arch_data['time_seconds'] = None

            # Win rate
            total = self.total_debates.get(arch, 0)
            wins = self.wins.get(arch, 0)

            if total > 0:
                arch_data['win_rate'] = (wins / total) * 100.0
                arch_data['debates'] = {
                    'total': total,
                    'wins': wins,
                    'losses': total - wins
                }
            else:
                arch_data['win_rate'] = None
                arch_data['debates'] = None

            aggregates[arch] = arch_data

        return aggregates

    def get_pareto_data(self) -> List[Dict[str, Any]]:
        """
        Generate data points for Pareto frontier visualization.

        Returns:
            List of dicts with architecture, quality, tokens, win_rate
        """
        aggregates = self.calculate_aggregates()
        pareto_points = []

        for arch, data in aggregates.items():
            # Only include architectures with both quality and token data
            if data.get('quality') and data.get('tokens'):
                point = {
                    'architecture': arch,
                    'quality': data['quality']['mean'],
                    'tokens': data['tokens']['mean'],
                    'time': data['time_seconds']['mean'] if data.get('time_seconds') else None,
                    'win_rate': data.get('win_rate', 0.0)
                }
                pareto_points.append(point)

        # Calculate which points are on the Pareto frontier
        pareto_points = self._mark_pareto_frontier(pareto_points)

        return pareto_points

    def _mark_pareto_frontier(self, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mark which points are on the Pareto frontier (non-dominated).

        A point is dominated if another point has:
        - Higher or equal quality AND lower or equal tokens
        - With at least one strict inequality

        Args:
            points: List of data points

        Returns:
            Same list with 'is_dominated' field added
        """
        for i, point_a in enumerate(points):
            is_dominated = False

            for j, point_b in enumerate(points):
                if i == j:
                    continue

                # Check if point_b dominates point_a
                # (better quality, fewer tokens)
                if (point_b['quality'] >= point_a['quality'] and
                    point_b['tokens'] <= point_a['tokens'] and
                    (point_b['quality'] > point_a['quality'] or
                     point_b['tokens'] < point_a['tokens'])):
                    is_dominated = True
                    break

            point_a['is_dominated'] = is_dominated

        return points

    def format_for_latex_table(self, aggregates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format aggregate data for LaTeX table generation.

        Args:
            aggregates: Output from calculate_aggregates()

        Returns:
            Dict with headers and rows for table
        """
        headers = ["Architecture", "Quality", "Tokens", "Time (s)", "Win Rate"]
        rows = []

        # Sort architectures by name
        for arch in sorted(aggregates.keys()):
            data = aggregates[arch]

            # Format values
            quality_str = f"{data['quality']['mean']:.2f}" if data.get('quality') else "N/A"
            tokens_str = f"{int(data['tokens']['mean']):,}" if data.get('tokens') else "N/A"
            time_str = f"{data['time_seconds']['mean']:.1f}" if data.get('time_seconds') else "N/A"
            win_rate_str = f"{data.get('win_rate', 0.0):.0f}%" if data.get('win_rate') is not None else "N/A"

            # Pretty architecture names
            arch_display = arch.replace('_', ' ').title()

            rows.append([arch_display, quality_str, tokens_str, time_str, win_rate_str])

        return {
            'headers': headers,
            'rows': rows
        }
