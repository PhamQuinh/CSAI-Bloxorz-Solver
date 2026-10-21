"""Depth-First Search (DFS) Solver for Bloxorz.
Implemented by TV2. Iterative (explicit stack) with a visited set to avoid cycles.
Not optimal: the returned path may be much longer than the shortest one.
Measurement scope matches BFS/A*: search + path reconstruction.
"""
from typing import Dict, Tuple, Optional, List

from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.domain.rules import is_goal_state
from bloxorz.engine.transitions import transition
from bloxorz.metrics.measurement import measure_performance
from bloxorz.solvers.base import BaseSolver, SearchResult


class DFSSolver(BaseSolver):
    """Iterative DFS with a global visited set (graph search)."""

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
        sr, sc = self.stage.start_pos
        initial_state = State(
            r1=sr, c1=sc, r2=sr, c2=sc,
            bridges=self.stage.initial_bridges,
            active_cube=-1,
        )

        if is_goal_state(initial_state, self.stage):
            return True, [], 0

        stack = [initial_state]
        visited = {initial_state}
        parent_map: Dict[State, Tuple[State, Action]] = {}
        expanded_nodes = 0
        goal_state: Optional[State] = None

        # Reversed because the stack is LIFO: UP is explored first.
        candidate_actions = [Action.SWITCH_BLOCK, Action.RIGHT, Action.LEFT,
                             Action.DOWN, Action.UP]

        while stack and goal_state is None:
            current = stack.pop()
            expanded_nodes += 1

            for act in candidate_actions:
                if act == Action.SWITCH_BLOCK and not current.is_split:
                    continue
                nxt = transition(current, act, self.stage)
                if nxt is None or nxt in visited:
                    continue
                visited.add(nxt)
                parent_map[nxt] = (current, act)
                if is_goal_state(nxt, self.stage):
                    goal_state = nxt
                    break
                stack.append(nxt)

        if goal_state is None:
            return False, [], expanded_nodes

        # Reconstruct path
        path: List[Action] = []
        curr = goal_state
        while curr != initial_state:
            prev_state, act = parent_map[curr]
            path.append(act)
            curr = prev_state
        path.reverse()

        return True, path, expanded_nodes