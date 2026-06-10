"""
Data models for architecture testing service.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DebateRunResult:
    """Result from a single debate run."""

    team1_arch: str
    team2_arch: str
    team1_role: str  # "proposition" or "opposition"
    team2_role: str  # "proposition" or "opposition"
    status: str  # "success" | "failed"
    output_file: Optional[str]
    error: Optional[str] = None
    winner: Optional[str] = None  # "proposition" | "opposition" | "tie"
    vote_margin: Optional[int] = None  # Difference in votes


@dataclass
class BatchSummary:
    """Summary of all runs for one base config."""

    base_config_id: str
    base_config_path: str
    started_at: str
    finished_at: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    results_matrix: list[dict]
    errors: list[dict]
