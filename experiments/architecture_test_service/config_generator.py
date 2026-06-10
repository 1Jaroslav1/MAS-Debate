"""
Configuration generator for architecture testing.

Generates 40 config variations from a base config:
- 20 architecture pairs (5×4, no self-comparison)
- Each pair tested twice (team role swap)
"""

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .architectures import ArchitectureConfig, get_all_architecture_keys, get_architecture_config


def generate_architecture_pairs() -> List[Tuple[str, str]]:
    """
    Generate all architecture pairs without self-comparison.

    Returns:
        List of (arch1, arch2) tuples where arch1 != arch2
        Total: 5 × 4 = 20 pairs
    """
    arch_keys = get_all_architecture_keys()
    pairs = []

    for arch1 in arch_keys:
        for arch2 in arch_keys:
            if arch1 != arch2:  # No self-comparison
                pairs.append((arch1, arch2))

    return pairs


def apply_architecture_to_team(team_config: Dict[str, Any], arch_config: ArchitectureConfig) -> None:
    """
    Apply architecture configuration to a team and all its members.

    Modifies team_config in-place:
    - Sets team-level architecture field
    - Sets member-level architecture and knowledge/evaluation flags for ALL members

    Args:
        team_config: Team configuration dict
        arch_config: Architecture configuration to apply
    """
    # Set team-level architecture
    team_config["architecture"] = arch_config.architecture

    # Apply to all members in the team
    if "members" not in team_config:
        return

    for member in team_config["members"]:
        member["knowledge_active"] = arch_config.knowledge_active
        member["knowledge_use_rag"] = arch_config.knowledge_use_rag
        member["knowledge_use_web_search"] = arch_config.knowledge_use_web_search
        member["evaluation_active"] = arch_config.evaluation_active


def swap_team_roles(config: Dict[str, Any]) -> None:
    """
    Swap the roles of the two teams (proposition ↔ opposition).

    Modifies config in-place:
    - Swaps team_type between teams
    - Swaps viewpoint_orientation if present

    Args:
        config: Debate configuration dict with exactly 2 teams
    """
    if len(config.get("teams", [])) != 2:
        raise ValueError("Config must have exactly 2 teams for role swapping")

    team1, team2 = config["teams"][0], config["teams"][1]

    # Swap team_type
    team1["team_type"], team2["team_type"] = team2["team_type"], team1["team_type"]

    # Swap viewpoint_orientation if present
    if "viewpoint_orientation" in team1 and "viewpoint_orientation" in team2:
        team1["viewpoint_orientation"], team2["viewpoint_orientation"] = (
            team2["viewpoint_orientation"],
            team1["viewpoint_orientation"],
        )


def generate_output_filename(
    base_id: str,
    team1_arch: str,
    team2_arch: str,
    team1_role: str,
    batch_dir: Path,
) -> str:
    """
    Generate unique output filename for a config variation.

    Pattern: {base_id}_{team1_arch}_{team2_arch}_{team1_role}_results.json

    Args:
        base_id: Base config ID
        team1_arch: Team 1 architecture short name
        team2_arch: Team 2 architecture short name
        team1_role: Team 1 role (proposition or opposition)
        batch_dir: Batch directory path

    Returns:
        Full path to output file
    """
    filename = f"{base_id}_{team1_arch}_{team2_arch}_{team1_role}_results.json"
    return str(batch_dir / filename)


def validate_base_config(config: Dict[str, Any]) -> None:
    """
    Validate that base config meets requirements.

    Requirements:
    - Must have exactly 2 teams
    - Each team must have at least 1 member

    Args:
        config: Base configuration dict

    Raises:
        ValueError: If validation fails
    """
    teams = config.get("teams", [])

    if len(teams) != 2:
        raise ValueError(f"Config must have exactly 2 teams, found {len(teams)}")

    for i, team in enumerate(teams):
        members = team.get("members", [])
        if len(members) == 0:
            raise ValueError(f"Team {i} must have at least 1 member")


def generate_configs(
    base_config_path: str | Path,
    batch_dir: Path,
) -> List[Tuple[Dict[str, Any], str, str, str, str]]:
    """
    Generate 40 config variations from a base config.

    Process:
    1. Load and validate base config
    2. Generate 20 architecture pairs (no self-comparison)
    3. For each pair, create 2 configs (original roles + swapped roles)
    4. Apply architectures to all team members
    5. Set unique output filenames

    Args:
        base_config_path: Path to base configuration JSON file
        batch_dir: Directory for batch outputs

    Returns:
        List of (config_dict, team1_arch, team2_arch, team1_role, team2_role) tuples
        Total: 40 configs

    Raises:
        ValueError: If config validation fails
    """
    # Load base config
    base_config_path = Path(base_config_path)
    with open(base_config_path, "r", encoding="utf-8") as f:
        base_config = json.load(f)

    # Validate
    validate_base_config(base_config)

    # Get base config ID
    base_id = base_config.get("id", base_config_path.stem)

    # Generate architecture pairs
    arch_pairs = generate_architecture_pairs()

    # Generate configs
    configs = []

    for arch1_key, arch2_key in arch_pairs:
        arch1_config = get_architecture_config(arch1_key)
        arch2_config = get_architecture_config(arch2_key)

        # Generate 2 configs: original roles + swapped roles
        for swap in [False, True]:
            # Deep copy base config
            config = copy.deepcopy(base_config)

            # Apply architectures
            apply_architecture_to_team(config["teams"][0], arch1_config)
            apply_architecture_to_team(config["teams"][1], arch2_config)

            # Swap roles if needed
            if swap:
                swap_team_roles(config)

            # Get team roles
            team1_role = config["teams"][0]["team_type"]
            team2_role = config["teams"][1]["team_type"]

            # Generate output filename
            output_file = generate_output_filename(
                base_id,
                arch1_config.short_name,
                arch2_config.short_name,
                team1_role,
                batch_dir,
            )

            # Set output file in config (use absolute path to ensure it works from temp file)
            config["output_file"] = str(Path(output_file).absolute())

            # Add to list
            configs.append((
                config,
                arch1_config.short_name,
                arch2_config.short_name,
                team1_role,
                team2_role,
            ))

    return configs
