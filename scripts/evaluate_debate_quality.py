"""
Debate Argument Quality Evaluation Script

This script evaluates the quality of arguments from debate simulation results
using the Wachsmuth et al. (2017) quality taxonomy with 15 dimensions.

Usage:
    python scripts/evaluate_debate_quality.py <folder_path>

Example:
    python scripts/evaluate_debate_quality.py architecture_tests_2/central_bank_digital_20260124_012432

Output:
    Creates {config_id}_arg_quality.json in the input folder with:
    - Architecture information (proposition/opposition)
    - Quality evaluations for all arguments
    - Aggregate statistics
"""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.evaluate_argument_quality.parse_debate_results import (
    discover_result_files,
    group_files_by_config_id,
    load_result_file,
    extract_architecture_info,
    convert_to_argument_objects
)
from scripts.evaluate_argument_quality.evaluate_quality import (
    initialize_evaluator,
    evaluate_arguments_batch,
    calculate_aggregate_statistics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_config_group(
    config_id: str,
    result_files: List[Path],
    output_folder: Path
):
    """
    Process all result files for a single config_id.

    Args:
        config_id: Configuration identifier
        result_files: List of result file paths with this config_id
        output_folder: Folder to save output JSON
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing config_id: {config_id}")
    logger.info(f"Files: {len(result_files)}")
    logger.info(f"{'='*60}\n")

    # Initialize evaluator once for all files
    evaluator = initialize_evaluator()

    # Process each file separately
    file_results = []
    topic = None

    for file_path in result_files:
        logger.info(f"\nProcessing file: {file_path.name}")

        try:
            result_data = load_result_file(file_path)

            # Store topic from first file
            if topic is None:
                topic = result_data['topic']

            # Extract architecture info
            arch_info = extract_architecture_info(result_data)

            # Convert arguments for this file
            arguments = convert_to_argument_objects(result_data, file_path.name)

            if not arguments:
                logger.warning(f"No arguments found in {file_path.name}")
                continue

            logger.info(f"Evaluating {len(arguments)} arguments from {file_path.name}...")

            # Evaluate arguments for this file
            evaluations = await evaluate_arguments_batch(evaluator, arguments)

            if not evaluations:
                logger.error(f"All evaluations failed for {file_path.name}")
                continue

            # Calculate statistics for this file
            file_stats = calculate_aggregate_statistics(evaluations)

            # Build file result
            file_result = {
                'source_file': file_path.name,
                'proposition': arch_info.get('proposition', {}),
                'opposition': arch_info.get('opposition', {}),
                'argument_evaluations': evaluations,
                'statistics': file_stats
            }

            file_results.append(file_result)

            logger.info(f"✓ Completed {file_path.name}")
            logger.info(f"  Arguments: {file_stats['total_arguments']}")
            logger.info(f"  Avg quality: {file_stats['average_overall_quality']:.3f}")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if not file_results:
        logger.warning(f"No results generated for config_id: {config_id}")
        return

    # Calculate overall aggregate statistics
    all_evaluations = []
    for file_result in file_results:
        all_evaluations.extend(file_result['argument_evaluations'])

    overall_stats = calculate_aggregate_statistics(all_evaluations)

    # Build output structure
    output = {
        'config_id': config_id,
        'topic': topic,
        'evaluation_timestamp': datetime.now().isoformat(),
        'total_files_processed': len(file_results),
        'results': file_results,
        'overall_statistics': overall_stats
    }

    # Save output
    output_file = output_folder / f"{config_id}_arg_quality.json"
    logger.info(f"\nSaving results to: {output_file.name}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"\n✓ Successfully processed {config_id}")
    logger.info(f"  Files processed: {len(file_results)}")
    logger.info(f"  Total arguments: {overall_stats['total_arguments']}")
    logger.info(f"  Overall avg quality: {overall_stats['average_overall_quality']:.3f}")
    logger.info(f"  Output: {output_file}")


async def main_async(folder_path: Path):
    """
    Main async execution function.

    Args:
        folder_path: Path to folder containing result files
    """
    logger.info(f"\nDebate Argument Quality Evaluation")
    logger.info(f"Folder: {folder_path}")
    logger.info(f"{'='*60}\n")

    # Discover result files
    logger.info("Discovering result files...")
    result_files = discover_result_files(folder_path)

    if not result_files:
        logger.error("No result files found!")
        return

    logger.info(f"Found {len(result_files)} result files\n")

    # Group by config_id
    logger.info("Grouping files by config_id...")
    grouped = group_files_by_config_id(result_files)

    logger.info(f"Config IDs found: {', '.join(grouped.keys())}\n")

    # Process each config_id group
    for config_id, files in grouped.items():
        try:
            await process_config_group(config_id, files, folder_path)
        except Exception as e:
            logger.error(f"Error processing config_id {config_id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    logger.info(f"\n{'='*60}")
    logger.info("Evaluation complete!")
    logger.info(f"{'='*60}\n")


def main():
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(
        description="Evaluate argument quality for debate simulation results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate all results in a folder
  python scripts/evaluate_debate_quality.py architecture_tests_2/central_bank_digital_20260124_012432

  # With verbose logging
  python scripts/evaluate_debate_quality.py architecture_tests_2/central_bank_digital_20260124_012432 -v

Output:
  Creates {config_id}_arg_quality.json files in the input folder containing:
  - Architecture information (proposition/opposition)
  - Quality evaluations for all arguments (15 dimensions)
  - Aggregate statistics
        """
    )
    parser.add_argument(
        'folder',
        type=Path,
        help='Path to folder containing *_results.json files'
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

    # Resolve folder to absolute path
    folder_path = args.folder.resolve()

    # Validate folder
    if not folder_path.exists():
        logger.error(f"Folder not found: {folder_path}")
        sys.exit(1)

    if not folder_path.is_dir():
        logger.error(f"Not a directory: {folder_path}")
        sys.exit(1)

    # Run async main
    try:
        asyncio.run(main_async(folder_path))
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
