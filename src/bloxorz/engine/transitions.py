"""Transitions module: Single source of truth for block movement and state changes.
Both GUI and all Solvers must use this module exclusively.
"""
from typing import Optional, List, Tuple
from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.domain.models import Stage
from bloxorz.engine.validation import is_valid_position, is_valid_cube_position

def get_valid_actions(state: State, stage: Stage) -> List[Action]:
    """Return all valid actions from current state."""
    actions = []
    candidates = [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]
    if state.is_split:
        candidates.append(Action.SWITCH_BLOCK)

    for act in candidates:
        nxt = transition(state, act, stage)
        if nxt is not None:
            actions.append(act)
    return actions

def transition(state: State, action: Action, stage: Stage) -> Optional[State]:
    """Compute successor state after taking an action.
    Returns None if action leads to an invalid state (falling, out of bounds, broken tile).
    """
    if action == Action.SWITCH_BLOCK:
        if not state.is_split:
            return None
        # Switch active cube (0 -> 1, 1 -> 0)
        return State(
            r1=state.r1, c1=state.c1,
            r2=state.r2, c2=state.c2,
            bridges=state.bridges,
            active_cube=1 if state.active_cube == 0 else 0
        )

    r1, c1, r2, c2 = state.r1, state.c1, state.r2, state.c2
    bridges = list(state.bridges)
    active_cube = state.active_cube

    if not state.is_split:
        # Standard 1x1x2 block
        if state.is_standing:
            if action == Action.UP:
                nr1, nc1, nr2, nc2 = r1 - 2, c1, r1 - 1, c1
            elif action == Action.DOWN:
                nr1, nc1, nr2, nc2 = r1 + 1, c1, r1 + 2, c1
            elif action == Action.LEFT:
                nr1, nc1, nr2, nc2 = r1, c1 - 2, r1, c1 - 1
            elif action == Action.RIGHT:
                nr1, nc1, nr2, nc2 = r1, c1 + 1, r1, c1 + 2
            else:
                return None
        elif state.is_lying_row:
            # r1 == r2 and c1 + 1 == c2
            if action == Action.UP:
                nr1, nc1, nr2, nc2 = r1 - 1, c1, r2 - 1, c2
            elif action == Action.DOWN:
                nr1, nc1, nr2, nc2 = r1 + 1, c1, r2 + 1, c2
            elif action == Action.LEFT:
                nr1, nc1, nr2, nc2 = r1, c1 - 1, r1, c1 - 1
            elif action == Action.RIGHT:
                nr1, nc1, nr2, nc2 = r1, c2 + 1, r1, c2 + 1
            else:
                return None
        elif state.is_lying_col:
            # c1 == c2 and r1 + 1 == r2
            if action == Action.UP:
                nr1, nc1, nr2, nc2 = r1 - 1, c1, r1 - 1, c1
            elif action == Action.DOWN:
                nr1, nc1, nr2, nc2 = r2 + 1, c1, r2 + 1, c1
            elif action == Action.LEFT:
                nr1, nc1, nr2, nc2 = r1, c1 - 1, r2, c2 - 1
            elif action == Action.RIGHT:
                nr1, nc1, nr2, nc2 = r1, c1 + 1, r2, c2 + 1
            else:
                return None
        else:
            return None
    else:
        # Split block: move currently active cube
        dr, dc = 0, 0
        if action == Action.UP: dr = -1
        elif action == Action.DOWN: dr = 1
        elif action == Action.LEFT: dc = -1
        elif action == Action.RIGHT: dc = 1
        else: return None

        if active_cube == 0:
            mr1, mc1 = r1 + dr, c1 + dc
            mr2, mc2 = r2, c2
        else:
            mr1, mc1 = r1, c1
            mr2, mc2 = r2 + dr, c2 + dc

        # Maintain canonical row-major order
        if mr1 < mr2 or (mr1 == mr2 and mc1 <= mc2):
            nr1, nc1, nr2, nc2 = mr1, mc1, mr2, mc2
            new_active = active_cube
        else:
            nr1, nc1, nr2, nc2 = mr2, mc2, mr1, mc1
            new_active = 1 - active_cube
        active_cube = new_active

    # Check validity of destination
    is_split_state = (active_cube != -1)
    if not is_valid_position(nr1, nc1, nr2, nc2, tuple(bridges), stage, is_split=is_split_state):
        return None

    # Handle switches and triggers
    new_bridges = bridges[:]
    bridge_actions = []

    if not state.is_split:
        # Block was a whole 1x1x2 block
        if nr1 == nr2 and nc1 == nc2:
            # Block lands Standing
            stand_pos = (nr1, nc1)

            # 1. Source switch trigger (Heavy 'X', Soft 'O', or Switch on 'T')
            if stand_pos in stage.switches:
                bridge_actions.extend(stage.switches[stand_pos])

            # Apply source switch triggers before potential teleport
            for b_idx, act in bridge_actions:
                if act == "on":
                    new_bridges[b_idx] = True
                elif act == "off":
                    new_bridges[b_idx] = False
                elif act == "swap":
                    new_bridges[b_idx] = not new_bridges[b_idx]
            bridge_actions.clear()

            # 2. Teleport / Split switch trigger
            if stand_pos in stage.teleports:
                tp = stage.teleports[stand_pos]
                tr1, tc1, tr2, tc2, t_active = tp
                # Canonical ordering
                if tr1 < tr2 or (tr1 == tr2 and tc1 <= tc2):
                    nr1, nc1, nr2, nc2 = tr1, tc1, tr2, tc2
                    active_cube = t_active
                else:
                    nr1, nc1, nr2, nc2 = tr2, tc2, tr1, tc1
                    active_cube = 1 - t_active

                # Immediately validate both teleport destinations!
                if not is_valid_cube_position(nr1, nc1, tuple(new_bridges), stage) or \
                   not is_valid_cube_position(nr2, nc2, tuple(new_bridges), stage):
                    return None  # Teleported into void, out-of-bounds, or closed bridge

                # Symmetrically process Soft switches 'O' at both destination tiles
                for dest_r, dest_c in [(nr1, nc1), (nr2, nc2)]:
                    if (dest_r, dest_c) in stage.switches and stage.grid[dest_r][dest_c] == 'O':
                        bridge_actions.extend(stage.switches[(dest_r, dest_c)])
        else:
            # Block lands Lying: only Soft switches 'O' trigger if newly stepped on
            if (nr1, nc1) in stage.switches and stage.grid[nr1][nc1] == 'O' and (nr1, nc1) not in [(r1, c1), (r2, c2)]:
                bridge_actions.extend(stage.switches[(nr1, nc1)])
            if (nr2, nc2) in stage.switches and stage.grid[nr2][nc2] == 'O' and (nr2, nc2) not in [(r1, c1), (r2, c2)]:
                bridge_actions.extend(stage.switches[(nr2, nc2)])
    else:
        # Block was split: only the moved cube can trigger a Soft switch 'O'
        moved_pos = (mr1, mc1) if state.active_cube == 0 else (mr2, mc2)
        if moved_pos in stage.switches and stage.grid[moved_pos[0]][moved_pos[1]] == 'O':
            bridge_actions.extend(stage.switches[moved_pos])

    # Apply remaining bridge state modifications
    for b_idx, act in bridge_actions:
        if act == "on":
            new_bridges[b_idx] = True
        elif act == "off":
            new_bridges[b_idx] = False
        elif act == "swap":
            new_bridges[b_idx] = not new_bridges[b_idx]

    # Re-merge check: if split cubes are Manhattan distance 1 apart, they merge back into 1x1x2 block!
    if active_cube != -1:
        if abs(nr1 - nr2) + abs(nc1 - nc2) == 1:
            active_cube = -1  # Merged!

    # Final support check: verify cubes/block don't stand on bridge closed by switch
    final_is_split = (active_cube != -1)
    if not is_valid_position(nr1, nc1, nr2, nc2, tuple(new_bridges), stage, is_split=final_is_split):
        return None

    return State(
        r1=nr1, c1=nc1,
        r2=nr2, c2=nc2,
        bridges=tuple(new_bridges),
        active_cube=active_cube
    )
