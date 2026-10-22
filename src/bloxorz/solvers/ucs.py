"""Uniform-Cost Search (UCS) Solver with a NON-UNIFORM cost function.
Implemented by TV2. The cost model lives in solvers/costs.py:
  switch / split / SWITCH_BLOCK = 1, whole block on fragile = 4, other roll = 2.
Measurement scope matches BFS/A*: search + path reconstruction.
"""
import heapq
import itertools
from typing import Dict, Tuple, Optional, List

from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.domain.rules import is_goal_state
from bloxorz.engine.transitions import transition
from bloxorz.metrics.measurement import measure_performance
from bloxorz.solvers.base import BaseSolver, SearchResult
from bloxorz.solvers.costs import step_cost


class UCSSolver(BaseSolver):
    """UCS with a priority queue and lazy deletion of stale entries."""

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

        counter = itertools.count()  # tie-breaker: never compare State objects
        heap = [(0, next(counter), initial_state)]
        best_g: Dict[State, int] = {initial_state: 0}
        parent_map: Dict[State, Tuple[State, Action]] = {}
        expanded_nodes = 0
        goal_state: Optional[State] = None

        candidate_actions = [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT,
                             Action.SWITCH_BLOCK]

        while heap:
            g, _, current = heapq.heappop(heap)
            if g > best_g.get(current, float("inf")):
                continue  # stale entry

            # Goal test at POP time -> guarantees optimality
            if is_goal_state(current, self.stage):
                goal_state = current
                break

            expanded_nodes += 1
            for act in candidate_actions:
                if act == Action.SWITCH_BLOCK and not current.is_split:
                    continue
                nxt = transition(current, act, self.stage)
                if nxt is None:
                    continue
                new_g = g + step_cost(self.stage, current, act, nxt)
                if new_g < best_g.get(nxt, float("inf")):
                    best_g[nxt] = new_g
                    parent_map[nxt] = (current, act)
                    heapq.heappush(heap, (new_g, next(counter), nxt))

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
        return True, path, expanded_nodes
