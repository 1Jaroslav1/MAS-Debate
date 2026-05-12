"""
File Parsers for Debate Results

Functions for loading and parsing debate result files, quality evaluations,
and batch summaries.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def load_debate_result(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a debate result JSON file.

    Args:
        file_path: Path to *_results.json file

    Returns:
        Parsed JSON data or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load {file_path.name}: {e}")
        return None


def load_quality_results(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load an argument quality evaluation JSON file.

    Args:
        file_path: Path to *_arg_quality.json file

    Returns:
        Parsed JSON data or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load quality file {file_path.name}: {e}")
        return None


def load_batch_summary(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a batch summary JSON file.

    Args:
        file_path: Path to batch_summary.json file

    Returns:
        Parsed JSON data or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load batch summary {file_path.name}: {e}")
        return None


def discover_debate_files(folder_path: Path) -> list[Path]:
    """
    Discover all debate result files in a folder.

    Args:
        folder_path: Path to folder containing result files

    Returns:
        List of paths to *_results.json files
    """
    result_files = list(folder_path.glob("*_results.json"))
    logger.info(f"Found {len(result_files)} debate result files in {folder_path.name}")
    return result_files


def find_quality_file(folder_path: Path) -> Optional[Path]:
    """
    Find the argument quality evaluation file in a folder.

    Args:
        folder_path: Path to folder

    Returns:
        Path to *_arg_quality.json file or None if not found
    """
    quality_files = list(folder_path.glob("*_arg_quality.json"))

    if not quality_files:
        logger.warning(f"No quality evaluation file found in {folder_path.name}")
        return None

    if len(quality_files) > 1:
        logger.warning(f"Multiple quality files found in {folder_path.name}, using first")

    return quality_files[0]


def find_batch_summary(folder_path: Path) -> Optional[Path]:
    """
    Find the batch summary file in a folder.

    Args:
        folder_path: Path to folder

    Returns:
        Path to batch_summary.json or None if not found
    """
    summary_path = folder_path / "batch_summary.json"

    if summary_path.exists():
        return summary_path

    logger.warning(f"No batch summary found in {folder_path.name}")
    return None
