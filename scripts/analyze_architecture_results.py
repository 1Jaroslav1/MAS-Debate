#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Architecture Results Analyzer

Analyzes debate results to extract architecture performance metrics.
Can analyze individual result files or entire batch summaries.

Usage:
    # Analyze a single result file
    python analyze_architecture_results.py --file path/to/result.json

    # Analyze a batch summary
    python analyze_architecture_results.py --batch path/to/batch_summary.json

    # Analyze all batches in a directory
    python analyze_architecture_results.py --dir architecture_tests/
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict


def extract_architecture_from_result(result_file: Path) -> Dict[str, Any]:
    """
    Extract architecture information from a single result file.

    Args:
        result_file: Path to result JSON file

    Returns:
        Dictionary with architecture details and outcome
    """
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    architectures = data.get("team_architectures", {})
    winner = data.get("final_winning_team")
    margin = data.get("final_margin_of_victory")

    return {
        "topic": data.get("topic", "Unknown"),
        "winner": winner,
        "margin": margin,
        "architectures": architectures,
        "rounds_completed": data.get("rounds_completed"),
        "max_rounds": data.get("max_rounds"),
    }


def analyze_batch_summary(batch_file: Path) -> Dict[str, Any]:
    """
    Analyze architecture performance from batch summary.

    Args:
        batch_file: Path to batch_summary.json

    Returns:
        Analysis results with architecture performance metrics
    """
    with open(batch_file, "r", encoding="utf-8") as f:
        batch = json.load(f)

    # Track wins by architecture
    arch_wins = defaultdict(int)
    arch_matchups = defaultdict(list)
    total_successful = 0

    for result in batch.get("results_matrix", []):
        if result.get("status") != "success":
            continue

        total_successful += 1
        team1_arch = result.get("team1_arch")
        team2_arch = result.get("team2_arch")
        winner = result.get("winner")
        margin = result.get("vote_margin")

        matchup_key = f"{team1_arch}_vs_{team2_arch}"
        arch_matchups[matchup_key].append({
            "winner": winner,
            "margin": margin,
            "team1_role": result.get("team1_role"),
        })

        # Track architecture wins
        arch_details = result.get("architecture_details", {})
        for team_name, details in arch_details.items():
            arch = details.get("architecture")
            if team_name == winner:
                arch_wins[arch] += 1

    # Calculate win rates
    arch_stats = {}
    for arch, wins in arch_wins.items():
        # Count total appearances (as either team1 or team2)
        total_appearances = sum(
            1 for result in batch.get("results_matrix", [])
            if result.get("status") == "success" and
            (arch in [result.get("team1_arch"), result.get("team2_arch")])
        )

        arch_stats[arch] = {
            "wins": wins,
            "appearances": total_appearances,
            "win_rate": wins / total_appearances if total_appearances > 0 else 0,
        }

    return {
        "base_config": batch.get("base_config_id"),
        "total_runs": batch.get("total_runs"),
        "successful_runs": total_successful,
        "failed_runs": batch.get("failed_runs"),
        "architecture_stats": arch_stats,
        "matchup_details": dict(arch_matchups),
    }


def print_architecture_analysis(analysis: Dict[str, Any]) -> None:
    """Print formatted architecture analysis."""
    print("\n" + "=" * 80)
    print(f"Architecture Performance Analysis: {analysis['base_config']}")
    print("=" * 80)

    print(f"\nTotal Runs: {analysis['total_runs']}")
    print(f"Successful: {analysis['successful_runs']}")
    print(f"Failed: {analysis['failed_runs']}")

    print("\n" + "-" * 80)
    print("Architecture Win Rates:")
    print("-" * 80)

    stats = analysis["architecture_stats"]
    sorted_archs = sorted(
        stats.items(),
        key=lambda x: x[1]["win_rate"],
        reverse=True
    )

    for arch, data in sorted_archs:
        win_rate = data["win_rate"] * 100
        print(f"{arch:15} | Wins: {data['wins']:2} / {data['appearances']:2} appearances | Win Rate: {win_rate:5.1f}%")

    print("\n" + "-" * 80)
    print("Head-to-Head Matchups:")
    print("-" * 80)

    for matchup, results in sorted(analysis["matchup_details"].items()):
        if not results:
            continue

        team1_arch, team2_arch = matchup.split("_vs_")
        print(f"\n{team1_arch} vs {team2_arch}:")

        # Count wins for each
        winners = [r["winner"] for r in results if r["winner"]]
        if winners:
            # Use architecture details to determine which won
            print(f"  Games played: {len(results)}")
            avg_margin = sum(r["margin"] for r in results if r["margin"]) / len(results)
            print(f"  Average margin: {avg_margin:.1f}")


def analyze_directory(dir_path: Path) -> List[Dict[str, Any]]:
    """
    Analyze all batch summaries in a directory.

    Args:
        dir_path: Directory containing batch folders

    Returns:
        List of analysis results
    """
    results = []

    # Find all batch_summary.json files
    batch_files = list(dir_path.rglob("batch_summary.json"))

    print(f"\nFound {len(batch_files)} batch summaries in {dir_path}")

    for batch_file in batch_files:
        print(f"\nAnalyzing: {batch_file.parent.name}")
        analysis = analyze_batch_summary(batch_file)
        results.append(analysis)
        print_architecture_analysis(analysis)

    return results


def main():
    parser = argparse.ArgumentParser(description="Analyze architecture performance from debate results")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Single result file to analyze")
    group.add_argument("--batch", type=str, help="Batch summary file to analyze")
    group.add_argument("--dir", type=str, help="Directory containing batch summaries")

    args = parser.parse_args()

    if args.file:
        result_file = Path(args.file)
        info = extract_architecture_from_result(result_file)
        print(json.dumps(info, indent=2))

    elif args.batch:
        batch_file = Path(args.batch)
        analysis = analyze_batch_summary(batch_file)
        print_architecture_analysis(analysis)

    elif args.dir:
        dir_path = Path(args.dir)
        analyze_directory(dir_path)


if __name__ == "__main__":
    main()
