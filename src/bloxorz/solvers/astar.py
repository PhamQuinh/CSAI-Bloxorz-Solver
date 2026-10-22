"""A* Search Solver for Bloxorz.
To be implemented by TV3 - Algorithm Specialist 2.
"""
from bloxorz.solvers.base import BaseSolver, SearchResult

class AStarSolver(BaseSolver):
    """A* Search using f(n) = g(n) + h(n)."""

    def solve(self) -> SearchResult:
        raise NotImplementedError("AStarSolver will be implemented by TV3.")
