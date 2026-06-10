"""
Debate runner for architecture testing.

Runs individual debates and handles errors gracefully.
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.debate_extended.debate_config import create_debate_from_config

from .models import DebateRunResult


def extract_winner_from_results(results: Dict[str, Any]) -> tuple[Optional[str], Optional[int]]:
    """
    Extract winner and vote margin from debate results.

    Args:
        results: Debate results dictionary

    Returns:
        Tuple of (winner, vote_margin)
        - winner: "proposition" | "opposition" | "tie" | None
        - vote_margin: Difference in votes | None
    """
    try:
        # Try to use new prefixed fields first
        final_winning_team = results.get("final_winning_team")
        final_margin = results.get("final_margin_of_victory")

        if final_winning_team and final_margin is not None:
            return final_winning_team, final_margin

        # Fallback to old fields for backwards compatibility
        winning_team = results.get("winning_team")
        margin_of_victory = results.get("margin_of_victory")

        if winning_team and margin_of_victory is not None:
            return winning_team, margin_of_victory

        # Fallback to counting votes manually (legacy behavior)
        final_votes = results.get("audience_final_votes", [])
        if not final_votes:
            return None, None

        # Count votes
        agree_count = sum(1 for v in final_votes if v.get("decision") == "agree")
        disagree_count = sum(1 for v in final_votes if v.get("decision") == "disagree")

        margin = abs(agree_count - disagree_count)

        if agree_count > disagree_count:
            winner = "proposition"
        elif disagree_count > agree_count:
            winner = "opposition"
        else:
            winner = "tie"

        return winner, margin

    except Exception:
        return None, None


def run_single_debate(
    config: Dict[str, Any],
    team1_arch: str,
    team2_arch: str,
    team1_role: str,
    team2_role: str,
) -> DebateRunResult:
    """
    Run a single debate from a config dictionary.

    Process:
    1. Write config to temporary JSON file
    2. Run debate using create_debate_from_config()
    3. Extract winner and vote margin from results
    4. Handle errors gracefully

    Args:
        config: Debate configuration dictionary
        team1_arch: Team 1 architecture short name
        team2_arch: Team 2 architecture short name
        team1_role: Team 1 role (proposition/opposition)
        team2_role: Team 2 role (proposition/opposition)

    Returns:
        DebateRunResult with status, output file, and optional winner/error
    """
    output_file = config.get("output_file")

    try:
        # Write config to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            json.dump(config, tmp, indent=2, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            # Run debate
            results = create_debate_from_config(tmp_path)

            # Extract winner and margin
            winner, vote_margin = extract_winner_from_results(results)

            return DebateRunResult(
                team1_arch=team1_arch,
                team2_arch=team2_arch,
                team1_role=team1_role,
                team2_role=team2_role,
                status="success",
                output_file=output_file,
                winner=winner,
                vote_margin=vote_margin,
            )

        finally:
            # Clean up temporary file
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass

    except Exception as e:
        return DebateRunResult(
            team1_arch=team1_arch,
            team2_arch=team2_arch,
            team1_role=team1_role,
            team2_role=team2_role,
            status="failed",
            output_file=output_file,
            error=str(e),
        )
