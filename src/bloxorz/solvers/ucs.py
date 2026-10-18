"""Uniform-Cost Search (UCS) Solver with a NON-UNIFORM cost function.
Implemented by TV2. The cost model lives in solvers/costs.py:
  switch / split / SWITCH_BLOCK = 1, normal roll = 2, roll onto fragile = 4.
"""
import heapq
import itertools
import time
import tracemalloc
from typing import Dict, Tuple, Optional

from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.domain.rules import is_goal_state
from bloxorz.engine.transitions import transition
from bloxorz.solvers.base import BaseSolver, SearchResult
from bloxorz.solvers.costs import step_cost


class UCSSolver(BaseSolver):
    """UCS with a priority queue and lazy deletion of stale entries."""

    def solve(self) -> SearchResult:
        tracemalloc.start()
        start_time = time.perf_counter()

        sr, sc = self.stage.start_pos
        initial_state = State(
            r1=sr, c1=sc, r2=sr, c2=sc,
            bridges=self.stage.initial_bridges,
            active_cube=-1,
        )

        counter = itertools.count()  # tie-breaker, tránh so sánh State
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
                continue  # entry cũ

            # Kiểm tra goal khi POP => đảm bảo tối ưu
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