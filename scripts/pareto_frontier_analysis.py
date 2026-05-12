"""
Pareto Frontier Analysis for Debate Architectures

Analyzes debate architectures within each complexity level (small, medium, large).
Pareto optimality is computed SEPARATELY for each complexity level, since
architectures at different complexity levels are solving different problems
and cannot be directly compared.

A solution is Pareto-optimal if no other solution (within the same complexity)
is better in all objectives.
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving plots
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple
import warnings

warnings.filterwarnings('ignore')

# Architecture display names mapping
ARCH_DISPLAY_NAMES = {
    'cot': 'CoT',
    'cot_refl': 'CoT with Reflexion',
    'cot_tools': 'CoT with tools',
    'godsaf_refl': 'AAF with Reflexion',
    'tot': 'ToT'
}


def get_arch_display_name(arch_key: str) -> str:
    """Get display name for architecture."""
    return ARCH_DISPLAY_NAMES.get(arch_key, arch_key)


@dataclass
class ArchitecturePoint:
    """Represents a single architecture configuration at a complexity level."""
    name: str
    complexity: str
    quality: float
    tokens: float
    time: float
    win_rate: float

    def to_array(self, objectives: List[str]) -> np.ndarray:
        """Convert to numpy array for Pareto computation."""
        mapping = {
            'quality': self.quality,
            'tokens': self.tokens,
            'time': self.time,
            'win_rate': self.win_rate
        }
        return np.array([mapping[obj] for obj in objectives])


def load_data(file_paths: Dict[str, str]) -> List[ArchitecturePoint]:
    """Load architecture data from JSON files."""
    points = []

    for complexity, path in file_paths.items():
        with open(path, 'r') as f:
            data = json.load(f)

        for arch_name, metrics in data['architecture_metrics'].items():
            point = ArchitecturePoint(
                name=arch_name,
                complexity=complexity,
                quality=metrics['quality']['mean'],
                tokens=metrics['tokens']['mean'],
                time=metrics['time_seconds']['mean'],
                win_rate=metrics.get('win_rate', 50.0)
            )
            points.append(point)

    return points


def is_dominated(point: np.ndarray, other_points: np.ndarray,
                 maximize: List[bool]) -> bool:
    """
    Check if a point is dominated by any other point.

    A point is dominated if there exists another point that is:
    - At least as good in all objectives
    - Strictly better in at least one objective
    """
    for other in other_points:
        if np.array_equal(point, other):
            continue

        # Check if 'other' dominates 'point'
        at_least_as_good = True
        strictly_better = False

        for i, maximize_obj in enumerate(maximize):
            if maximize_obj:
                # For maximization: higher is better
                if other[i] < point[i]:
                    at_least_as_good = False
                    break
                if other[i] > point[i]:
                    strictly_better = True
            else:
                # For minimization: lower is better
                if other[i] > point[i]:
                    at_least_as_good = False
                    break
                if other[i] < point[i]:
                    strictly_better = True

        if at_least_as_good and strictly_better:
            return True

    return False


def compute_pareto_frontier(points: List[ArchitecturePoint],
                           objectives: List[str],
                           maximize: List[bool]) -> List[Tuple[ArchitecturePoint, bool]]:
    """
    Compute Pareto frontier for given objectives.

    Returns list of (point, is_on_frontier) tuples.
    """
    if not points:
        return []

    # Convert to numpy arrays
    arrays = np.array([p.to_array(objectives) for p in points])

    results = []
    for i, point in enumerate(points):
        dominated = is_dominated(arrays[i], arrays, maximize)
        results.append((point, not dominated))

    return results


def compute_pareto_by_complexity(points: List[ArchitecturePoint],
                                  objectives: List[str],
                                  maximize: List[bool]) -> Dict[str, List[Tuple[ArchitecturePoint, bool]]]:
    """
    Compute Pareto frontier SEPARATELY for each complexity level.

    This is the correct approach since architectures at different complexity
    levels are solving different problems and cannot be directly compared.

    Returns dict mapping complexity -> list of (point, is_on_frontier) tuples.
    """
    complexities = set(p.complexity for p in points)
    results = {}

    for complexity in complexities:
        # Filter points for this complexity level only
        complexity_points = [p for p in points if p.complexity == complexity]
        # Compute Pareto frontier within this complexity level
        results[complexity] = compute_pareto_frontier(complexity_points, objectives, maximize)

    return results


def plot_2d_pareto_by_complexity(points: List[ArchitecturePoint],
                                  x_obj: str, y_obj: str,
                                  x_maximize: bool, y_maximize: bool,
                                  title: str, save_path: str = None,
                                  x_log: bool = False):
    """
    Plot 2D Pareto frontier with separate frontiers per complexity level.

    Each complexity level gets its own Pareto frontier (shown as dashed line).
    """

    # Define colors and markers for architectures
    arch_colors = {
        'cot': '#1f77b4',
        'cot_refl': '#ff7f0e',
        'cot_tools': '#2ca02c',
        'godsaf_refl': '#d62728',
        'tot': '#9467bd'
    }

    complexity_markers = {
        'small': 'o',
        'medium': 's',
        'large': '^'
    }

    complexity_sizes = {
        'small': 150,
        'medium': 200,
        'large': 250
    }

    complexity_line_colors = {
        'small': '#2ecc71',
        'medium': '#f39c12',
        'large': '#e74c3c'
    }

    # Compute Pareto frontier per complexity level
    results_by_complexity = compute_pareto_by_complexity(
        points, [x_obj, y_obj], [x_maximize, y_maximize]
    )

    fig, ax = plt.subplots(figsize=(12, 6.4))

    # Get attribute mapping
    obj_mapping = {
        'quality': lambda p: p.quality,
        'tokens': lambda p: p.tokens,
        'time': lambda p: p.time,
        'win_rate': lambda p: p.win_rate
    }

    # Plot all points and connect frontier per complexity
    for complexity in ['small', 'medium', 'large']:
        if complexity not in results_by_complexity:
            continue

        results = results_by_complexity[complexity]
        frontier_points = []

        for point, is_frontier in results:
            x = obj_mapping[x_obj](point)
            y = obj_mapping[y_obj](point)

            color = arch_colors.get(point.name, 'gray')
            marker = complexity_markers.get(point.complexity, 'o')
            size = complexity_sizes.get(point.complexity, 100)

            # Frontier points get bold edge
            edge_color = 'black' if is_frontier else color
            edge_width = 3 if is_frontier else 1

            ax.scatter(x, y, c=color, marker=marker, s=size,
                      edgecolors=edge_color, linewidths=edge_width,
                      alpha=0.8, zorder=5 if is_frontier else 3)

            if is_frontier:
                frontier_points.append((x, y))

        # Connect Pareto frontier points for this complexity
        if frontier_points:
            frontier_points.sort(key=lambda p: p[0])
            xs, ys = zip(*frontier_points)
            line_color = complexity_line_colors.get(complexity, 'gray')
            ax.plot(xs, ys, '--', color=line_color, alpha=0.7, linewidth=2,
                   label=f'{complexity.capitalize()} Frontier')

    # Apply logarithmic scale for x-axis if requested
    if x_log:
        ax.set_xscale('log')

    # Labels
    obj_labels = {
        'quality': 'Quality',
        'tokens': 'Tokens Used' if x_log and x_obj == 'tokens' else 'Tokens Used',
        'time': 'Time in seconds' if x_log and x_obj == 'time' else 'Time in seconds',
        'win_rate': 'Win Rate % (higher is better)'
    }

    ax.set_xlabel(obj_labels[x_obj], fontsize=14)
    ax.set_ylabel(obj_labels[y_obj], fontsize=14)
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.tick_params(axis='both', labelsize=12)

    # Create legends
    arch_handles = [Patch(facecolor=c, label=get_arch_display_name(n))
                    for n, c in arch_colors.items()]

    complexity_handles = [plt.Line2D([0], [0], marker=m, color='gray',
                                     linestyle='', markersize=12,
                                     label=n.capitalize())
                         for n, m in complexity_markers.items()]

    frontier_handle = plt.Line2D([0], [0], marker='o', color='white',
                                 markeredgecolor='black', markeredgewidth=3,
                                 markersize=12, linestyle='',
                                 label='Pareto Optimal')

    # Frontier line handles
    frontier_line_handles = [plt.Line2D([0], [0], linestyle='--', color=c,
                                        linewidth=2, label=f'{n.capitalize()} Frontier')
                            for n, c in complexity_line_colors.items()]

    # Position legends
    legend1 = ax.legend(handles=arch_handles, title='Architecture',
                       loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=11, title_fontsize=12)
    legend2 = ax.legend(handles=complexity_handles + [frontier_handle] + frontier_line_handles,
                       title='Complexity & Frontiers',
                       loc='upper left', bbox_to_anchor=(1.02, 0.55), fontsize=11, title_fontsize=12)
    ax.add_artist(legend1)

    ax.grid(True, alpha=0.3, which='both')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")

    plt.close(fig)


def plot_combined_pareto(points: List[ArchitecturePoint],
                         save_path: str = None):
    """
    Plot combined Pareto frontiers: Quality vs Tokens and Quality vs Time
    side by side with a single shared legend.
    """

    # Define colors and markers for architectures
    arch_colors = {
        'cot': '#1f77b4',
        'cot_refl': '#ff7f0e',
        'cot_tools': '#2ca02c',
        'godsaf_refl': '#d62728',
        'tot': '#9467bd'
    }

    complexity_markers = {
        'small': 'o',
        'medium': 's',
        'large': '^'
    }

    complexity_sizes = {
        'small': 150,
        'medium': 200,
        'large': 250
    }

    complexity_line_colors = {
        'small': '#2ecc71',
        'medium': '#f39c12',
        'large': '#e74c3c'
    }

    # Create figure with 1 row, 2 columns
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    obj_mapping = {
        'quality': lambda p: p.quality,
        'tokens': lambda p: p.tokens,
        'time': lambda p: p.time,
    }

    # Define the two plots
    plot_configs = [
        {'x_obj': 'tokens', 'y_obj': 'quality', 'x_max': False, 'y_max': True,
         'title': 'Quality vs Tokens', 'xlabel': 'Tokens Used'},
        {'x_obj': 'time', 'y_obj': 'quality', 'x_max': False, 'y_max': True,
         'title': 'Quality vs Time', 'xlabel': 'Time (seconds)'},
    ]

    for ax, config in zip(axes, plot_configs):
        x_obj = config['x_obj']
        y_obj = config['y_obj']

        # Compute Pareto frontier per complexity level
        results_by_complexity = compute_pareto_by_complexity(
            points, [x_obj, y_obj], [config['x_max'], config['y_max']]
        )

        # Plot all points and connect frontier per complexity
        for complexity in ['small', 'medium', 'large']:
            if complexity not in results_by_complexity:
                continue

            results = results_by_complexity[complexity]
            frontier_points = []

            for point, is_frontier in results:
                x = obj_mapping[x_obj](point)
                y = obj_mapping[y_obj](point)

                color = arch_colors.get(point.name, 'gray')
                marker = complexity_markers.get(point.complexity, 'o')
                size = complexity_sizes.get(point.complexity, 100)

                # Frontier points get bold edge
                edge_color = 'black' if is_frontier else color
                edge_width = 3 if is_frontier else 1

                ax.scatter(x, y, c=color, marker=marker, s=size,
                          edgecolors=edge_color, linewidths=edge_width,
                          alpha=0.8, zorder=5 if is_frontier else 3)

                if is_frontier:
                    frontier_points.append((x, y))

            # Connect Pareto frontier points for this complexity
            if frontier_points:
                frontier_points.sort(key=lambda p: p[0])
                xs, ys = zip(*frontier_points)
                line_color = complexity_line_colors.get(complexity, 'gray')
                ax.plot(xs, ys, '--', color=line_color, alpha=0.7, linewidth=2)

        # Apply logarithmic scale for x-axis
        ax.set_xscale('log')
        ax.set_xlabel(config['xlabel'], fontsize=13)
        ax.set_ylabel(config['y_obj'].capitalize(), fontsize=13)
        ax.set_title(config['title'], fontsize=14, fontweight='bold')
        ax.tick_params(axis='both', labelsize=11)
        ax.grid(True, alpha=0.3, which='both')

    # Create shared legend handles
    arch_handles = [Patch(facecolor=c, label=get_arch_display_name(n))
                    for n, c in arch_colors.items()]

    complexity_handles = [plt.Line2D([0], [0], marker=m, color='gray',
                                     linestyle='', markersize=10,
                                     label=n.capitalize())
                         for n, m in complexity_markers.items()]

    frontier_handle = plt.Line2D([0], [0], marker='o', color='white',
                                 markeredgecolor='black', markeredgewidth=3,
                                 markersize=10, linestyle='',
                                 label='Pareto Optimal')

    frontier_line_handles = [plt.Line2D([0], [0], linestyle='--', color=c,
                                        linewidth=2, label=f'{n.capitalize()} Frontier')
                            for n, c in complexity_line_colors.items()]

    # Combine all handles
    all_handles = arch_handles + [plt.Line2D([0], [0], color='none')] + \
                  complexity_handles + [frontier_handle] + frontier_line_handles

    all_labels = [get_arch_display_name(n) for n in arch_colors.keys()] + [''] + \
                 [n.capitalize() for n in complexity_markers.keys()] + \
                 ['Pareto Optimal'] + [f'{n.capitalize()} Frontier' for n in complexity_line_colors.keys()]

    # Add single legend to the right of the figure
    fig.legend(all_handles, all_labels,
               loc='center right',
               bbox_to_anchor=(1.02, 0.5),
               fontsize=10,
               frameon=True,
               title='Legend',
               title_fontsize=11,
               borderaxespad=0.4,
               labelspacing=0.4
               )

    plt.tight_layout()
    plt.subplots_adjust(right=0.88)  # Make room for legend

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")

    plt.close(fig)


def plot_pareto_per_complexity(points: List[ArchitecturePoint],
                                output_dir: Path):
    """
    Generate separate Pareto frontier plots for each complexity level.
    """

    arch_colors = {
        'cot': '#1f77b4',
        'cot_refl': '#ff7f0e',
        'cot_tools': '#2ca02c',
        'godsaf_refl': '#d62728',
        'tot': '#9467bd'
    }

    for complexity in ['small', 'medium', 'large']:
        complexity_points = [p for p in points if p.complexity == complexity]
        if not complexity_points:
            continue

        # Compute Pareto frontier for this complexity
        results = compute_pareto_frontier(
            complexity_points,
            ['quality', 'tokens', 'time'],
            [True, False, False]
        )

        # Create 2x2 subplot for this complexity
        fig, axes = plt.subplots(2, 2, figsize=(14, 9.6))

        objectives_pairs = [
            ('tokens', 'quality', False, True, 'Quality vs Tokens'),
            ('time', 'quality', False, True, 'Quality vs Time'),
            ('tokens', 'time', False, False, 'Tokens vs Time'),
        ]

        obj_mapping = {
            'quality': lambda p: p.quality,
            'tokens': lambda p: p.tokens,
            'time': lambda p: p.time,
        }

        for ax, (x_obj, y_obj, x_max, y_max, subtitle) in zip(axes.flatten()[:3], objectives_pairs):
            # Compute 2D Pareto for this pair
            results_2d = compute_pareto_frontier(
                complexity_points, [x_obj, y_obj], [x_max, y_max]
            )

            frontier_points = []

            for point, is_frontier in results_2d:
                x = obj_mapping[x_obj](point)
                y = obj_mapping[y_obj](point)

                color = arch_colors.get(point.name, 'gray')
                edge_color = 'black' if is_frontier else color
                edge_width = 3 if is_frontier else 1

                ax.scatter(x, y, c=color, s=200,
                          edgecolors=edge_color, linewidths=edge_width,
                          alpha=0.8, zorder=5 if is_frontier else 3)

                # Add architecture label
                display_name = get_arch_display_name(point.name)
                ax.annotate(display_name, (x, y),
                           textcoords="offset points", xytext=(0, 12),
                           ha='center', fontsize=10, fontweight='bold')

                if is_frontier:
                    frontier_points.append((x, y))

            # Connect frontier
            if frontier_points:
                frontier_points.sort(key=lambda p: p[0])
                xs, ys = zip(*frontier_points)
                ax.plot(xs, ys, 'k--', alpha=0.5, linewidth=1.5)

            ax.set_xscale('log')
            ax.set_xlabel(x_obj.capitalize(), fontsize=13)
            ax.set_ylabel(y_obj.capitalize(), fontsize=13)
            ax.set_title(subtitle, fontsize=14, fontweight='bold')
            ax.tick_params(axis='both', labelsize=11)
            ax.grid(True, alpha=0.3, which='both')

        # Summary table in 4th subplot
        ax = axes.flatten()[3]
        ax.axis('off')

        # Create summary table
        table_data = []
        headers = ['Architecture', 'Quality', 'Tokens', 'Time(s)', 'Pareto']

        for point, is_frontier in sorted(results, key=lambda x: -x[0].quality):
            pareto_mark = '*' if is_frontier else ''
            table_data.append([
                get_arch_display_name(point.name),
                f'{point.quality:.3f}',
                f'{point.tokens:,.0f}',
                f'{point.time:.1f}',
                pareto_mark
            ])

        table = ax.table(cellText=table_data, colLabels=headers,
                        loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.3, 1.8)

        # Color Pareto optimal rows
        for i, (point, is_frontier) in enumerate(sorted(results, key=lambda x: -x[0].quality)):
            if is_frontier:
                for j in range(5):
                    table[(i+1, j)].set_facecolor('#d5f5e3')

        ax.set_title('Summary (* = Pareto Optimal)', fontsize=14, fontweight='bold', pad=20)

        plt.suptitle(f'Pareto Analysis: {complexity.upper()} Complexity',
                     fontsize=18, fontweight='bold', y=1.02)
        plt.tight_layout()

        save_path = output_dir / f'pareto_{complexity}.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
        plt.close(fig)


def plot_complexity_comparison(points: List[ArchitecturePoint],
                               save_path: str = None):
    """Plot how architectures scale across complexity levels."""

    arch_colors = {
        'cot': '#1f77b4',
        'cot_refl': '#ff7f0e',
        'cot_tools': '#2ca02c',
        'godsaf_refl': '#d62728',
        'tot': '#9467bd'
    }

    complexities = ['small', 'medium', 'large']
    architectures = list(arch_colors.keys())

    fig, axes = plt.subplots(2, 2, figsize=(14, 9.6))

    metrics = [
        ('quality', 'Quality Score', True),
        ('tokens', 'Tokens Used', False),
        ('time', 'Time (seconds)', False),
        ('win_rate', 'Win Rate (%)', True)
    ]

    for ax, (metric, label, higher_better) in zip(axes.flatten(), metrics):
        for arch in architectures:
            values = []
            for complexity in complexities:
                point = next((p for p in points
                             if p.name == arch and p.complexity == complexity), None)
                if point:
                    val = getattr(point, metric)
                    values.append(val)
                else:
                    values.append(np.nan)

            ax.plot(complexities, values, 'o-', color=arch_colors[arch],
                   label=get_arch_display_name(arch), linewidth=2.5, markersize=10)

        ax.set_xlabel('Complexity Level', fontsize=13)
        ax.set_ylabel(label, fontsize=13)
        ax.set_title(f'{label} vs Complexity', fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=11)
        ax.tick_params(axis='both', labelsize=11)
        ax.grid(True, alpha=0.3)

        # Use log scale for tokens and time
        if metric in ['tokens', 'time']:
            ax.set_yscale('log')

    plt.suptitle('Architecture Scaling Across Complexity Levels',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")

    plt.close(fig)


def compute_efficiency_metrics(points: List[ArchitecturePoint]) -> Dict:
    """Compute efficiency metrics for each architecture."""

    efficiency = {}

    for point in points:
        key = (point.name, point.complexity)
        efficiency[key] = {
            'quality_per_1k_tokens': point.quality / (point.tokens / 1000),
            'quality_per_minute': point.quality / (point.time / 60),
            'tokens_per_second': point.tokens / point.time,
            'efficiency_score': point.quality / np.log10(point.tokens * point.time + 1)
        }

    return efficiency


def print_pareto_summary(points: List[ArchitecturePoint]):
    """Print summary of Pareto analysis per complexity level."""

    print("\n" + "="*80)
    print("PARETO FRONTIER ANALYSIS SUMMARY")
    print("(Computed SEPARATELY for each complexity level)")
    print("="*80)

    for complexity in ['small', 'medium', 'large']:
        complexity_points = [p for p in points if p.complexity == complexity]
        if not complexity_points:
            continue

        print(f"\n{'='*40}")
        print(f"  {complexity.upper()} COMPLEXITY")
        print(f"{'='*40}")

        # 3D Pareto frontier for this complexity
        results = compute_pareto_frontier(
            complexity_points,
            ['quality', 'tokens', 'time'],
            [True, False, False]
        )

        print("\n  [PARETO OPTIMAL] (quality UP, tokens DOWN, time DOWN)")
        print("  " + "-" * 55)

        pareto_count = 0
        for point, is_frontier in sorted(results, key=lambda x: -x[0].quality):
            status = ">>" if is_frontier else "  "
            pareto_count += 1 if is_frontier else 0
            display_name = get_arch_display_name(point.name)
            print(f"  {status} {display_name:20} - "
                  f"Q: {point.quality:.3f}, T: {point.tokens:>10,.0f}, "
                  f"Time: {point.time:>7.1f}s")

        print(f"\n  Pareto optimal: {pareto_count} / {len(complexity_points)} architectures")

    # Efficiency metrics per complexity
    print("\n" + "="*80)
    print("EFFICIENCY METRICS (per complexity level)")
    print("="*80)

    efficiency = compute_efficiency_metrics(points)

    for complexity in ['small', 'medium', 'large']:
        complexity_efficiency = {k: v for k, v in efficiency.items() if k[1] == complexity}
        if not complexity_efficiency:
            continue

        print(f"\n  [{complexity.upper()}]")

        best_qpt = max(complexity_efficiency.items(), key=lambda x: x[1]['quality_per_1k_tokens'])
        print(f"    Best Quality/1K Tokens: {get_arch_display_name(best_qpt[0][0]):20} - {best_qpt[1]['quality_per_1k_tokens']:.4f}")

        best_qpm = max(complexity_efficiency.items(), key=lambda x: x[1]['quality_per_minute'])
        print(f"    Best Quality/Minute:    {get_arch_display_name(best_qpm[0][0]):20} - {best_qpm[1]['quality_per_minute']:.4f}")

    print("\n" + "="*80)


def generate_latex_table(points: List[ArchitecturePoint]) -> str:
    """Generate LaTeX table for Pareto analysis per complexity."""

    latex = r"""
