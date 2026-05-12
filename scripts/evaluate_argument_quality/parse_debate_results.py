"""
Parse Debate Simulation Results

This module provides functions to parse debate simulation result JSON files
and extract arguments for quality evaluation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from src.team_extended.common.evaluator.model import Argument

logger = logging.getLogger(__name__)


def load_result_file(file_path: Path) -> Dict[str, Any]:
    """
    Load a debate simulation result JSON file.

    Args:
        file_path: Path to the result JSON file

    Returns:
        Dictionary containing the parsed result data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    logger.info(f"Loading result file: {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate required fields
    required_fields = ['config_id', 'topic', 'team_architectures', 'arguments']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise ValueError(f"Missing required fields in {file_path.name}: {missing_fields}")

    return data


def extract_architecture_info(result_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract architecture information for proposition and opposition teams.

    Args:
        result_data: Parsed result data from load_result_file

    Returns:
        Dictionary with 'proposition' and 'opposition' architecture details
    """
    team_architectures = result_data['team_architectures']

    architecture_info = {}

    for team_name, team_data in team_architectures.items():
        team_type = team_data.get('team_type', 'unknown')

        info = {
            'team_name': team_name,
            'architecture': team_data.get('architecture', 'unknown'),
            'team_type': team_type,
            'members': team_data.get('members', [])
        }

        architecture_info[team_type] = info

    return architecture_info


def convert_to_argument_objects(
    result_data: Dict[str, Any],
    source_file: str
) -> List[Tuple[Argument, Dict[str, Any]]]:
    """
    Convert arguments from result data to Argument objects for evaluation.

    Args:
        result_data: Parsed result data from load_result_file
        source_file: Name of the source file for metadata

    Returns:
        List of tuples containing (Argument object, metadata dict)
    """
    arguments = result_data.get('arguments', [])
    topic = result_data['topic']
    team_architectures = result_data['team_architectures']

    argument_objects = []

    for i, arg in enumerate(arguments, 1):
        team_name = arg.get('team', '')

        if team_name not in team_architectures:
            logger.warning(f"Team {team_name} not found in architectures, skipping argument")
            continue

        team_arch = team_architectures[team_name]
        team_type = team_arch.get('team_type', 'unknown')
        architecture = team_arch.get('architecture', 'unknown')

        # Extract viewpoint_orientation from member config or use default
        viewpoint_orientation = 'balanced'
        members = team_arch.get('members', [])
        if members and isinstance(members, list) and len(members) > 0:
            # Check if viewpoint_orientation exists in member config
            member = members[0]
            if isinstance(member, dict):
                viewpoint_orientation = member.get('viewpoint_orientation', 'balanced')

        # Create Argument object
        argument_obj = Argument(
            text=arg.get('text', ''),
            topic=topic,
            team_type=team_type,
            team_perspective=team_name,
            viewpoint_orientation=viewpoint_orientation
        )

        # Create metadata for tracking
        metadata = {
            'argument_id': f"arg{i}",
            'source_file': source_file,
            'round': arg.get('round', 1),
            'team': team_name,
            'team_type': team_type,
            'architecture': architecture,
            'member_name': arg.get('member_name', 'Unknown'),
            'argument_name': arg.get('argument_name', f'argument_{i}'),
            'original_text': arg.get('text', '')
        }

        argument_objects.append((argument_obj, metadata))
        logger.debug(f"Converted argument {metadata['argument_id']} from {team_name}")

    logger.info(f"Converted {len(argument_objects)} arguments from {source_file}")
    return argument_objects


def discover_result_files(folder_path: Path) -> List[Path]:
    """
    Discover all *_results.json files in a folder.

    Args:
        folder_path: Path to folder containing result files

    Returns:
        List of Path objects for result files
    """
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    if not folder_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder_path}")

    result_files = list(folder_path.glob("*_results.json"))

    logger.info(f"Discovered {len(result_files)} result files in {folder_path.name}")

    return sorted(result_files)


def group_files_by_config_id(result_files: List[Path]) -> Dict[str, List[Path]]:
    """
    Group result files by their config_id.

    Args:
        result_files: List of result file paths

    Returns:
        Dictionary mapping config_id to list of file paths
    """
    grouped = {}

    for file_path in result_files:
        try:
            data = load_result_file(file_path)
            config_id = data.get('config_id', 'unknown')

            if config_id not in grouped:
                grouped[config_id] = []

            grouped[config_id].append(file_path)

        except Exception as e:
            logger.error(f"Error reading {file_path.name}: {e}")
            continue

    logger.info(f"Grouped files into {len(grouped)} config_id(s)")

    return grouped
