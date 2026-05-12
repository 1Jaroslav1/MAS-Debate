"""
Batch Argument Quality Evaluation Script

This script evaluates argument quality for completed debate simulations
and generates quality scores that can be used for analysis.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from evaluation.argument_quality_evaluator import (
    ArgumentQualityEvaluator,
    SimulationQualityReport
)
from models.llm_model import LLMModel


def load_simulation_results(results_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all simulation result files from directory.

    Args:
        results_dir: Directory containing result JSON files

    Returns:
        List of simulation result dictionaries
    """
    results = []
    for json_file in results_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results.append(data)
                print(f"Loaded: {json_file.name}")
        except Exception as e:
            print(f"Error loading {json_file.name}: {e}")

    return results


def evaluate_batch(
    simulation_results: List[Dict[str, Any]],
    output_dir: Path,
    model_name: str = "gpt-4",
    temperature: float = 0.3
) -> List[SimulationQualityReport]:
    """
    Evaluate argument quality for a batch of simulations.

    Args:
        simulation_results: List of simulation result dictionaries
        output_dir: Directory to save evaluation reports
        model_name: LLM model to use for evaluation
        temperature: Temperature for LLM

    Returns:
        List of quality reports
    """
    # Initialize evaluator
    model = LLMModel(model_name=model_name, temperature=temperature)
    evaluator = ArgumentQualityEvaluator(model=model, temperature=temperature)

    reports = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, sim_result in enumerate(simulation_results, 1):
        config_id = sim_result.get("config_id", f"simulation_{i}")
        print(f"\n{'='*60}")
        print(f"Evaluating {i}/{len(simulation_results)}: {config_id}")
        print(f"{'='*60}")

        try:
            # Evaluate simulation
            report = evaluator.evaluate_simulation(sim_result)
            reports.append(report)

            # Save individual report
            report_path = output_dir / f"{config_id}_quality_report.json"
            evaluator.save_report(report, report_path)

            print(f"✓ Evaluation complete")
            print(f"  Winning team (quality): {report.winning_team_quality}")
            print(f"  Quality margin: {report.quality_margin:.2f}")
            print(f"  Report saved: {report_path}")

        except Exception as e:
            print(f"✗ Error evaluating {config_id}: {e}")
            import traceback
            traceback.print_exc()

    return reports


def generate_summary_report(
    reports: List[SimulationQualityReport],
    output_path: Path
):
    """
    Generate summary report across all evaluations.

    Args:
        reports: List of quality reports
        output_path: Path to save summary JSON
    """
    summary = {
        "total_simulations": len(reports),
        "evaluation_timestamp": datetime.now().isoformat(),
        "aggregate_statistics": {},
        "simulations": []
    }

    # Collect aggregate statistics
    all_scores = []
    team_performance = {}

    for report in reports:
        sim_summary = {
            "config_id": report.config_id,
            "topic": report.topic,
            "winning_team_quality": report.winning_team_quality,
            "quality_margin": report.quality_margin,
            "team_scores": {}
        }

        for team_name, team_score in report.team_scores.items():
            sim_summary["team_scores"][team_name] = {
                "avg_overall_score": team_score.avg_overall_score,
                "avg_logical_coherence": team_score.avg_logical_coherence,
                "avg_evidence_strength": team_score.avg_evidence_strength,
                "avg_relevance": team_score.avg_relevance,
                "avg_persuasiveness": team_score.avg_persuasiveness,
                "avg_clarity": team_score.avg_clarity,
                "avg_counterargument_handling": team_score.avg_counterargument_handling,
                "consistency_score": team_score.consistency_score
            }

            all_scores.append(team_score.avg_overall_score)

            # Track team type performance
            team_type = "proposition" if "pro" in team_name else "opposition"
            if team_type not in team_performance:
                team_performance[team_type] = []
            team_performance[team_type].append(team_score.avg_overall_score)

        summary["simulations"].append(sim_summary)

    # Calculate aggregate statistics
    if all_scores:
        summary["aggregate_statistics"] = {
            "mean_quality_score": sum(all_scores) / len(all_scores),
            "min_quality_score": min(all_scores),
            "max_quality_score": max(all_scores),
            "std_dev": (
                sum((x - sum(all_scores) / len(all_scores)) ** 2 for x in all_scores) / len(all_scores)
            ) ** 0.5,
            "team_type_performance": {
                team_type: {
                    "mean": sum(scores) / len(scores) if scores else 0,
                    "count": len(scores)
                }
                for team_type, scores in team_performance.items()
            }
        }

    # Save summary
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Summary report saved: {output_path}")
    print(f"{'='*60}")
    print(f"Total simulations evaluated: {summary['total_simulations']}")
    print(f"Mean quality score: {summary['aggregate_statistics'].get('mean_quality_score', 0):.2f}/10")
    print(f"Quality score range: {summary['aggregate_statistics'].get('min_quality_score', 0):.2f} - {summary['aggregate_statistics'].get('max_quality_score', 0):.2f}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Evaluate argument quality for debate simulations"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Directory containing simulation result JSON files"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("evaluation_results/quality_reports"),
        help="Directory to save quality evaluation reports"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="LLM model to use for evaluation"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="Temperature for LLM (lower = more consistent)"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.json",
        help="File pattern to match (e.g., 'ai_systems*.json')"
    )

    args = parser.parse_args()

    print("Argument Quality Evaluation")
    print(f"Results directory: {args.results_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"Model: {args.model}")
    print(f"Temperature: {args.temperature}")
    print(f"Pattern: {args.pattern}")

    # Load simulation results
    print(f"\nLoading simulation results from {args.results_dir}...")
    all_results = []
    for json_file in args.results_dir.glob(args.pattern):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.append(data)
                print(f"  ✓ {json_file.name}")
        except Exception as e:
            print(f"  ✗ {json_file.name}: {e}")

    if not all_results:
        print("\nNo simulation results found!")
        return

    print(f"\nFound {len(all_results)} simulation(s) to evaluate")

    # Evaluate batch
    reports = evaluate_batch(
        simulation_results=all_results,
        output_dir=args.output_dir,
        model_name=args.model,
        temperature=args.temperature
    )

    # Generate summary
    if reports:
        summary_path = args.output_dir / "quality_evaluation_summary.json"
        generate_summary_report(reports, summary_path)

        print(f"\n{'='*60}")
        print("Evaluation complete!")
        print(f"Individual reports: {args.output_dir}")
        print(f"Summary report: {summary_path}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
