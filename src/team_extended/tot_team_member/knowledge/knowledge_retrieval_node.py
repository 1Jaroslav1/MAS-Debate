"""
ToT Knowledge Retrieval Node

For ToT architecture, we use the same knowledge retrieval as CoT since
knowledge retrieval doesn't need to be branched - all branches can share
the same knowledge base.
"""

from src.team_extended.cot_team_member.knowledge.knowledge_retrieval_node import knowledge_retrieval_node

# Re-export the CoT knowledge retrieval node
__all__ = ["knowledge_retrieval_node"]
