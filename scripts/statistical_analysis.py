"""
Statistical Analysis of Debate Simulation Quality Scores

Computes descriptive statistics per (architecture, level) cell and runs
non-parametric statistical tests (Kruskal-Wallis + pairwise Mann-Whitney U).

Usage:
    python scripts/statistical_analysis.py \
        --folders architecture_tests_2/genetic_modification_20260128_231749 \
                  architecture_tests_medium/ai_systems_should_20260123_192237 \
        --output statistical_results.json

Level is inferred from each debate's max_rounds:
    L1 = 1 round (1 member), L2 = 2 rounds (2 members), L3 = 3 rounds (3 members)

Architecture names are parsed from filenames (cot, cot_refl, cot_tools, godsaf_refl, tot).

For each debate file, per architecture, the mean of all argument-level overall_quality
scores is used as a single simulation data point.
"""

import argparse
import json
import logging
import math
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.aggregate_results.parsers import (
    discover_debate_files,
    find_quality_file,
    load_debate_result,
    load_quality_results,
)
from scripts.aggregate_results.extractors import parse_architectures_from_filename

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Display name mapping
ARCH_DISPLAY = {
    "cot": "CoT",
    "cot_refl": "CoT+Reflection",
    "cot_tools": "CoT+Tools",
    "godsaf_refl": "AAF+Reflection",
    "tot": "ToT",
}

LEVEL_DISPLAY = {1: "L1", 2: "L2", 3: "L3"}


def determine_level(debate_data: dict) -> str | None:
    """Infer complexity level from max_rounds in debate data."""
    max_rounds = debate_data.get("max_rounds")
    if max_rounds in (1, 2, 3):
        return LEVEL_DISPLAY[max_rounds]
    logger.warning(f"Unexpected max_rounds={max_rounds}")
    return None


def process_folder(folder_path: Path, scores: dict[str, dict[str, list[float]]]):
    """
    Extract per-simulation quality scores grouped by (architecture, level).

    Args:
        folder_path: Folder with debate results and quality file.
        scores: Dict of {level: {architecture: [quality_scores]}} to populate.
    """
    logger.info(f"Processing folder: {folder_path.name}")

    quality_file = find_quality_file(folder_path)
    if not quality_file:
        return

    quality_data = load_quality_results(quality_file)
    if not quality_data:
        return

    debate_files = discover_debate_files(folder_path)
    # Build lookup: filename -> debate data (for level detection)
    debate_cache: dict[str, dict] = {}
    for df in debate_files:
        data = load_debate_result(df)
        if data:
            debate_cache[df.name] = data

    for result in quality_data.get("results", []):
        source_file = result.get("source_file")
        if not source_file:
            continue

        # Parse architectures from filename
        arch1, arch2, role = parse_architectures_from_filename(source_file)
        if not arch1 or not arch2:
            continue

        # Determine proposition/opposition architecture
        if role == "opposition":
            opp_arch, prop_arch = arch1, arch2
        else:
            prop_arch, opp_arch = arch1, arch2

        # Map team_type to architecture
        type_to_arch = {"proposition": prop_arch, "opposition": opp_arch}

        # Determine level from debate data
        debate_data = debate_cache.get(source_file)
        if not debate_data:
            # Try loading directly
            debate_path = folder_path / source_file
            if debate_path.exists():
                debate_data = load_debate_result(debate_path)
            if not debate_data:
                logger.warning(f"No debate data for {source_file}, skipping")
                continue

        level = determine_level(debate_data)
        if not level:
            continue

        # Collect quality scores per architecture in this debate
        arch_scores: dict[str, list[float]] = defaultdict(list)
        for ev in result.get("argument_evaluations", []):
            team_type = ev.get("team_type")
            overall_q = ev.get("quality_evaluation", {}).get("overall_quality")
            if team_type and overall_q is not None:
                arch = type_to_arch.get(team_type)
                if arch:
                    arch_scores[arch].append(overall_q)

        # Mean quality per architecture per debate = one simulation data point
        for arch, qs in arch_scores.items():
            sim_mean = float(np.mean(qs))
            scores[level][arch].append(sim_mean)

    logger.info(f"  Completed {folder_path.name}")


