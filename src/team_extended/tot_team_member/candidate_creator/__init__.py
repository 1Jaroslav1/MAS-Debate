"""
ToT Candidate Creator Module

Exports the ToT-specific candidate creator node that creates candidates
from evaluated argument variations.
"""

from .candidate_creator_node import candidate_creator_node

__all__ = ["candidate_creator_node"]
