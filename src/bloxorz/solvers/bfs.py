"""Breadth-First Search (BFS) Solver for Bloxorz.
Implemented by TV1 (Leader) - System Architect.
Guarantees finding the optimal (shortest path) solution in unweighted state space.
"""
from collections import deque
from typing import Dict, Tuple, Optional, List

from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.domain.rules import is_goal_state
from bloxorz.engine.transitions import transition
from bloxorz.metrics.measurement import measure_performance
from bloxorz.solvers.base import BaseSolver, SearchResult


class BFSSolver(BaseSolver):
    """Breadth-First Search solver using queue and hash-set for cycle detection."""

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
            expanded_nodes=measured["expanded_nodes"]
        )

    def _search(self) -> Tuple[bool, List[Action], int]:
        sr, sc = self.stage.start_pos
        initial_state = State(
            r1=sr, c1=sc,
            r2=sr, c2=sc,
            bridges=self.stage.initial_bridges,
            active_cube=-1
        )

        if is_goal_state(initial_state, self.stage):
            return True, [], 0

        queue = deque([initial_state])
        visited = {initial_state}
        parent_map: Dict[State, Tuple[State, Action]] = {}
        expanded_nodes = 0
        goal_state: Optional[State] = None

        candidate_actions = [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT, Action.SWITCH_BLOCK]

        while queue:
            current = queue.popleft()
            expanded_nodes += 1

            for act in candidate_actions:
                if act == Action.SWITCH_BLOCK and not current.is_split:
                    continue

                nxt = transition(current, act, self.stage)
                if nxt is not None and nxt not in visited:
                    visited.add(nxt)
                    parent_map[nxt] = (current, act)

                    if is_goal_state(nxt, self.stage):
                        goal_state = nxt
                        break

                    queue.append(nxt)

            if goal_state is not None:
                break

        if goal_state is None:
            return False, [], expanded_nodes

        # Reconstruct path
        path = []
        curr = goal_state
        while curr in parent_map:
            prev_state, act = parent_map[curr]
            path.append(act)
            curr = prev_state
        path.reverse()

        return True, path, expanded_nodes
