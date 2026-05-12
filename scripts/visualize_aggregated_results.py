"""
Visualization Script for Aggregated Debate Results

This script creates visualizations from aggregated debate results,
including Pareto frontier plots and metrics comparisons.

Usage:
    python scripts/visualize_aggregated_results.py <aggregated_results.json>

Example:
    python scripts/visualize_aggregated_results.py aggregated_results.json
"""

import json
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ImportError:
    print("ERROR: matplotlib is required for visualization")
    print("Install with: pip install matplotlib")
    sys.exit(1)


def load_data(file_path: Path) -> dict:
    """Load aggregated results JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_pareto_plot(data: dict, output_file: str = 'pareto_frontier.png'):
    """
    Create Pareto frontier scatter plot.

    Args:
        data: Aggregated results data
        output_file: Path to save the plot
    """
    pareto_points = data['pareto_frontier']

    if not pareto_points:
        print("No Pareto frontier data available")
        return

    # Separate frontier and dominated points
    frontier = [p for p in pareto_points if not p['is_dominated']]
    dominated = [p for p in pareto_points if p['is_dominated']]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot dominated points
    if dominated:
        for point in dominated:
            ax.scatter(
                point['tokens'] / 1000,
                point['quality'],
                s=point['win_rate'] * 10,
                c='lightblue',
                alpha=0.5,
                edgecolors='blue',
                linewidth=1
            )
            ax.text(
                point['tokens'] / 1000,
                point['quality'] + 0.02,
                point['architecture'],
                fontsize=9,
                ha='center',
                alpha=0.7
            )

    # Plot frontier points
    if frontier:
        frontier_x = []
        frontier_y = []

        for point in frontier:
            x = point['tokens'] / 1000
            y = point['quality']
            frontier_x.append(x)
            frontier_y.append(y)

            ax.scatter(
                x, y,
                s=point['win_rate'] * 10,
                c='red',
                alpha=0.7,
                edgecolors='darkred',
                linewidth=2,
                zorder=5
            )
            ax.text(
                x, y + 0.02,
                point['architecture'],
                fontsize=10,
                fontweight='bold',
                ha='center'
            )

        # Draw frontier line
        if len(frontier) > 1:
            sorted_frontier = sorted(zip(frontier_x, frontier_y))
            fx, fy = zip(*sorted_frontier)
            ax.plot(fx, fy, 'r--', alpha=0.5, linewidth=1, zorder=4)

    # Styling
    ax.set_xlabel('Total Tokens (thousands)', fontsize=12)
    ax.set_ylabel('Argument Quality Score (1-3)', fontsize=12)
    ax.set_title('Pareto Frontier: Quality vs Computational Cost',
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(1.0, 3.0)

    # Legend
    frontier_patch = mpatches.Patch(color='red', label='Pareto Frontier')
    if dominated:
        dominated_patch = mpatches.Patch(color='lightblue', label='Dominated')
        ax.legend(handles=[frontier_patch, dominated_patch], loc='best')
    else:
        ax.legend(handles=[frontier_patch], loc='best')

    # Note
    ax.text(
        0.02, 0.98,
        'Note: Point size scaled by win rate',
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3)
    )

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def create_metrics_comparison(data: dict, output_file: str = 'metrics_comparison.png'):
    """
    Create bar chart comparing metrics across architectures.

    Args:
        data: Aggregated results data
        output_file: Path to save the plot
    """
    metrics = data['architecture_metrics']
    archs = sorted(metrics.keys())

    # Extract data
    qualities = [metrics[a]['quality']['mean'] if metrics[a]['quality'] else 0
                for a in archs]
    tokens = [metrics[a]['tokens']['mean'] / 1000 if metrics[a]['tokens'] else 0
             for a in archs]
    times = [metrics[a]['time_seconds']['mean'] if metrics[a]['time_seconds'] else 0
            for a in archs]
    win_rates = [metrics[a]['win_rate'] if metrics[a]['win_rate'] is not None else 0
                for a in archs]

    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Quality
    axes[0, 0].bar(archs, qualities, color='steelblue', alpha=0.7)
    axes[0, 0].set_ylabel('Quality Score')
    axes[0, 0].set_title('Average Argument Quality')
    axes[0, 0].set_ylim(0, 3)
    axes[0, 0].grid(axis='y', alpha=0.3)
    axes[0, 0].tick_params(axis='x', rotation=45)

    # Tokens
    axes[0, 1].bar(archs, tokens, color='coral', alpha=0.7)
    axes[0, 1].set_ylabel('Tokens (thousands)')
    axes[0, 1].set_title('Average Token Usage')
    axes[0, 1].grid(axis='y', alpha=0.3)
    axes[0, 1].tick_params(axis='x', rotation=45)

    # Time
    axes[1, 0].bar(archs, times, color='mediumseagreen', alpha=0.7)
    axes[1, 0].set_ylabel('Time (seconds)')
    axes[1, 0].set_title('Average Execution Time')
    axes[1, 0].grid(axis='y', alpha=0.3)
    axes[1, 0].tick_params(axis='x', rotation=45)

    # Win rate
    axes[1, 1].bar(archs, win_rates, color='gold', alpha=0.7)
    axes[1, 1].set_ylabel('Win Rate (%)')
    axes[1, 1].set_title('Debate Win Rate')
    axes[1, 1].set_ylim(0, 100)
    axes[1, 1].grid(axis='y', alpha=0.3)
    axes[1, 1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def print_summary(data: dict):
    """Print formatted summary to console."""
    table = data['latex_table']
    headers = table['headers']
    rows = table['rows']

    # Calculate column widths
    widths = [max(len(str(h)), max(len(str(r[i])) for r in rows))
             for i, h in enumerate(headers)]

    # Print header
    line = " | ".join(f"{h:<{widths[i]}}" for i, h in enumerate(headers))
    print("\n" + "=" * len(line))
    print(line)
    print("=" * len(line))

    # Print rows
    for row in rows:
        line = " | ".join(f"{str(r):<{widths[i]}}" for i, r in enumerate(row))
        print(line)

    print("=" * len(line) + "\n")


def main():
    """Main execution."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/visualize_aggregated_results.py <aggregated_results.json>")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    print("Loading aggregated results...")
    data = load_data(input_file)

    meta = data['metadata']
    print(f"\nProcessed {meta['total_folders_processed']} folders")
    print(f"Architectures: {', '.join(meta['architectures'])}")

    # Print summary
    print("\nArchitecture Metrics Summary:")
    print_summary(data)

    # Pareto info
    frontier = [p for p in data['pareto_frontier'] if not p['is_dominated']]
    print(f"Pareto frontier: {len(frontier)} non-dominated solutions")
    for point in frontier:
        print(f"  • {point['architecture']}: Quality={point['quality']:.2f}, "
              f"Tokens={point['tokens']:.0f}, Win={point['win_rate']:.0f}%")

    # Create visualizations
    print("\nGenerating visualizations...")
    output_dir = input_file.parent
    create_pareto_plot(data, str(output_dir / 'pareto_frontier.png'))
    create_metrics_comparison(data, str(output_dir / 'metrics_comparison.png'))

    print("\n✓ Complete! Check the generated PNG files in:", output_dir)


if __name__ == "__main__":
    main()
