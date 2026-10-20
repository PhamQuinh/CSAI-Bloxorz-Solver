"""Conceptual rules for Bloxorz victory, switch activation, and tile behavior."""
from bloxorz.domain.state import State
from bloxorz.domain.models import Stage, TileType

def is_goal_state(state: State, stage: Stage) -> bool:
    """Return True if block is standing upright on the goal hole."""
    if state.is_split:
        return False
    if state.is_standing:
        return (state.r1, state.c1) == stage.goal_pos
    return False

def can_activate_heavy_switch(state: State) -> bool:
    """Heavy switch (X) can only be activated by a standing 1x1x2 block."""
    return state.is_standing and (not state.is_split)

def can_activate_split_switch(state: State) -> bool:
    """Split switch (T) is activated only by a standing 1x1x2 block."""
    return state.is_standing and (not state.is_split)
