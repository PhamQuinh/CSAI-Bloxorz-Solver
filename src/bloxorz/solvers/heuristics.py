"""Two A* heuristics, admissible under step_cost in costs.py.

h1: Manhattan distance of the block center divided by 2, scaled by
    MIN_STEP_COST, and raised to the number of moves needed to rejoin a
    split block.
h2: h1 plus MIN_STEP_COST when the block is not standing on one cell.
"""
from bloxorz.domain.models import Stage
from bloxorz.domain.state import State
from bloxorz.solvers.costs import MIN_STEP_COST

# One roll changes the block position by at most 2 cells (SPEC). The center
# actually shifts by at most 1.5, so dividing by 2 stays below the true cost.
MAX_CELLS_PER_ROLL = 2


def _center(state: State) -> tuple:
    return ((state.r1 + state.r2) / 2.0, (state.c1 + state.c2) / 2.0)


def center_manhattan(state: State, goal: tuple) -> float:
    """Manhattan distance from the block center to the goal hole."""
    row, col = _center(state)
    return abs(row - goal[0]) + abs(col - goal[1])


def steps_to_merge(state: State) -> int:
    """Minimum moves until two 1x1 cubes stand adjacent and merge.

    A whole block needs 0. Two split cubes that are d cells apart need at
    least d - 1 moves: each move pulls one cube by 1 cell, and they merge
    when d = 1.
    """
    if not state.is_split:
        return 0
    apart = abs(state.r1 - state.r2) + abs(state.c1 - state.c2)
    return max(0, apart - 1)


def _roll_steps(state: State, goal: tuple) -> float:
    return center_manhattan(state, goal) / MAX_CELLS_PER_ROLL


def manhattan_half(state: State, stage: Stage) -> float:
    """h1(s) = MIN_STEP_COST * max(d / 2, moves to merge).

    Admissible. Every path of L moves satisfies L >= d / 2, because one
    move brings the center at most 2 cells closer to the goal. A split
    block also satisfies L >= moves to merge. Those moves are the same
    moves, so the bound is the max, not the sum. step_cost is always
    >= MIN_STEP_COST, so the optimal cost is >= h1(s).

    Consistent on non-teleport edges. d / 2 changes by at most 0.75 and
    the merge count changes by at most 1, so h1 changes by at most
    MIN_STEP_COST, which does not exceed that edge's step_cost.
    """
    goal = stage.goal_pos
    step_bound = max(_roll_steps(state, goal), float(steps_to_merge(state)))
    return MIN_STEP_COST * step_bound


def _needs_orientation_roll(state: State) -> bool:
    """The hole accepts only a standing 1x1x2 block, not a lying or split one."""
    return state.is_split or not state.is_standing


def manhattan_half_with_orientation_penalty(state: State, stage: Stage) -> float:
    """h2(s) = h1(s) + MIN_STEP_COST when the block is not standing, else h1(s).

    A lying or split block cannot fall into the hole, so at least one more
    roll remains and that roll costs >= MIN_STEP_COST. This is tighter than
    h1 when h1 is small. The roll that stands the block on the hole is
    already partly counted inside h1, so h2 is not the default: on an edge
    that costs only MIN_STEP_COST, adding another MIN_STEP_COST can exceed
    the remaining cost. A* uses h1.
    """
    base = manhattan_half(state, stage)
    if not _needs_orientation_roll(state):
        return base
    return base + float(MIN_STEP_COST)
