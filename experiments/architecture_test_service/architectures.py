"""
Architecture definitions for debate testing.

Defines the 5 debate architectures and their configurations.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ArchitectureConfig:
    """Configuration for a debate architecture."""

    name: str  # Full display name
    short_name: str  # Abbreviated name for filenames
    architecture: str  # Architecture type for team config
    knowledge_active: bool
    knowledge_use_rag: bool
    knowledge_use_web_search: bool
    evaluation_active: bool


# Define the 5 architectures
ARCHITECTURES: Dict[str, ArchitectureConfig] = {
    "cot": ArchitectureConfig(
        name="Chain of Thought",
        short_name="cot",
        architecture="cot",
        knowledge_active=False,
        knowledge_use_rag=False,
        knowledge_use_web_search=False,
        evaluation_active=False,
    ),
    "cot_refl": ArchitectureConfig(
        name="CoT with Reflection",
        short_name="cot_refl",
        architecture="cot",
        knowledge_active=False,
        knowledge_use_rag=False,
        knowledge_use_web_search=False,
        evaluation_active=True,
    ),
    "cot_tools": ArchitectureConfig(
        name="CoT with Tools",
        short_name="cot_tools",
        architecture="cot",
        knowledge_active=True,
        knowledge_use_rag=False,
        knowledge_use_web_search=True,
        evaluation_active=False,
    ),
    "tot": ArchitectureConfig(
        name="Tree of Thoughts",
        short_name="tot",
        architecture="tot",
        knowledge_active=False,
        knowledge_use_rag=False,
        knowledge_use_web_search=False,
        evaluation_active=False,
    ),
    "godsaf_refl": ArchitectureConfig(
        name="AAF with Reflection",
        short_name="godsaf_refl",
        architecture="godsaf",
        knowledge_active=False,
        knowledge_use_rag=False,
        knowledge_use_web_search=False,
        evaluation_active=True,
    ),
}


def get_architecture_config(arch_key: str) -> ArchitectureConfig:
    """Get architecture configuration by key."""
    if arch_key not in ARCHITECTURES:
        raise ValueError(f"Unknown architecture: {arch_key}. Valid options: {list(ARCHITECTURES.keys())}")
    return ARCHITECTURES[arch_key]


def get_all_architecture_keys() -> list[str]:
    """Get all architecture keys."""
    return list(ARCHITECTURES.keys())
