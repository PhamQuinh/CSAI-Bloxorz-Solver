"""Breadth-First Search (BFS) Solver for Bloxorz.
Implemented by TV1 (Leader) - System Architect.
Guarantees finding the optimal (shortest path) solution in unweighted state space.
"""
import time
import tracemalloc
from collections import deque
from typing import Dict, Tuple, Optional

from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.domain.rules import is_goal_state
from bloxorz.engine.transitions import transition
from bloxorz.solvers.base import BaseSolver, SearchResult

class BFSSolver(BaseSolver):
    """Breadth-First Search solver using queue and hash-set for cycle detection."""

    def solve(self) -> SearchResult:
        # Start measurements
        tracemalloc.start()
        start_time = time.perf_counter()

        # Initial state setup
        sr, sc = self.stage.start_pos
        initial_state = State(
            r1=sr, c1=sc,
            r2=sr, c2=sc,
            bridges=self.stage.initial_bridges,
            active_cube=-1
        )

        # Early goal check
        if is_goal_state(initial_state, self.stage):
            elapsed = time.perf_counter() - start_time
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return SearchResult(
                found=True,
                actions=[],
                solution_length=0,
                search_time=elapsed,
                peak_memory_mb=peak_mem / (1024 * 1024),
                expanded_nodes=0
            )

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
                # If block is not split, don't attempt SWITCH_BLOCK
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

        elapsed = time.perf_counter() - start_time
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if goal_state is None:
            return SearchResult(
                found=False,
                actions=[],
                solution_length=0,
                search_time=elapsed,
                peak_memory_mb=peak_mem / (1024 * 1024),
                expanded_nodes=expanded_nodes
            )

        # Reconstruct path
        path = []
        curr = goal_state
        while curr in parent_map:
            prev_state, act = parent_map[curr]
            path.append(act)
            curr = prev_state
        path.reverse()

        return SearchResult(
            found=True,
            actions=path,
            solution_length=len(path),
            search_time=elapsed,
            peak_memory_mb=peak_mem / (1024 * 1024),
            expanded_nodes=expanded_nodes
        )
