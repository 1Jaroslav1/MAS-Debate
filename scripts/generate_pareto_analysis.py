"""
Generate Pareto Frontier Analysis and Results Tables

This script creates publication-quality tables and charts demonstrating
that architectural rankings are complexity-dependent.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Tuple
import argparse
from scipy.spatial import ConvexHull


class ParetoAnalyzer:
    """Analyze and visualize Pareto frontiers for debate architectures."""

    def __init__(self, quality_scores_path: Path, execution_metrics_path: Path = None):
        """
        Initialize analyzer with quality and execution data.

        Args:
            quality_scores_path: Path to quality_scores.csv
            execution_metrics_path: Path to execution metrics (optional)
        """
        self.quality_df = pd.read_csv(quality_scores_path)
        self.execution_metrics = self._load_execution_metrics(execution_metrics_path)

        # Calculate complexity scores
        self._calculate_complexity_scores()

    def _load_execution_metrics(self, path: Path = None) -> pd.DataFrame:
        """Load execution metrics from simulation results."""
        if path and path.exists():
            return pd.read_csv(path)

        # If no metrics file, extract from simulation results
        metrics_data = []

        results_dir = Path("results")
        if results_dir.exists():
            for result_file in results_dir.glob("*.json"):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    exec_metrics = data.get("execution_metrics", {})
                    for team_data in exec_metrics.get("teams", []):
                        metrics_data.append({
                            "config_id": data.get("config_id"),
                            "team_name": team_data.get("team_name"),
                            "total_tokens": team_data.get("total_tokens", 0),
                            "total_time_seconds": team_data.get("total_time_seconds", 0),
                            "total_nodes": team_data.get("total_nodes", 0)
                        })
                except Exception as e:
                    print(f"Warning: Could not load {result_file.name}: {e}")

        return pd.DataFrame(metrics_data) if metrics_data else pd.DataFrame()

    def _calculate_complexity_scores(self):
        """Calculate normalized complexity scores (0-100)."""
        # Merge execution metrics with quality scores
        if not self.execution_metrics.empty:
            self.quality_df = self.quality_df.merge(
                self.execution_metrics,
                on=["config_id", "team_name"],
                how="left"
            )

        # Fill missing values with estimates
        self.quality_df['total_tokens'] = self.quality_df.get('total_tokens', 5000)
        self.quality_df['total_time_seconds'] = self.quality_df.get('total_time_seconds', 60)
        self.quality_df['total_nodes'] = self.quality_df.get('total_nodes', 2)

        # Normalize each component to 0-1
        max_tokens = self.quality_df['total_tokens'].max() if self.quality_df['total_tokens'].max() > 0 else 1
        max_time = self.quality_df['total_time_seconds'].max() if self.quality_df['total_time_seconds'].max() > 0 else 1
        max_nodes = self.quality_df['total_nodes'].max() if self.quality_df['total_nodes'].max() > 0 else 1

        # Weighted composite complexity score (0-100)
        self.quality_df['complexity_score'] = (
            (self.quality_df['total_tokens'] / max_tokens) * 40 +  # 40% weight on tokens
            (self.quality_df['total_time_seconds'] / max_time) * 35 +  # 35% weight on time
            (self.quality_df['total_nodes'] / max_nodes) * 25  # 25% weight on nodes
        )

        # Efficiency metrics
        self.quality_df['quality_per_1k_tokens'] = (
            self.quality_df['avg_overall_score'] /
            (self.quality_df['total_tokens'] / 1000)
        )
        self.quality_df['quality_per_minute'] = (
            self.quality_df['avg_overall_score'] /
            (self.quality_df['total_time_seconds'] / 60)
        )

    def identify_pareto_frontier(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Identify points on the Pareto frontier.

        Args:
            data: DataFrame with 'complexity_score' and 'avg_overall_score'

        Returns:
            DataFrame with additional 'is_pareto' column
        """
        if data is None:
            data = self.quality_df.copy()

        data['is_pareto'] = False

        # For each point, check if it's dominated by any other point
        for idx, row in data.iterrows():
            is_dominated = False

            for _, other_row in data.iterrows():
                # Other point dominates if it has:
                # - Higher or equal quality AND lower complexity, OR
                # - Higher quality AND lower or equal complexity
                if (
                    (other_row['avg_overall_score'] >= row['avg_overall_score'] and
                     other_row['complexity_score'] < row['complexity_score']) or
                    (other_row['avg_overall_score'] > row['avg_overall_score'] and
                     other_row['complexity_score'] <= row['complexity_score'])
                ):
                    is_dominated = True
                    break

            if not is_dominated:
                data.at[idx, 'is_pareto'] = True

        return data

    def classify_topic_complexity(self, config_id: str) -> str:
        """
        Classify topic complexity (simple/medium/complex).

        This is a placeholder - adjust based on your actual complexity metrics.
        """
        # Example classification based on config_id patterns
        simple_topics = ['red_meat', 'commercial_space']
        complex_topics = ['artificial_consciousn', 'mind_uploading', 'genetic_modification']

        if any(s in config_id for s in simple_topics):
            return 'simple'
        elif any(s in config_id for s in complex_topics):
            return 'complex'
        else:
            return 'medium'

    def generate_summary_table(self) -> pd.DataFrame:
        """Generate Table 1: Architecture Performance Summary."""
        # Group by architecture (extract from team_name or config)
        # This is a simplified version - adjust based on your naming convention

        self.quality_df['architecture'] = self.quality_df['team_name'].apply(
            self._extract_architecture
        )

        summary = self.quality_df.groupby('architecture').agg({
            'config_id': 'count',
            'avg_overall_score': ['mean', 'std'],
            'won_quality': lambda x: (x.sum() / len(x)) * 100,
            'complexity_score': 'mean',
            'total_tokens': 'mean',
            'total_time_seconds': 'mean'
        }).round(2)

        summary.columns = [
            'debates_n',
            'quality_mean',
            'quality_std',
            'win_rate_pct',
            'complexity_score',
            'tokens_mean',
            'time_mean'
        ]

        # Determine Pareto status
        pareto_data = self.identify_pareto_frontier(
            self.quality_df.groupby('architecture').agg({
                'avg_overall_score': 'mean',
                'complexity_score': 'mean'
            }).reset_index()
        )

        pareto_status = dict(zip(
            pareto_data['architecture'],
            ['Frontier' if p else 'Non-optimal' for p in pareto_data['is_pareto']]
        ))

        summary['pareto_status'] = summary.index.map(pareto_status)

        return summary

    def _extract_architecture(self, team_name: str) -> str:
        """Extract architecture type from team name."""
        # Adjust this based on your actual naming convention
        if 'cot' in team_name.lower():
            return 'CoT'
        elif 'tot' in team_name.lower():
            return 'ToT'
        elif 'hybrid' in team_name.lower():
            return 'Hybrid'
        else:
            return 'Unknown'

    def plot_pareto_frontier(
        self,
        output_path: Path,
        by_complexity: bool = False
    ):
        """
        Create Pareto frontier visualization.

        Args:
            output_path: Path to save figure
            by_complexity: If True, create separate plots by topic complexity
        """
        if by_complexity:
            self._plot_pareto_by_complexity(output_path)
        else:
            self._plot_pareto_overall(output_path)

    def _plot_pareto_overall(self, output_path: Path):
        """Plot overall Pareto frontier."""
        # Aggregate by architecture
        arch_data = self.quality_df.groupby('architecture').agg({
            'avg_overall_score': 'mean',
            'complexity_score': 'mean',
            'total_tokens': 'mean',
            'total_time_seconds': 'mean'
        }).reset_index()

        # Identify Pareto frontier
        arch_data = self.identify_pareto_frontier(arch_data)

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 7))

        # Plot all points
        colors = {'CoT': 'blue', 'ToT': 'red', 'Hybrid': 'green', 'Unknown': 'gray'}

        for arch in arch_data['architecture'].unique():
            arch_subset = arch_data[arch_data['architecture'] == arch]
            is_pareto = arch_subset['is_pareto'].iloc[0]

            ax.scatter(
                arch_subset['complexity_score'],
                arch_subset['avg_overall_score'],
                c=colors.get(arch, 'gray'),
                s=200,
                marker='D' if is_pareto else 'o',
                label=f"{arch} {'(Frontier)' if is_pareto else ''}",
                edgecolors='black',
                linewidths=2 if is_pareto else 1,
                zorder=3 if is_pareto else 2
            )

            # Add labels
            ax.annotate(
                arch,
                (arch_subset['complexity_score'].iloc[0],
                 arch_subset['avg_overall_score'].iloc[0]),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=10,
                fontweight='bold' if is_pareto else 'normal'
            )

        # Draw Pareto frontier line
        frontier_points = arch_data[arch_data['is_pareto']].sort_values('complexity_score')
        if len(frontier_points) > 1:
            ax.plot(
                frontier_points['complexity_score'],
                frontier_points['avg_overall_score'],
                'k--',
                linewidth=2,
                label='Pareto Frontier',
                alpha=0.6,
                zorder=1
            )

            # Shade dominated region
            ax.fill_between(
                frontier_points['complexity_score'],
                0,
                frontier_points['avg_overall_score'],
                alpha=0.1,
                color='gray',
                label='Dominated Region'
            )

        ax.set_xlabel('Complexity Score (0-100)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Average Quality Score (0-10)', fontsize=12, fontweight='bold')
        ax.set_title(
            'Pareto Frontier: Quality vs Complexity\n'
            '(Architectural Trade-off Analysis)',
            fontsize=14,
            fontweight='bold'
        )
        ax.grid(True, alpha=0.3)
        ax.legend(loc='lower right', fontsize=10)

        # Set axis limits
        ax.set_xlim(-5, 105)
        ax.set_ylim(
            arch_data['avg_overall_score'].min() - 0.5,
            arch_data['avg_overall_score'].max() + 0.5
        )

        plt.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Pareto frontier plot saved: {output_path}")

    def _plot_pareto_by_complexity(self, output_path: Path):
        """Plot Pareto frontiers separated by topic complexity."""
        # Add complexity classification
        self.quality_df['topic_complexity'] = self.quality_df['config_id'].apply(
            self.classify_topic_complexity
        )

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        complexity_levels = ['simple', 'medium', 'complex']

        for idx, complexity in enumerate(complexity_levels):
            ax = axes[idx]

            # Filter data
            subset = self.quality_df[
                self.quality_df['topic_complexity'] == complexity
            ]

            if subset.empty:
                continue

            # Aggregate by architecture
            arch_data = subset.groupby('architecture').agg({
                'avg_overall_score': 'mean',
                'complexity_score': 'mean',
                'won_quality': lambda x: (x.sum() / len(x)) * 100
            }).reset_index()

            # Identify Pareto frontier
            arch_data = self.identify_pareto_frontier(arch_data)

            # Plot
            colors = {'CoT': 'blue', 'ToT': 'red', 'Hybrid': 'green'}

            for arch in arch_data['architecture'].unique():
                arch_subset = arch_data[arch_data['architecture'] == arch]
                is_pareto = arch_subset['is_pareto'].iloc[0]

                ax.scatter(
                    arch_subset['complexity_score'],
                    arch_subset['avg_overall_score'],
                    c=colors.get(arch, 'gray'),
                    s=150,
                    marker='D' if is_pareto else 'o',
                    edgecolors='black',
                    linewidths=2 if is_pareto else 1,
                    alpha=0.7
                )

                # Label with win rate
                win_rate = arch_subset['won_quality'].iloc[0]
                ax.annotate(
                    f"{arch}\n({win_rate:.0f}%)",
                    (arch_subset['complexity_score'].iloc[0],
                     arch_subset['avg_overall_score'].iloc[0]),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8,
                    fontweight='bold' if is_pareto else 'normal'
                )

            # Draw frontier
            frontier = arch_data[arch_data['is_pareto']].sort_values('complexity_score')
            if len(frontier) > 1:
                ax.plot(
                    frontier['complexity_score'],
                    frontier['avg_overall_score'],
                    'k--',
                    linewidth=2,
                    alpha=0.6
                )

            ax.set_title(f'{complexity.capitalize()} Topics', fontsize=12, fontweight='bold')
            ax.set_xlabel('Complexity Score', fontsize=10)
            if idx == 0:
                ax.set_ylabel('Quality Score', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(7, 9)

        plt.suptitle(
            'Pareto Frontiers by Topic Complexity\n'
            '(Demonstrates Complexity-Dependent Rankings)',
            fontsize=14,
            fontweight='bold'
        )
        plt.tight_layout()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Complexity-stratified Pareto plot saved: {output_path}")

    def generate_markdown_tables(self, output_dir: Path):
        """Generate all markdown tables for presentation."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Table 1: Summary
        summary = self.generate_summary_table()
        self._save_markdown_table(
            summary,
            output_dir / "table1_architecture_summary.md",
            "Architecture Performance Summary"
        )

        # Table 2: Quality dimensions
        dimensions = self._generate_dimension_table()
        self._save_markdown_table(
            dimensions,
            output_dir / "table2_quality_dimensions.md",
            "Quality Dimension Breakdown"
        )

        # Table 3: Efficiency
        efficiency = self._generate_efficiency_table()
        self._save_markdown_table(
            efficiency,
            output_dir / "table3_efficiency.md",
            "Complexity-Quality Efficiency"
        )

        print(f"Markdown tables saved to {output_dir}")

    def _generate_dimension_table(self) -> pd.DataFrame:
        """Generate quality dimension breakdown table."""
        dimensions = [
            'avg_logical_coherence',
            'avg_evidence_strength',
            'avg_relevance',
            'avg_persuasiveness',
            'avg_clarity',
            'avg_counterargument_handling',
            'consistency_score'
        ]

        result = self.quality_df.groupby('architecture')[dimensions + ['avg_overall_score']].mean().round(2)
        return result

    def _generate_efficiency_table(self) -> pd.DataFrame:
        """Generate efficiency metrics table."""
        efficiency = self.quality_df.groupby('architecture').agg({
            'quality_per_1k_tokens': 'mean',
            'quality_per_minute': 'mean',
            'avg_overall_score': 'mean',
            'complexity_score': 'mean'
        }).round(2)

        efficiency['efficiency_score'] = (
            (efficiency['quality_per_1k_tokens'] / efficiency['quality_per_1k_tokens'].max()) * 100
        ).round(1)

        efficiency = efficiency.sort_values('efficiency_score', ascending=False)
        efficiency['rank'] = range(1, len(efficiency) + 1)

        return efficiency

    def _save_markdown_table(self, df: pd.DataFrame, path: Path, title: str):
        """Save DataFrame as markdown table."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(df.to_markdown())
            f.write("\n")


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Generate Pareto frontier analysis and results tables"
    )
    parser.add_argument(
        "--quality-scores",
        type=Path,
        default=Path("analysis/quality_scores.csv"),
        help="Path to quality scores CSV"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/pareto_analysis"),
        help="Output directory for visualizations"
    )

    args = parser.parse_args()

    print("Generating Pareto Frontier Analysis")
    print(f"Quality scores: {args.quality_scores}")
    print(f"Output directory: {args.output_dir}")

    # Initialize analyzer
    analyzer = ParetoAnalyzer(args.quality_scores)

    # Generate visualizations
    print("\nGenerating visualizations...")

    # Overall Pareto frontier
    analyzer.plot_pareto_frontier(
        args.output_dir / "pareto_frontier_overall.png",
        by_complexity=False
    )

    # By complexity
    analyzer.plot_pareto_frontier(
        args.output_dir / "pareto_frontier_by_complexity.png",
        by_complexity=True
    )

    # Generate tables
    print("\nGenerating markdown tables...")
    analyzer.generate_markdown_tables(args.output_dir / "tables")

    print("\n" + "="*60)
    print("Analysis complete!")
    print(f"Outputs saved to: {args.output_dir}")
    print("="*60)


if __name__ == "__main__":
    main()
