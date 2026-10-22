"""Shared non-uniform cost model for UCS and A*."""
from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.domain.models import Stage, TileType

COST_NORMAL = 2
COST_FRAGILE = 4         # whole (non-split) block lying on a fragile tile 
COST_SWITCH = 1          # press a switch / enter a split tile
COST_SWITCH_BLOCK = 1    # change controlled cube
MIN_STEP_COST = min(COST_NORMAL, COST_FRAGILE, COST_SWITCH, COST_SWITCH_BLOCK)

_FRAGILE = TileType.FRAGILE.value


def is_fragile(stage: Stage, r: int, c: int) -> bool:
    return 0 <= r < stage.rows and 0 <= c < stage.cols and stage.grid[r][c] == _FRAGILE


def step_cost(stage: Stage, cur: State, act: Action, nxt: State) -> int:
    """Non-uniform cost of cur --act--> nxt. Always >= 1."""
    if act == Action.SWITCH_BLOCK:
        return COST_SWITCH_BLOCK
    if nxt.bridges != cur.bridges or (nxt.is_split and not cur.is_split):
        return COST_SWITCH
    if not nxt.is_split and (is_fragile(stage, nxt.r1, nxt.c1) or is_fragile(stage, nxt.r2, nxt.c2)):
        return COST_FRAGILE
    return COST_NORMAL