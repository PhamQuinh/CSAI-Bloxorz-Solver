"""Depth-First Search (DFS) Solver for Bloxorz.
Implemented by TV2. Iterative (explicit stack) with a visited set to avoid cycles.
Not optimal: the returned path may be much longer than the shortest one.
"""
import time
import tracemalloc
from typing import Dict, Tuple, Optional

from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.domain.rules import is_goal_state
from bloxorz.engine.transitions import transition
from bloxorz.solvers.base import BaseSolver, SearchResult


class DFSSolver(BaseSolver):
    """Iterative DFS with a global visited set (graph search)."""

    def solve(self) -> SearchResult:
        tracemalloc.start()
        start_time = time.perf_counter()

        sr, sc = self.stage.start_pos
        initial_state = State(
            r1=sr, c1=sc, r2=sr, c2=sc,
            bridges=self.stage.initial_bridges,
            active_cube=-1,
        )

        expanded_nodes = 0
        goal_state: Optional[State] = None
        parent_map: Dict[State, Tuple[State, Action]] = {}

        if is_goal_state(initial_state, self.stage):
            goal_state = initial_state
        else:
            stack = [initial_state]
            visited = {initial_state}
            # Đảo thứ tự vì stack là LIFO: UP sẽ được thử trước.
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

        elapsed = time.perf_counter() - start_time
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mb = peak_mem / (1024 * 1024)

        if goal_state is None:
            return SearchResult(found=False, search_time=elapsed,
                                peak_memory_mb=peak_mb, expanded_nodes=expanded_nodes)

        path = []
        curr = goal_state
        while curr != initial_state:
            prev_state, act = parent_map[curr]
            path.append(act)
            curr = prev_state
        path.reverse()

        return SearchResult(found=True, actions=path, solution_length=len(path),
                            search_time=elapsed, peak_memory_mb=peak_mb,
                            expanded_nodes=expanded_nodes)