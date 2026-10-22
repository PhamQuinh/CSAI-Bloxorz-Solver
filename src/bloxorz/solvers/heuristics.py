"""Heuristics for A* under step_cost in costs.py.

manhattan_half is a lower bound on the remaining cost, including paths
that use a split-switch teleport. manhattan_half_with_orientation_penalty
adds an extra minimum step when the block is not standing; that extra
term can exceed the true remaining cost, so A* does not use it.
"""
from functools import lru_cache

from bloxorz.domain.models import Stage
from bloxorz.domain.state import State
from bloxorz.solvers.costs import MIN_STEP_COST

# One roll changes the block center by at most 1.5 cells. Dividing by 2
# stays at or below the number of non-teleport moves.
MAX_CELLS_PER_ROLL = 2


def _center(state: State) -> tuple:
    return ((state.r1 + state.r2) / 2.0, (state.c1 + state.c2) / 2.0)


def center_manhattan(state: State, goal: tuple) -> float:
    """Manhattan distance from the block center to a target cell."""
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


def _roll_lower_bound(state: State, target: tuple) -> float:
    """Lower bound on step_cost to reach target with no teleport in between.

    The block must be whole to stand on a goal or a split switch, so a
    split block needs at least steps_to_merge moves. Those moves are the
    same ones that carry the center, so the bound is the max, not the sum.
    Every move costs at least MIN_STEP_COST, and without a teleport the
    center closes at most MAX_CELLS_PER_ROLL cells per move.
    """
    steps = max(
        center_manhattan(state, target) / MAX_CELLS_PER_ROLL,
        float(steps_to_merge(state)),
    )
    return MIN_STEP_COST * steps


def _landing_state(dest: tuple) -> State:
    """Block position after standing on a split switch, including auto-merge."""
    r1, c1, r2, c2, active = dest
    if not (r1 < r2 or (r1 == r2 and c1 <= c2)):
        r1, c1, r2, c2 = r2, c2, r1, c1
        active = 1 - active
    if active != -1 and abs(r1 - r2) + abs(c1 - c2) == 1:
        active = -1
    return State(r1=r1, c1=c1, r2=r2, c2=c2, bridges=(), active_cube=active)


@lru_cache(maxsize=32)
def _landing_lower_bounds(goal: tuple, portals: tuple) -> tuple:
    """Shortest-path lower bounds from each teleport landing to the goal.

    portals is a sorted tuple of (switch_cell, destination). Node i is the
    landing of switch i. An edge i -> goal weighs the no-teleport bound.
    An edge i -> j weighs the no-teleport bound from landing i to switch j,
    which already includes the move that arrives at landing j.
    """
    cells = []
    landings = []
    for cell, dest in portals:
        cells.append(cell)
        landings.append(_landing_state(dest))
    count = len(landings)
    bound = [_roll_lower_bound(landings[i], goal) for i in range(count)]
    for _ in range(count):
        changed = False
        for i in range(count):
            for j in range(count):
                via = _roll_lower_bound(landings[i], cells[j]) + bound[j]
                if via < bound[i]:
                    bound[i] = via
                    changed = True
        if not changed:
            break
    return tuple(bound)


def _portal_key(stage: Stage) -> tuple:
    return (
        stage.goal_pos,
        tuple(sorted(
            (cell, tuple(dest)) for cell, dest in stage.teleports.items()
        )),
    )


def manhattan_half(state: State, stage: Stage) -> float:
    """Lower bound on the remaining step_cost from state to the goal.

    h(s) = min(roll(s, goal), min over switches j of roll(s, j) + H(landing j)).
    roll is _roll_lower_bound. H(landing j) is the portal-graph distance
    from that landing to the goal, so a later teleport is included.

    Why h(s) is at most the optimal remaining cost:
    Every action costs at least MIN_STEP_COST. Split a minimum-cost path
    at the teleports it uses.

    - If it never stands on a split switch, every move shifts the center
      by at most 1.5 cells and a split block must merge before it can
      stand on the hole. The cost is therefore at least roll(s, goal).
    - If its first teleport is switch j, the moves before that landing
      do not teleport. Reaching the switch (the same move that lands)
      costs at least roll(s, j). The suffix starts at landing j, and the
      same argument on the portal graph gives a suffix cost of at least
      H(landing j), by induction on the number of teleports left. Each
      teleport edge weighs at least MIN_STEP_COST, so an optimal suffix
      does not loop.

    h takes the minimum of these cases, so it stays under every one of
    them. The bound ignores walls and bridges; those only add cost.

    A teleport can drop h by more than the cost of that edge, so h is not
    claimed to be consistent. A* reopens a node when g improves, which is
    what keeps the first dequeued goal optimal.
    """
    best = _roll_lower_bound(state, stage.goal_pos)
    if not stage.teleports:
        return best
    _, portals = _portal_key(stage)
    bounds = _landing_lower_bounds(stage.goal_pos, portals)
    for (cell, _), after in zip(portals, bounds):
        via = _roll_lower_bound(state, cell) + after
        if via < best:
            best = via
    return best


def _needs_orientation_roll(state: State) -> bool:
    """The hole accepts only a standing 1x1x2 block, not a lying or split one."""
    return state.is_split or not state.is_standing


def manhattan_half_with_orientation_penalty(state: State, stage: Stage) -> float:
    """manhattan_half plus MIN_STEP_COST when the block is not standing.

    The roll that stands the block on the hole is already partly counted
    inside manhattan_half. On an edge that costs only MIN_STEP_COST, adding
    another MIN_STEP_COST can exceed the remaining cost. A* does not use
    this function.
    """
    base = manhattan_half(state, stage)
    if not _needs_orientation_roll(state):
        return base
    return base + float(MIN_STEP_COST)
