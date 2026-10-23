"""Abstract base solver class and standardized search result dataclass."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from bloxorz.domain.models import Stage
from bloxorz.domain.actions import Action

@dataclass
class SearchResult:
    found: bool
    actions: List[Action] = field(default_factory=list)
    solution_length: int = 0
    search_time: float = 0.0      # seconds
    peak_memory_mb: float = 0.0   # MB
    expanded_nodes: int = 0

    def to_dict(self) -> dict:
        """Expose the team-wide solver output format without changing internals."""
        return {
            "status": "SUCCESS" if self.found else "FAILED",
            "path": [action.value for action in self.actions],
            "solution_length": self.solution_length,
            "search_time": self.search_time,
            "peak_memory_mb": self.peak_memory_mb,
            "expanded_nodes": self.expanded_nodes,
        }

class BaseSolver(ABC):
    """Abstract interface that all Bloxorz solvers must implement."""

    def __init__(self, stage: Stage):
        self.stage = stage

    @abstractmethod
    def solve(self) -> SearchResult:
        """Execute the search algorithm and return standardized SearchResult."""
        pass