def compute_descriptive_stats(scores: dict) -> list[dict]:
    """Compute descriptive statistics for each (level, architecture) cell."""
    rows = []
    for level in ["L1", "L2", "L3"]:
        if level not in scores:
            continue
        for arch in sorted(scores[level].keys()):
            data = np.array(scores[level][arch])
            n = len(data)
            if n == 0:
                continue
            mean = float(np.mean(data))
            sd = float(np.std(data, ddof=1)) if n > 1 else 0.0
            ci_margin = 1.96 * sd / math.sqrt(n) if n > 0 else 0.0
            rows.append({
                "level": level,
                "architecture": arch,
                "display_name": ARCH_DISPLAY.get(arch, arch),
                "n": n,
                "mean": round(mean, 4),
                "sd": round(sd, 4),
                "min": round(float(np.min(data)), 4),
                "max": round(float(np.max(data)), 4),
                "ci_lower": round(mean - ci_margin, 4),
                "ci_upper": round(mean + ci_margin, 4),
            })
    return rows


def run_statistical_tests(scores: dict) -> dict:
    """
    Run Kruskal-Wallis and pairwise Mann-Whitney U tests.

    Returns dict with results per level.
    """
    results = {}
    for level in ["L1", "L2", "L3"]:
        if level not in scores:
            continue

        level_data = scores[level]
        architectures = sorted(level_data.keys())

        if len(architectures) < 2:
            continue

        groups = [np.array(level_data[a]) for a in architectures]

        # Kruskal-Wallis H test
        h_stat, kw_p = stats.kruskal(*groups)

        level_result = {
            "kruskal_wallis": {
                "H_statistic": round(float(h_stat), 4),
                "p_value": float(kw_p),
                "significant": bool(kw_p < 0.05),
                "architectures": architectures,
                "sample_sizes": [len(g) for g in groups],
            },
            "pairwise_tests": [],
        }

        # Pairwise Mann-Whitney U if KW is significant
        if kw_p < 0.05:
            pairs = list(combinations(range(len(architectures)), 2))
            n_pairs = len(pairs)
            bonferroni_alpha = 0.05 / n_pairs

            for i, j in pairs:
                u_stat, mw_p = stats.mannwhitneyu(
                    groups[i], groups[j], alternative="two-sided"
                )
                # Effect size r = Z / sqrt(N)
                n_total = len(groups[i]) + len(groups[j])
                # Convert U to Z approximation
                n1, n2 = len(groups[i]), len(groups[j])
                mu_u = n1 * n2 / 2
                sigma_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
                z_score = (u_stat - mu_u) / sigma_u if sigma_u > 0 else 0.0
                effect_r = abs(z_score) / math.sqrt(n_total)

                pair_result = {
                    "arch_1": architectures[i],
                    "arch_1_display": ARCH_DISPLAY.get(architectures[i], architectures[i]),
                    "arch_2": architectures[j],
                    "arch_2_display": ARCH_DISPLAY.get(architectures[j], architectures[j]),
                    "U_statistic": round(float(u_stat), 4),
                    "p_value": float(mw_p),
                    "p_value_bonferroni": float(min(mw_p * n_pairs, 1.0)),
                    "bonferroni_alpha": bonferroni_alpha,
                    "significant_bonferroni": bool(mw_p * n_pairs < 0.05),
                    "Z_score": round(z_score, 4),
                    "effect_size_r": round(effect_r, 4),
                    "n1": n1,
                    "n2": n2,
                }
                level_result["pairwise_tests"].append(pair_result)

        results[level] = level_result

    return results