\begin{table}[h]
\centering
\caption{Debate Architecture Performance with Pareto Optimality per Complexity Level}
\begin{tabular}{llrrrl}
\toprule
\textbf{Architecture} & \textbf{Complexity} & \textbf{Quality} & \textbf{Tokens} & \textbf{Time (s)} & \textbf{Pareto} \\
\midrule
"""

    for complexity in ['small', 'medium', 'large']:
        complexity_points = [p for p in points if p.complexity == complexity]
        if not complexity_points:
            continue

        results = compute_pareto_frontier(
            complexity_points,
            ['quality', 'tokens', 'time'],
            [True, False, False]
        )

        for point, is_frontier in sorted(results, key=lambda x: x[0].name):
            pareto_marker = r"$\star$" if is_frontier else ""
            display_name = get_arch_display_name(point.name)
            latex += f"{display_name} & {point.complexity} & "
            latex += f"{point.quality:.3f} & {point.tokens:,.0f} & {point.time:.1f} & {pareto_marker} \\\\\n"

        latex += r"\midrule" + "\n"

    # Remove last midrule
    latex = latex.rsplit(r"\midrule", 1)[0]

    latex += r"""
\bottomrule
\end{tabular}
\label{tab:pareto}
\end{table}
"""
    return latex


def main():
    """Main function to run Pareto frontier analysis."""

    # File paths
    base_path = Path(__file__).parent
    file_paths = {
        'small': base_path / 'small.json',
        'medium': base_path / 'medium.json',
        'large': base_path / 'large.json'
    }

    # Check files exist
    for name, path in file_paths.items():
        if not path.exists():
            print(f"Warning: {path} not found")
            return

    print("Loading data...")
    points = load_data(file_paths)
    print(f"Loaded {len(points)} architecture configurations")

    # Print summary
    print_pareto_summary(points)

    # Output directory
    output_dir = base_path / 'pareto_analysis'
    output_dir.mkdir(exist_ok=True)

    # Generate plots
    print("\nGenerating visualizations...")

    # Separate Pareto plot for each complexity level
    plot_pareto_per_complexity(points, output_dir)

    # Combined plot with two subplots and shared legend
    plot_combined_pareto(
        points,
        save_path=str(output_dir / 'pareto_combined.png')
    )

    # Combined 2D Pareto with separate frontiers per complexity
    plot_2d_pareto_by_complexity(
        points,
        x_obj='tokens', y_obj='quality',
        x_maximize=False, y_maximize=True,
        title='Pareto Frontiers: Quality vs Tokens',
        save_path=str(output_dir / 'pareto_quality_vs_tokens.png'),
        x_log=True
    )

    plot_2d_pareto_by_complexity(
        points,
        x_obj='time', y_obj='quality',
        x_maximize=False, y_maximize=True,
        title='Pareto Frontiers: Quality vs Time',
        save_path=str(output_dir / 'pareto_quality_vs_time.png'),
        x_log=True
    )

    plot_2d_pareto_by_complexity(
        points,
        x_obj='tokens', y_obj='time',
        x_maximize=False, y_maximize=False,
        title='Pareto Frontiers: Tokens vs Time (per complexity)',
        save_path=str(output_dir / 'pareto_tokens_vs_time.png'),
        x_log=True
    )

    # Complexity comparison
    plot_complexity_comparison(
        points,
        save_path=str(output_dir / 'complexity_scaling.png')
    )

    # Generate LaTeX table
    latex_table = generate_latex_table(points)
    latex_path = output_dir / 'pareto_table.tex'
    with open(latex_path, 'w') as f:
        f.write(latex_table)
    print(f"Saved LaTeX table: {latex_path}")

    print("\n[DONE] Analysis complete! Results saved to:", output_dir)


if __name__ == '__main__':
    main()
