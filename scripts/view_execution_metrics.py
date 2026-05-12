"""
Utility script to view execution metrics from debate results.

This script reads a debate results JSON file and displays the execution metrics
in a human-readable format.

Usage:
    python scripts/view_execution_metrics.py <path_to_results.json>
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def format_time(seconds: float) -> str:
    """Format time in seconds to a human-readable string"""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"


def format_cost(cost_usd: float) -> str:
    """Format cost in USD"""
    if cost_usd < 0.01:
        return f"${cost_usd * 1000:.3f} (${cost_usd:.6f})"
    else:
        return f"${cost_usd:.4f}"


def print_separator(char="=", length=80):
    """Print a separator line"""
    print(char * length)


def print_metrics_summary(metrics: Dict[str, Any]):
    """Print a formatted summary of execution metrics"""
    if not metrics:
        print("No execution metrics found in the results.")
        return

    print_separator("=")
    print("EXECUTION METRICS SUMMARY")
    print_separator("=")
    print()

    # Overall summary
    print("OVERALL STATISTICS:")
    print(f"  Total Executions: {metrics.get('total_executions', 0)}")
    print(f"  Total Time: {format_time(metrics.get('total_time_seconds', 0))}")
    print(f"  Total Tokens: {metrics.get('total_tokens', 0):,}")
    print(f"    - Input Tokens: {metrics.get('total_input_tokens', 0):,}")
    print(f"    - Output Tokens: {metrics.get('total_output_tokens', 0):,}")
    print(f"  Total Cost: {format_cost(metrics.get('total_cost_usd', 0))}")
    print()

    # Team summaries
    teams = metrics.get('teams', [])
    if teams:
        print_separator("-")
        print("TEAM SUMMARIES:")
        print_separator("-")
        for team in teams:
            print(f"\nTeam: {team.get('team_name', 'Unknown')}")
            print(f"  Executions: {team.get('total_executions', 0)}")
            print(f"  Total Time: {format_time(team.get('total_time_seconds', 0))}")
            print(f"  Total Tokens: {team.get('total_tokens', 0):,}")
            print(f"  Total Cost: {format_cost(team.get('total_cost_usd', 0))}")
            print(f"  Average Time/Execution: {format_time(team.get('average_time_per_execution', 0))}")
            print(f"  Average Tokens/Execution: {team.get('average_tokens_per_execution', 0):,.0f}")
            print(f"  Members: {', '.join(team.get('members', []))}")

    # Member summaries
    members = metrics.get('members', [])
    if members:
        print()
        print_separator("-")
        print("MEMBER SUMMARIES:")
        print_separator("-")
        for member in members:
            print(f"\nMember: {member.get('member_name', 'Unknown')}")
            print(f"  Team: {member.get('team_name', 'Unknown')}")
            print(f"  Executions: {member.get('total_executions', 0)}")
            print(f"  Total Time: {format_time(member.get('total_time_seconds', 0))}")
            print(f"  Total Tokens: {member.get('total_tokens', 0):,}")
            print(f"    - Input: {member.get('total_input_tokens', 0):,}")
            print(f"    - Output: {member.get('total_output_tokens', 0):,}")
            print(f"  Total Cost: {format_cost(member.get('total_cost_usd', 0))}")
            print(f"  Iterations: {member.get('iterations', [])}")

    print()
    print_separator("=")


def print_detailed_metrics(results: Dict[str, Any]):
    """Print detailed metrics from each argument in the log"""
    argument_log = results.get('arguments', [])
    if not argument_log:
        print("\nNo arguments found in the log.")
        return

    print()
    print_separator("=")
    print("DETAILED ARGUMENT METRICS")
    print_separator("=")

    for idx, arg in enumerate(argument_log, 1):
        exec_metrics = arg.get('execution_metrics')
        if not exec_metrics:
            continue

        print(f"\nArgument #{idx}")
        print(f"  Round: {arg.get('round', 'N/A')}")
        print(f"  Team: {arg.get('team', 'N/A')}")
        print(f"  Member: {exec_metrics.get('member_name', 'N/A')}")
        print(f"  Iteration: {exec_metrics.get('iteration_number', 'N/A')}")
        print(f"  Total Time: {format_time(exec_metrics.get('total_time_seconds', 0))}")
        print(f"  Total Tokens: {exec_metrics.get('total_tokens', 0):,}")
        print(f"  Cost: {format_cost(exec_metrics.get('estimated_cost_usd', 0))}")

        # Breakdown by phase
        breakdown = exec_metrics.get('breakdown', {})
        if breakdown:
            print("  Phase Breakdown:")
            for phase_name, phase_data in breakdown.items():
                if phase_data:
                    print(f"    {phase_name.replace('_', ' ').title()}:")
                    print(f"      Time: {format_time(phase_data.get('time_seconds', 0))}")
                    print(f"      Tokens: {phase_data.get('tokens', 0):,}")

    print()
    print_separator("=")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/view_execution_metrics.py <path_to_results.json>")
        print("\nExample:")
        print("  python scripts/view_execution_metrics.py results/debate_results.json")
        sys.exit(1)

    results_path = Path(sys.argv[1])

    if not results_path.exists():
        print(f"Error: File not found: {results_path}")
        sys.exit(1)

    # Load the results
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to read file: {e}")
        sys.exit(1)

    # Print metrics
    print(f"\nLoading metrics from: {results_path}")
    print()

    # Print summary metrics
    metrics = results.get('execution_metrics')
    if metrics:
        print_metrics_summary(metrics)

    # Print detailed metrics
    if '--detailed' in sys.argv or '-d' in sys.argv:
        print_detailed_metrics(results)

    # Print usage tip
    print("\nTip: Use --detailed or -d flag to see detailed per-argument metrics")
    print("Example: python scripts/view_execution_metrics.py <file.json> --detailed")


if __name__ == "__main__":
    main()
