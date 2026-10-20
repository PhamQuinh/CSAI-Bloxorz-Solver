"""A* search for Bloxorz.

Implemented by TV3. g(n) is the sum of step_cost from costs.py, the same
non-uniform cost UCS uses. f(n) = g(n) + h(n). The default heuristic is
manhattan_half, a lower bound on the remaining cost of that function,
including a path that teleports through a split switch. A cheaper g
reopens the node, so the first time the goal is popped its g is optimal.
"""
import heapq
import itertools
from typing import Callable, Dict, List, Optional, Tuple

from bloxorz.domain.actions import Action
from bloxorz.domain.models import Stage
from bloxorz.domain.rules import is_goal_state
from bloxorz.domain.state import State
from bloxorz.engine.transitions import transition
from bloxorz.metrics.measurement import measure_performance
from bloxorz.solvers.base import BaseSolver, SearchResult
from bloxorz.solvers.costs import step_cost
from bloxorz.solvers.heuristics import manhattan_half

Heuristic = Callable[[State, Stage], float]

_CANDIDATE_ACTIONS = (
    Action.UP,
    Action.DOWN,
    Action.LEFT,
    Action.RIGHT,
    Action.SWITCH_BLOCK,
)


class AStarSolver(BaseSolver):
    """A* with a binary heap and reopening when a cheaper g is found."""

    def __init__(self, stage: Stage, heuristic: Optional[Heuristic] = None):
        super().__init__(stage)
        self.heuristic = heuristic if heuristic is not None else manhattan_half

    def solve(self) -> SearchResult:
        with measure_performance() as measured:
            found, actions, expanded = self._search()
            measured["expanded_nodes"] = expanded

        return SearchResult(
            found=found,
            actions=actions,
            solution_length=len(actions) if found else 0,
            search_time=measured["search_time"],
            peak_memory_mb=measured["peak_memory_mb"],
            expanded_nodes=measured["expanded_nodes"],
        )

    def _search(self) -> Tuple[bool, List[Action], int]:
        stage = self.stage
        sr, sc = stage.start_pos
        initial = State(
            r1=sr, c1=sc, r2=sr, c2=sc,
            bridges=stage.initial_bridges,
            active_cube=-1,
        )

        counter = itertools.count()
        h0 = self.heuristic(initial, stage)
        # (f, tie-break, g, state). The tie-break is unique, so State is never compared.
        heap: List[Tuple[float, int, int, State]] = [(h0, next(counter), 0, initial)]
        best_g: Dict[State, int] = {initial: 0}
        parent: Dict[State, Tuple[State, Action]] = {}
        expanded = 0
        goal: Optional[State] = None

        while heap:
            _, _, g, current = heapq.heappop(heap)
            if g > best_g.get(current, float("inf")):
                continue

            # Pop order is by f. manhattan_half never exceeds the optimal
            # remaining cost, and a cheaper g reopens the node, so this g
            # is optimal. The heuristic need not be consistent: a teleport
            # can cut h by more than the edge that caused it.
            if is_goal_state(current, stage):
                goal = current
                break

            expanded += 1
            for act in _CANDIDATE_ACTIONS:
                if act == Action.SWITCH_BLOCK and not current.is_split:
                    continue
                nxt = transition(current, act, stage)
                if nxt is None:
                    continue
                new_g = g + step_cost(stage, current, act, nxt)
                if new_g < best_g.get(nxt, float("inf")):
                    best_g[nxt] = new_g
                    parent[nxt] = (current, act)
                    f = new_g + self.heuristic(nxt, stage)
                    heapq.heappush(heap, (f, next(counter), new_g, nxt))

        if goal is None:
            return False, [], expanded

        path: List[Action] = []
        cursor = goal
        while cursor != initial:
            cursor, act = parent[cursor]
            path.append(act)
        path.reverse()
        return True, path, expanded
