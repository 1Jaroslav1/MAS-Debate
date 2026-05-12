"""
Debate Results Aggregation Script

This script aggregates debate simulation results across multiple folders
to generate metrics for result tables and Pareto frontier visualizations.

Usage:
    python scripts/aggregate_debate_results.py --folders <folder1> <folder2> ... --output <output.json>

Example:
    python scripts/aggregate_debate_results.py \
        --folders architecture_tests_2/central_bank_digital_20260124_012432 \
                  architecture_tests_2/commercial_space_20260124_134002 \
        --output aggregated_results.json

Output:
    Creates a JSON file with:
    - Architecture metrics (quality, tokens, time, win rate)
    - Pareto frontier data points
    - LaTeX table-ready data
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.aggregate_results.parsers import (
    discover_debate_files,
    find_quality_file,
    load_debate_result,
    load_quality_results
)
from scripts.aggregate_results.extractors import (
    extract_tokens_by_architecture,
    extract_time_by_architecture,
    extract_quality_by_architecture,
    determine_winner,
    get_architectures_from_file,
    parse_architectures_from_filename
)
from scripts.aggregate_results.aggregator import ArchitectureMetricsAggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_folder(folder_path: Path, aggregator: ArchitectureMetricsAggregator):
    """
    Process all debate results in a single folder.

    Args:
        folder_path: Path to folder containing result files
        aggregator: ArchitectureMetricsAggregator instance to update
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing folder: {folder_path.name}")
    logger.info(f"{'='*60}\n")

    # Discover debate result files
    debate_files = discover_debate_files(folder_path)

    if not debate_files:
        logger.warning(f"No debate files found in {folder_path}")
        return

    # Find quality evaluation file
    quality_file = find_quality_file(folder_path)

    if not quality_file:
        logger.warning(f"No quality evaluation file found in {folder_path}")
        logger.warning("Quality scores will not be included for this folder")

    # Load quality data once
    quality_data = None
    if quality_file:
        quality_data = load_quality_results(quality_file)

    # Process each debate file
    for debate_file in debate_files:
        logger.info(f"Processing: {debate_file.name}")

        # Load debate result
        debate_data = load_debate_result(debate_file)
        if not debate_data:
            continue

        # Parse architectures from filename (more reliable than JSON content)
        arch1, arch2, role = parse_architectures_from_filename(debate_file.name)

        if not arch1 or not arch2:
            logger.warning(f"Could not parse architectures from filename: {debate_file.name}")
            continue

        # Determine which is proposition and which is opposition based on role
        # role indicates which team type arch1 is playing as in THIS file
        # In "opposition" files: arch1 plays opposition role
        # In "proposition" files: arch1 plays proposition role
        if role == 'opposition':
            opp_arch = arch1
            prop_arch = arch2
        else:  # proposition
            prop_arch = arch1
            opp_arch = arch2

        # Build architecture mapping for extraction
        # Map team names to the actual architectures from filename
        team_architectures = debate_data.get('team_architectures', {})
        arch_mapping = {}

        for team_name, team_info in team_architectures.items():
            team_type = team_info.get('team_type')
            if team_type == 'proposition':
                arch_mapping[team_name] = prop_arch
            elif team_type == 'opposition':
                arch_mapping[team_name] = opp_arch

        # Extract tokens using corrected mapping
        exec_metrics = debate_data.get('execution_metrics', {})
        teams = exec_metrics.get('teams', [])

        for team in teams:
            team_name = team.get('team_name')
            tokens = team.get('total_tokens', 0)
            time_sec = team.get('total_time_seconds', 0.0)

            arch = arch_mapping.get(team_name)
            if arch:
                if tokens > 0:
                    aggregator.add_tokens(arch, tokens)
                if time_sec > 0:
                    aggregator.add_time(arch, time_sec)

        # Extract quality scores with corrected architecture names
        if quality_data:
            results = quality_data.get('results', [])

            for result in results:
                if result.get('source_file') == debate_file.name:
                    evaluations = result.get('argument_evaluations', [])

                    for evaluation in evaluations:
                        team_name = evaluation.get('team')
                        quality_eval = evaluation.get('quality_evaluation', {})
                        overall_quality = quality_eval.get('overall_quality')

                        # Map team_name to actual architecture
                        arch = arch_mapping.get(team_name)
                        if arch and overall_quality is not None:
                            aggregator.add_quality_score(arch, overall_quality)

                    break

        # Determine winner and map to actual architecture
        winning_team_type, _ = determine_winner(debate_data)

        if winning_team_type == 'proposition':
            winning_arch = prop_arch
        elif winning_team_type == 'opposition':
            winning_arch = opp_arch
        else:
            winning_arch = None

        # Record debate outcome
        aggregator.record_debate_outcome(prop_arch, opp_arch, winning_arch)

        logger.info(f"  Prop: {prop_arch}, Opp: {opp_arch}, Winner: {winning_arch or 'Tie'}")

    logger.info(f"\nCompleted processing {folder_path.name}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Aggregate debate simulation results across multiple folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single folder
  python scripts/aggregate_debate_results.py \
      --folders architecture_tests_2/central_bank_digital_20260124_012432 \
      --output results.json

  # Process multiple folders
  python scripts/aggregate_debate_results.py \
      --folders architecture_tests_2/central_bank_digital_20260124_012432 \
                architecture_tests_2/commercial_space_20260124_134002 \
      --output aggregated_results.json

Output:
  Creates JSON file with:
  - Architecture metrics (quality, tokens, time, win rate)
  - Pareto frontier data
  - LaTeX table-ready data
        """
    )
    parser.add_argument(
        '--folders',
        nargs='+',
        type=Path,
        required=True,
        help='Paths to folders containing debate result files'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output JSON file path'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Resolve folder paths
    folders = [f.resolve() for f in args.folders]

    # Validate folders
    for folder in folders:
        if not folder.exists():
            logger.error(f"Folder not found: {folder}")
            sys.exit(1)
        if not folder.is_dir():
            logger.error(f"Not a directory: {folder}")
            sys.exit(1)

    logger.info(f"\n{'='*60}")
    logger.info("Debate Results Aggregation")
    logger.info(f"Folders: {len(folders)}")
    logger.info(f"Output: {args.output}")
    logger.info(f"{'='*60}\n")

    # Create aggregator
    aggregator = ArchitectureMetricsAggregator()

    # Process each folder
    for folder in folders:
        try:
            process_folder(folder, aggregator)
        except Exception as e:
            logger.error(f"Error processing {folder}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Calculate aggregates
    logger.info(f"\n{'='*60}")
    logger.info("Calculating aggregate metrics...")
    logger.info(f"{'='*60}\n")

    metrics = aggregator.calculate_aggregates()
    pareto_data = aggregator.get_pareto_data()
    table_data = aggregator.format_for_latex_table(metrics)

    # Build output
    output = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_folders_processed': len(folders),
            'folder_names': [f.name for f in folders],
            'architectures': sorted(metrics.keys())
        },
        'architecture_metrics': metrics,
        'pareto_frontier': pareto_data,
        'latex_table': table_data
    }

    # Save output
    logger.info(f"Saving results to: {args.output}")

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("Aggregation Complete!")
    logger.info(f"{'='*60}")
    logger.info(f"Architectures processed: {len(metrics)}")
    logger.info(f"Pareto frontier points: {len([p for p in pareto_data if not p['is_dominated']])}")
    logger.info(f"Output saved to: {args.output}")
    logger.info(f"{'='*60}\n")

    # Print summary table
    print("\nArchitecture Summary:")
    print(f"{'Architecture':<20} {'Quality':<10} {'Tokens':<10} {'Time (s)':<10} {'Win Rate':<10}")
    print("-" * 70)

    for arch in sorted(metrics.keys()):
        data = metrics[arch]
        quality = f"{data['quality']['mean']:.2f}" if data.get('quality') else "N/A"
        tokens = f"{int(data['tokens']['mean']):,}" if data.get('tokens') else "N/A"
        time = f"{data['time_seconds']['mean']:.1f}" if data.get('time_seconds') else "N/A"
        win_rate = f"{data.get('win_rate', 0.0):.0f}%" if data.get('win_rate') is not None else "N/A"

        print(f"{arch:<20} {quality:<10} {tokens:<10} {time:<10} {win_rate:<10}")


if __name__ == "__main__":
    main()