def print_descriptive_table(rows: list[dict]):
    """Print descriptive statistics as a formatted table."""
    header = f"{'Level':<6} {'Architecture':<18} {'n':>4} {'Mean':>7} {'SD':>7} {'Min':>7} {'Max':>7} {'95% CI Lower':>13} {'95% CI Upper':>13}"
    print("\n" + "=" * len(header))
    print("DESCRIPTIVE STATISTICS")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    current_level = None
    for r in rows:
        if r["level"] != current_level:
            if current_level is not None:
                print("-" * len(header))
            current_level = r["level"]
        print(
            f"{r['level']:<6} {r['display_name']:<18} {r['n']:>4} "
            f"{r['mean']:>7.4f} {r['sd']:>7.4f} {r['min']:>7.4f} {r['max']:>7.4f} "
            f"{r['ci_lower']:>13.4f} {r['ci_upper']:>13.4f}"
        )
    print("=" * len(header))


def print_statistical_tests(test_results: dict):
    """Print statistical test results."""
    print("\n" + "=" * 90)
    print("STATISTICAL TESTS")
    print("=" * 90)

    for level in ["L1", "L2", "L3"]:
        if level not in test_results:
            continue

        lr = test_results[level]
        kw = lr["kruskal_wallis"]

        print(f"\n--- {level}: Kruskal-Wallis H Test ---")
        print(f"  H = {kw['H_statistic']:.4f}, p = {kw['p_value']:.6f}  "
              f"{'*** SIGNIFICANT' if kw['significant'] else 'not significant'}")
        print(f"  Architectures: {', '.join(kw['architectures'])}")
        print(f"  Sample sizes:  {kw['sample_sizes']}")

        if lr["pairwise_tests"]:
            print(f"\n  Pairwise Mann-Whitney U (Bonferroni-corrected, alpha = "
                  f"{lr['pairwise_tests'][0]['bonferroni_alpha']:.4f}):")
            print(f"  {'Pair':<40} {'U':>10} {'p':>12} {'p_adj':>12} {'Sig':>5} {'r':>7}")
            print(f"  {'-'*86}")
            for pt in lr["pairwise_tests"]:
                pair_name = f"{pt['arch_1_display']} vs {pt['arch_2_display']}"
                sig = "***" if pt["significant_bonferroni"] else ""
                print(
                    f"  {pair_name:<40} {pt['U_statistic']:>10.1f} "
                    f"{pt['p_value']:>12.6f} {pt['p_value_bonferroni']:>12.6f} "
                    f"{sig:>5} {pt['effect_size_r']:>7.4f}"
                )


def main():
    parser = argparse.ArgumentParser(
        description="Statistical analysis of debate quality scores by architecture and level",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/statistical_analysis.py \\
      --folders architecture_tests_2/genetic_modification_20260128_231749 \\
                architecture_tests_medium/ai_systems_should_20260123_192237 \\
      --output statistical_results.json
        """,
    )
    parser.add_argument(
        "--folders", nargs="+", type=Path, required=True,
        help="Paths to folders containing debate result files",
    )
    parser.add_argument(
        "--output", type=Path, required=True,
        help="Output JSON file path",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose debug logging",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    folders = [f.resolve() for f in args.folders]
    for folder in folders:
        if not folder.exists():
            logger.error(f"Folder not found: {folder}")
            sys.exit(1)

    # scores[level][architecture] = [list of simulation mean quality scores]
    scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for folder in folders:
        try:
            process_folder(folder, scores)
        except Exception as e:
            logger.error(f"Error processing {folder}: {e}")
            import traceback
            traceback.print_exc()

    # Summary of collected data
    print("\nData collection summary:")
    for level in ["L1", "L2", "L3"]:
        if level in scores:
            for arch in sorted(scores[level].keys()):
                n = len(scores[level][arch])
                print(f"  {level} / {ARCH_DISPLAY.get(arch, arch)}: {n} simulations")

    # Descriptive statistics
    desc_rows = compute_descriptive_stats(scores)
    print_descriptive_table(desc_rows)

    # Statistical tests
    test_results = run_statistical_tests(scores)
    print_statistical_tests(test_results)

    # Save JSON output
    output = {
        "descriptive_statistics": desc_rows,
        "statistical_tests": test_results,
        "raw_counts": {
            level: {arch: len(vals) for arch, vals in archs.items()}
            for level, archs in scores.items()
        },
    }

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            return super().default(obj)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)

    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
