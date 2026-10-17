"""Admissible and consistent heuristics for A* search.
Designed by TV3 - Algorithm Specialist 2.
"""
from bloxorz.domain.state import State
from bloxorz.domain.models import Stage

def manhattan_half(state: State, stage: Stage) -> float:
    """Lower bound: Manhattan distance divided by 2.
    Admissible since a single roll moves the block by at most 2 cells.
    """
    gr, gc = stage.goal_pos
    # Average position of the block
    avg_r = (state.r1 + state.r2) / 2.0
    avg_c = (state.c1 + state.c2) / 2.0
    dist = abs(avg_r - gr) + abs(avg_c - gc)
    return dist / 2.0

def manhattan_half_with_orientation_penalty(state: State, stage: Stage) -> float:
    """Manhattan / 2 plus orientation penalty.
    If the block is not standing, it must roll at least once more to stand on goal.
    """
    base = manhattan_half(state, stage)
    penalty = 0.0 if state.is_standing else 1.0
    return base + penalty
