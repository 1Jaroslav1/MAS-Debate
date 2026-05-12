"""
Branch Manager for Tree of Thoughts Architecture

Manages the tree structure, branch tracking, pruning, and search algorithms
for exploring multiple reasoning paths in argument generation.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BranchType(Enum):
    """Type of branch in the ToT tree"""
    ANALYSIS = "analysis"
    ARGUMENT = "argument"


class PruningStrategy(Enum):
    """Strategy for pruning branches"""
    TOP_K = "top_k"
    THRESHOLD = "threshold"
    DIVERSITY = "diversity"


class SearchAlgorithm(Enum):
    """Algorithm for tree search"""
    BFS = "bfs"
    DFS = "dfs"
    BEST_FIRST = "best_first"


@dataclass
class Branch:
    """Represents a single branch in the tree"""
    branch_id: str
    parent_id: Optional[str]
    branch_type: BranchType
    data: Any
    score: float = 0.0
    is_pruned: bool = False
    depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BranchManager:
    """
    Manages the tree of thought branches, including:
    - Adding and tracking branches
    - Scoring and ranking
    - Pruning strategies
    - Tree search algorithms
    """

    def __init__(self):
        self.branches: Dict[str, Branch] = {}
        self.children: Dict[str, List[str]] = {}  # parent_id -> list of child_ids
        self.root_branches: List[str] = []
        self.pruning_count: int = 0
        self.total_branches: int = 0
        self.max_depth: int = 0

    def add_branch(
        self,
        branch_id: str,
        parent_id: Optional[str],
        branch_type: BranchType,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Branch:
        """Add a new branch to the tree"""
        depth = 0
        if parent_id and parent_id in self.branches:
            depth = self.branches[parent_id].depth + 1

        branch = Branch(
            branch_id=branch_id,
            parent_id=parent_id,
            branch_type=branch_type,
            data=data,
            depth=depth,
            metadata=metadata or {}
        )

        self.branches[branch_id] = branch
        self.total_branches += 1
        self.max_depth = max(self.max_depth, depth)

        # Track parent-child relationships
        if parent_id is None:
            self.root_branches.append(branch_id)
        else:
            if parent_id not in self.children:
                self.children[parent_id] = []
            self.children[parent_id].append(branch_id)

        logger.debug(f"Added branch {branch_id} (type={branch_type.value}, depth={depth})")
        return branch

    def set_score(self, branch_id: str, score: float) -> None:
        """Set the score for a branch"""
        if branch_id in self.branches:
            self.branches[branch_id].score = score
            logger.debug(f"Branch {branch_id} scored: {score:.2f}")

    def set_metadata(self, branch_id: str, key: str, value: Any) -> None:
        """Set metadata for a branch"""
        if branch_id in self.branches:
            self.branches[branch_id].metadata[key] = value

    def get_branch(self, branch_id: str) -> Optional[Branch]:
        """Get a branch by ID"""
        return self.branches.get(branch_id)

    def get_active_branches(self, branch_type: Optional[BranchType] = None) -> List[Branch]:
        """Get all non-pruned branches, optionally filtered by type"""
        branches = [b for b in self.branches.values() if not b.is_pruned]
        if branch_type:
            branches = [b for b in branches if b.branch_type == branch_type]
        return branches

    def get_children(self, branch_id: str) -> List[Branch]:
        """Get all children of a branch"""
        child_ids = self.children.get(branch_id, [])
        return [self.branches[child_id] for child_id in child_ids if child_id in self.branches]

    def prune_branches(
        self,
        strategy: PruningStrategy = PruningStrategy.TOP_K,
        keep_top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        diversity_weight: float = 0.2,
        branch_type: Optional[BranchType] = None
    ) -> int:
        """
        Prune branches based on the specified strategy

        Args:
            strategy: Pruning strategy to use
            keep_top_k: For TOP_K strategy, number of branches to keep
            threshold: For THRESHOLD strategy, minimum score to keep
            diversity_weight: For DIVERSITY strategy, weight of diversity vs score
            branch_type: Only prune branches of this type (None = all types)

        Returns:
            Number of branches pruned
        """
        # Get candidates for pruning
        candidates = self.get_active_branches(branch_type)

        if not candidates:
            return 0

        pruned_count = 0

        if strategy == PruningStrategy.TOP_K:
            pruned_count = self._prune_top_k(candidates, keep_top_k)
        elif strategy == PruningStrategy.THRESHOLD:
            pruned_count = self._prune_threshold(candidates, threshold)
        elif strategy == PruningStrategy.DIVERSITY:
            pruned_count = self._prune_diversity(candidates, keep_top_k, diversity_weight)

        self.pruning_count += 1
        logger.info(f"Pruning round {self.pruning_count}: {pruned_count} branches pruned")
        return pruned_count

    def _prune_top_k(self, candidates: List[Branch], keep_top_k: int) -> int:
        """Keep only top-k highest scoring branches"""
        if keep_top_k is None or len(candidates) <= keep_top_k:
            return 0

        # Sort by score descending
        sorted_branches = sorted(candidates, key=lambda b: b.score, reverse=True)

        # Prune all except top k
        pruned_count = 0
        for branch in sorted_branches[keep_top_k:]:
            branch.is_pruned = True
            pruned_count += 1
            logger.debug(f"Pruned branch {branch.branch_id} (score={branch.score:.2f})")

        return pruned_count

    def _prune_threshold(self, candidates: List[Branch], threshold: float) -> int:
        """Prune all branches below threshold score"""
        if threshold is None:
            return 0

        pruned_count = 0
        for branch in candidates:
            if branch.score < threshold:
                branch.is_pruned = True
                pruned_count += 1
                logger.debug(f"Pruned branch {branch.branch_id} (score={branch.score:.2f} < {threshold})")

        return pruned_count

    def _prune_diversity(
        self,
        candidates: List[Branch],
        keep_top_k: int,
        diversity_weight: float
    ) -> int:
        """Keep diverse high-scoring branches"""
        if keep_top_k is None or len(candidates) <= keep_top_k:
            return 0

        # Start with highest scoring branch
        sorted_branches = sorted(candidates, key=lambda b: b.score, reverse=True)
        selected = [sorted_branches[0]]
        remaining = sorted_branches[1:]

        # Greedily select branches that maximize score + diversity
        while len(selected) < keep_top_k and remaining:
            best_idx = 0
            best_score = -float('inf')

            for idx, branch in enumerate(remaining):
                # Calculate diversity score (simple: based on metadata differences)
                diversity_score = self._calculate_diversity(branch, selected)
                combined_score = (1 - diversity_weight) * branch.score + diversity_weight * diversity_score

                if combined_score > best_score:
                    best_score = combined_score
                    best_idx = idx

            selected.append(remaining.pop(best_idx))

        # Prune unselected branches
        pruned_count = 0
        for branch in remaining:
            branch.is_pruned = True
            pruned_count += 1

        return pruned_count

    def _calculate_diversity(self, branch: Branch, selected_branches: List[Branch]) -> float:
        """Calculate diversity score for a branch compared to already selected branches"""
        if not selected_branches:
            return 1.0

        # Simple diversity metric: different strategy rationales or metadata
        diversity_sum = 0.0
        for selected in selected_branches:
            # Compare metadata similarity
            similarity = 0.0
            if branch.metadata and selected.metadata:
                common_keys = set(branch.metadata.keys()) & set(selected.metadata.keys())
                if common_keys:
                    same_values = sum(1 for k in common_keys if branch.metadata[k] == selected.metadata[k])
                    similarity = same_values / len(common_keys)
            diversity_sum += (1.0 - similarity)

        return diversity_sum / len(selected_branches)

    def search_tree(self, algorithm: SearchAlgorithm = SearchAlgorithm.BEST_FIRST) -> Optional[Branch]:
        """
        Search the tree to find the best argument branch

        Args:
            algorithm: Search algorithm to use

        Returns:
            Best argument branch found, or None
        """
        if algorithm == SearchAlgorithm.BFS:
            return self._search_bfs()
        elif algorithm == SearchAlgorithm.DFS:
            return self._search_dfs()
        elif algorithm == SearchAlgorithm.BEST_FIRST:
            return self._search_best_first()

        return None

    def _search_bfs(self) -> Optional[Branch]:
        """Breadth-first search: find best argument at any level"""
        argument_branches = self.get_active_branches(BranchType.ARGUMENT)
        if not argument_branches:
            return None

        # Return highest scoring argument
        return max(argument_branches, key=lambda b: b.score)

    def _search_dfs(self) -> Optional[Branch]:
        """Depth-first search: follow best path from root to leaf"""
        if not self.root_branches:
            return None

        # Start from best root
        active_roots = [b for b in self.root_branches if not self.branches[b].is_pruned]
        if not active_roots:
            return None

        current_id = max(active_roots, key=lambda bid: self.branches[bid].score)

        # Follow best child at each level until we reach an argument
        while True:
            current = self.branches[current_id]

            if current.branch_type == BranchType.ARGUMENT:
                return current

            # Get active children
            children = [c for c in self.get_children(current_id) if not c.is_pruned]
            if not children:
                # Dead end, return current if it's an argument, else None
                return current if current.branch_type == BranchType.ARGUMENT else None

            # Follow best child
            current_id = max(children, key=lambda c: c.score).branch_id

    def _search_best_first(self) -> Optional[Branch]:
        """Best-first search: consider path quality, not just leaf score"""
        argument_branches = self.get_active_branches(BranchType.ARGUMENT)
        if not argument_branches:
            return None

        best_branch = None
        best_path_score = -float('inf')

        for arg_branch in argument_branches:
            # Calculate path score (average of all ancestors + current)
            path_score = self._calculate_path_score(arg_branch.branch_id)

            if path_score > best_path_score:
                best_path_score = path_score
                best_branch = arg_branch

        return best_branch

    def _calculate_path_score(self, branch_id: str) -> float:
        """Calculate average score along path from root to branch"""
        scores = []
        current_id = branch_id

        while current_id:
            branch = self.branches.get(current_id)
            if branch:
                scores.append(branch.score)
                current_id = branch.parent_id
            else:
                break

        return sum(scores) / len(scores) if scores else 0.0

    def get_best_path(self) -> List[str]:
        """Get the IDs of branches in the best path from root to selected argument"""
        argument_branches = self.get_active_branches(BranchType.ARGUMENT)
        if not argument_branches:
            return []

        best_branch = max(argument_branches, key=lambda b: b.score)

        # Trace back to root
        path = []
        current_id = best_branch.branch_id

        while current_id:
            path.append(current_id)
            branch = self.branches.get(current_id)
            if branch:
                current_id = branch.parent_id
            else:
                break

        return list(reversed(path))

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the tree"""
        active_branches = self.get_active_branches()

        return {
            "total_branches": self.total_branches,
            "active_branches": len(active_branches),
            "pruned_branches": self.total_branches - len(active_branches),
            "pruning_rounds": self.pruning_count,
            "max_depth": self.max_depth,
            "analysis_branches": len(self.get_active_branches(BranchType.ANALYSIS)),
            "argument_branches": len(self.get_active_branches(BranchType.ARGUMENT)),
        }
