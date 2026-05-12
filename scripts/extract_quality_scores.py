"""
Extract Quality Scores for Analysis

This script extracts team quality scores from evaluation reports
and formats them for statistical analysis (CSV, Excel, etc.).
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import csv
from datetime import datetime


def load_quality_reports(reports_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all quality report JSON files.

    Args:
        reports_dir: Directory containing quality report files

    Returns:
        List of quality report dictionaries
    """
    reports = []
    for json_file in reports_dir.glob("*_quality_report.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                reports.append(data)
                print(f"Loaded: {json_file.name}")
        except Exception as e:
            print(f"Error loading {json_file.name}: {e}")

    return reports


def extract_team_scores(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract team scores from quality reports.

    Args:
        reports: List of quality report dictionaries

    Returns:
        List of flattened team score records
    """
    records = []

    for report in reports:
        config_id = report.get("config_id", "")
        topic = report.get("topic", "")

        for team_name, team_data in report.get("team_scores", {}).items():
            # Determine team type
            team_type = "proposition" if "pro" in team_name.lower() else "opposition"

            # Check if this team won on quality
            won_quality = (team_name == report.get("winning_team_quality"))

            record = {
                "config_id": config_id,
                "topic": topic,
                "team_name": team_name,
                "team_type": team_type,
                "won_quality": won_quality,
                "quality_margin": report.get("quality_margin", 0.0),

                # Quality scores
                "avg_logical_coherence": team_data.get("avg_logical_coherence", 0.0),
                "avg_evidence_strength": team_data.get("avg_evidence_strength", 0.0),
                "avg_relevance": team_data.get("avg_relevance", 0.0),
                "avg_persuasiveness": team_data.get("avg_persuasiveness", 0.0),
                "avg_clarity": team_data.get("avg_clarity", 0.0),
                "avg_counterargument_handling": team_data.get("avg_counterargument_handling", 0.0),
                "avg_overall_score": team_data.get("avg_overall_score", 0.0),
                "consistency_score": team_data.get("consistency_score", 0.0),

                # Argument count
                "num_arguments": len(team_data.get("arguments", [])),

                # Strengths and weaknesses (as lists)
                "strengths": "; ".join(team_data.get("overall_strengths", [])),
                "weaknesses": "; ".join(team_data.get("overall_weaknesses", []))
            }

            records.append(record)

    return records


def save_to_csv(records: List[Dict[str, Any]], output_path: Path):
    """
    Save records to CSV file.

    Args:
        records: List of team score records
        output_path: Path to save CSV file
    """
    if not records:
        print("No records to save")
        return

    fieldnames = [
        "config_id",
        "topic",
        "team_name",
        "team_type",
        "won_quality",
        "quality_margin",
        "avg_logical_coherence",
        "avg_evidence_strength",
        "avg_relevance",
        "avg_persuasiveness",
        "avg_clarity",
        "avg_counterargument_handling",
        "avg_overall_score",
        "consistency_score",
        "num_arguments",
        "strengths",
        "weaknesses"
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Saved {len(records)} records to {output_path}")


def create_analysis_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create summary statistics for analysis.

    Args:
        records: List of team score records

    Returns:
        Dictionary with summary statistics
    """
    if not records:
        return {}

    # Group by team type
    prop_scores = [r["avg_overall_score"] for r in records if r["team_type"] == "proposition"]
    opp_scores = [r["avg_overall_score"] for r in records if r["team_type"] == "opposition"]

    # Quality dimension averages
    dimensions = [
        "avg_logical_coherence",
        "avg_evidence_strength",
        "avg_relevance",
        "avg_persuasiveness",
        "avg_clarity",
        "avg_counterargument_handling"
    ]

    dimension_stats = {}
    for dim in dimensions:
        prop_dim = [r[dim] for r in records if r["team_type"] == "proposition"]
        opp_dim = [r[dim] for r in records if r["team_type"] == "opposition"]

        dimension_stats[dim] = {
            "proposition_mean": sum(prop_dim) / len(prop_dim) if prop_dim else 0,
            "opposition_mean": sum(opp_dim) / len(opp_dim) if opp_dim else 0,
            "difference": (
                (sum(prop_dim) / len(prop_dim) if prop_dim else 0) -
                (sum(opp_dim) / len(opp_dim) if opp_dim else 0)
            )
        }

    summary = {
        "total_teams_evaluated": len(records),
        "total_simulations": len(set(r["config_id"] for r in records)),

        "proposition_teams": {
            "count": len(prop_scores),
            "mean_score": sum(prop_scores) / len(prop_scores) if prop_scores else 0,
            "min_score": min(prop_scores) if prop_scores else 0,
            "max_score": max(prop_scores) if prop_scores else 0,
            "wins": sum(1 for r in records if r["team_type"] == "proposition" and r["won_quality"])
        },

        "opposition_teams": {
            "count": len(opp_scores),
            "mean_score": sum(opp_scores) / len(opp_scores) if opp_scores else 0,
            "min_score": min(opp_scores) if opp_scores else 0,
            "max_score": max(opp_scores) if opp_scores else 0,
            "wins": sum(1 for r in records if r["team_type"] == "opposition" and r["won_quality"])
        },

        "dimension_statistics": dimension_stats,

        "overall_statistics": {
            "mean_quality_score": sum(r["avg_overall_score"] for r in records) / len(records),
            "mean_consistency": sum(r["consistency_score"] for r in records) / len(records),
            "mean_quality_margin": sum(abs(r["quality_margin"]) for r in records) / len(records)
        }
    }

    return summary


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Extract quality scores for analysis"
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("evaluation_results/quality_reports"),
        help="Directory containing quality report JSON files"
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("analysis/quality_scores.csv"),
        help="Output CSV file path"
    )
    parser.add_argument(
        "--output-summary",
        type=Path,
        default=Path("analysis/quality_summary.json"),
        help="Output summary JSON file path"
    )

    args = parser.parse_args()

    print("Quality Score Extraction")
    print(f"Reports directory: {args.reports_dir}")
    print(f"Output CSV: {args.output_csv}")
    print(f"Output summary: {args.output_summary}")

    # Load reports
    print(f"\nLoading quality reports...")
    reports = load_quality_reports(args.reports_dir)

    if not reports:
        print("No quality reports found!")
        return

    print(f"Loaded {len(reports)} quality report(s)")

    # Extract team scores
    print(f"\nExtracting team scores...")
    records = extract_team_scores(reports)
    print(f"Extracted {len(records)} team score record(s)")

    # Save to CSV
    save_to_csv(records, args.output_csv)

    # Create and save summary
    print(f"\nGenerating summary statistics...")
    summary = create_analysis_summary(records)

    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_summary, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Summary saved to {args.output_summary}")

    # Print key statistics
    print(f"\n{'='*60}")
    print("KEY STATISTICS")
    print(f"{'='*60}")
    print(f"Total simulations: {summary['total_simulations']}")
    print(f"Total teams evaluated: {summary['total_teams_evaluated']}")
    print(f"\nProposition teams:")
    print(f"  Mean score: {summary['proposition_teams']['mean_score']:.2f}/10")
    print(f"  Quality wins: {summary['proposition_teams']['wins']}/{summary['proposition_teams']['count']}")
    print(f"\nOpposition teams:")
    print(f"  Mean score: {summary['opposition_teams']['mean_score']:.2f}/10")
    print(f"  Quality wins: {summary['opposition_teams']['wins']}/{summary['opposition_teams']['count']}")
    print(f"\nOverall:")
    print(f"  Mean quality score: {summary['overall_statistics']['mean_quality_score']:.2f}/10")
    print(f"  Mean quality margin: {summary['overall_statistics']['mean_quality_margin']:.2f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
