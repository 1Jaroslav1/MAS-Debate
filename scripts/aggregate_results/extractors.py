"""
Metrics Extractors for Debate Results

Functions for extracting specific metrics (tokens, time, quality, wins)
from debate result data structures.
"""

import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_tokens_by_architecture(debate_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract token usage per architecture from debate result.

    Args:
        debate_data: Loaded debate result JSON

    Returns:
        Dict mapping architecture name to token count
    """
    tokens_by_arch = {}

    try:
        # Get team architecture mapping
        team_architectures = debate_data.get('team_architectures', {})
        arch_mapping = {team_name: info.get('architecture')
                       for team_name, info in team_architectures.items()}

        # Get execution metrics
        exec_metrics = debate_data.get('execution_metrics', {})
        teams = exec_metrics.get('teams', [])

        for team in teams:
            team_name = team.get('team_name')
            tokens = team.get('total_tokens', 0)

            # Map team_name to architecture
            arch = arch_mapping.get(team_name)
            if arch and tokens > 0:
                tokens_by_arch[arch] = tokens

    except Exception as e:
        logger.error(f"Error extracting tokens: {e}")

    return tokens_by_arch


def extract_time_by_architecture(debate_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract execution time per architecture from debate result.

    Args:
        debate_data: Loaded debate result JSON

    Returns:
        Dict mapping architecture name to time in seconds
    """
    time_by_arch = {}

    try:
        # Get team architecture mapping
        team_architectures = debate_data.get('team_architectures', {})
        arch_mapping = {team_name: info.get('architecture')
                       for team_name, info in team_architectures.items()}

        # Get execution metrics
        exec_metrics = debate_data.get('execution_metrics', {})
        teams = exec_metrics.get('teams', [])

        for team in teams:
            team_name = team.get('team_name')
            time_sec = team.get('total_time_seconds', 0.0)

            # Map team_name to architecture
            arch = arch_mapping.get(team_name)
            if arch and time_sec > 0:
                time_by_arch[arch] = time_sec

    except Exception as e:
        logger.error(f"Error extracting time: {e}")

    return time_by_arch


def extract_quality_by_architecture(
    quality_data: Dict[str, Any],
    source_file: str
) -> Dict[str, list[float]]:
    """
    Extract quality scores per architecture from quality evaluation data.

    Args:
        quality_data: Loaded *_arg_quality.json data
        source_file: Name of the source result file to match

    Returns:
        Dict mapping architecture to list of quality scores
    """
    quality_by_arch = {}

    try:
        results = quality_data.get('results', [])

        # Find the matching result file
        for result in results:
            if result.get('source_file') == source_file:
                # Extract quality scores from argument evaluations
                evaluations = result.get('argument_evaluations', [])

                for evaluation in evaluations:
                    arch = evaluation.get('architecture')
                    quality_eval = evaluation.get('quality_evaluation', {})
                    overall_quality = quality_eval.get('overall_quality')

                    if arch and overall_quality is not None:
                        if arch not in quality_by_arch:
                            quality_by_arch[arch] = []
                        quality_by_arch[arch].append(overall_quality)

                break

    except Exception as e:
        logger.error(f"Error extracting quality for {source_file}: {e}")

    return quality_by_arch


def determine_winner(debate_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Determine the winner of a debate from vote counts.

    Args:
        debate_data: Loaded debate result JSON

    Returns:
        Tuple of (winning_team_type, winning_architecture) or (None, None)
    """
    try:
        # Count final votes
        final_votes = debate_data.get('audience_final_votes', [])

        # Support both "decision" and "vote" keys
        agree_count = sum(1 for vote in final_votes
                         if vote.get('decision') == 'agree' or vote.get('vote') == 'agree')
        disagree_count = sum(1 for vote in final_votes
                            if vote.get('decision') == 'disagree' or vote.get('vote') == 'disagree')

        # Determine winning team type
        if agree_count > disagree_count:
            winning_team_type = 'proposition'
        elif disagree_count > agree_count:
            winning_team_type = 'opposition'
        else:
            return None, None  # Tie

        # Find architecture for winning team
        team_architectures = debate_data.get('team_architectures', {})

        for team_name, team_info in team_architectures.items():
            if team_info.get('team_type') == winning_team_type:
                winning_architecture = team_info.get('architecture')
                return winning_team_type, winning_architecture

    except Exception as e:
        logger.error(f"Error determining winner: {e}")

    return None, None


def extract_architecture_mapping(debate_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract mapping of team names to architectures.

    Args:
        debate_data: Loaded debate result JSON

    Returns:
        Dict mapping team name to architecture
    """
    arch_mapping = {}

    try:
        team_architectures = debate_data.get('team_architectures', {})

        for team_name, team_info in team_architectures.items():
            arch = team_info.get('architecture')
            if arch:
                arch_mapping[team_name] = arch

    except Exception as e:
        logger.error(f"Error extracting architecture mapping: {e}")

    return arch_mapping


def get_architectures_from_file(debate_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Get the two architectures used in a debate.

    Args:
        debate_data: Loaded debate result JSON

    Returns:
        Tuple of (proposition_architecture, opposition_architecture)
    """
    prop_arch = None
    opp_arch = None

    try:
        team_architectures = debate_data.get('team_architectures', {})

        for team_name, team_info in team_architectures.items():
            team_type = team_info.get('team_type')
            arch = team_info.get('architecture')

            if team_type == 'proposition':
                prop_arch = arch
            elif team_type == 'opposition':
                opp_arch = arch

    except Exception as e:
        logger.error(f"Error getting architectures: {e}")

    return prop_arch, opp_arch


def parse_architectures_from_filename(filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse architecture names from debate result filename.

    Filename format: {topic}_{arch1}_{arch2}_{role}_results.json
    Examples:
        - central_bank_digital_cot_cot_refl_opposition_results.json
          -> topic=central_bank_digital, arch1=cot, arch2=cot_refl, role=opposition
        - central_bank_digital_tot_godsaf_refl_proposition_results.json
          -> topic=central_bank_digital, arch1=tot, arch2=godsaf_refl, role=proposition

    Args:
        filename: Name of the result file

    Returns:
        Tuple of (arch1, arch2, role) where role is 'proposition' or 'opposition'
    """
    try:
        # Remove .json extension
        name = filename.replace('_results.json', '')

        # Split by underscore
        parts = name.split('_')

        # Role is always the last part (proposition or opposition)
        role = parts[-1]
        if role not in ['proposition', 'opposition']:
            logger.warning(f"Could not parse role from filename: {filename}")
            return None, None, None

        # Remove role from parts
        parts = parts[:-1]

        # Now we need to identify where the topic ends and architectures begin
        # Known architectures: cot, cot_refl, cot_tools, tot, godsaf, godsaf_refl
        # Strategy: Work backwards to find two architecture names

        arch2 = None
        arch1 = None

        # Build arch2 from end (can be multi-part like godsaf_refl)
        i = len(parts) - 1
        while i >= 0:
            if arch2 is None:
                arch2 = parts[i]
            else:
                # Check if this could be part of arch2 (like godsaf + _refl = godsaf_refl)
                potential_arch2 = parts[i] + '_' + arch2
                if potential_arch2 in ['cot_refl', 'cot_tools', 'godsaf_refl']:
                    arch2 = potential_arch2
                else:
                    # This is the start of arch1
                    break
            i -= 1

        # Build arch1 (remaining parts before arch2)
        if i >= 0:
            arch1_parts = []
            while i >= 0:
                part = parts[i]
                # Check if this looks like a topic word (not an architecture)
                # Topic words are usually lowercase nouns
                # Architecture keywords: cot, refl, tools, tot, godsaf
                if part in ['cot', 'refl', 'tools', 'tot', 'godsaf']:
                    arch1_parts.insert(0, part)
                    i -= 1
                else:
                    # This is still part of the topic
                    break

            if arch1_parts:
                arch1 = '_'.join(arch1_parts)

        if not arch1 or not arch2:
            logger.warning(f"Could not parse architectures from filename: {filename}")
            return None, None, None

        return arch1, arch2, role

    except Exception as e:
        logger.error(f"Error parsing filename {filename}: {e}")
        return None, None, None
