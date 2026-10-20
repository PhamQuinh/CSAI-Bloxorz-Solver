"""Loads and parses Bloxorz stage JSON files into domain Stage objects."""
import json
from pathlib import Path
from typing import Union, Dict, Tuple, List
from bloxorz.domain.models import Stage

def load_stage(file_path: Union[str, Path]) -> Stage:
    """Load and validate a stage JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Stage file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grid = [row for row in data["grid"]]
    rows = len(grid)
    cols = max(len(row) for row in grid) if rows > 0 else 0
    # Pad rows to uniform length
    grid = [row.ljust(cols, " ") for row in grid]

    VALID_TILES = {' ', '.', '-', 'S', 'H', 'O', 'X', 'B', 'b', 'T'}
    VALID_SWITCH_ACTIONS = {"on", "off", "swap"}

    start_pos = None
    goal_pos = None
    s_count = 0
    h_count = 0
    ch_B = set()
    ch_b = set()

    for r in range(rows):
        for c in range(cols):
            ch = grid[r][c]
            if ch not in VALID_TILES:
                raise ValueError(f"Stage {data.get('name')} contains invalid tile '{ch}' at ({r}, {c})")
            if ch == "S":
                s_count += 1
                start_pos = (r, c)
            elif ch == "H":
                h_count += 1
                goal_pos = (r, c)
            elif ch == "B":
                ch_B.add((r, c))
            elif ch == "b":
                ch_b.add((r, c))

    if s_count != 1:
        raise ValueError(f"Stage {data.get('name')} must have exactly one start position 'S', found {s_count}")
    if h_count != 1:
        raise ValueError(f"Stage {data.get('name')} must have exactly one goal position 'H', found {h_count}")

    raw_bridges = data.get("bridges", [])
    initial_bridges_list = [False] * len(raw_bridges)
    bridges = []
    declared_bridge_cells = set()

    for i, b in enumerate(raw_bridges):
        coords = [tuple(pos) for pos in b]
        for pr, pc in coords:
            if pr < 0 or pr >= rows or pc < 0 or pc >= cols:
                raise ValueError(f"Bridge group {i} contains out-of-bounds coordinates ({pr}, {pc})")
            declared_bridge_cells.add((pr, pc))
        bridges.append(coords)
        if coords and coords[0] in ch_B:
            initial_bridges_list[i] = True

    orphan_bridges = (ch_B | ch_b) - declared_bridge_cells
    if orphan_bridges:
        raise ValueError(f"Stage {data.get('name')} contains orphan bridge tiles not defined in bridges list: {orphan_bridges}")

    switches = {}
    for sw in data.get("switches", []):
        if len(sw) < 3:
            raise ValueError(f"Invalid switch configuration format: {sw}")
        r, c, actions = sw[0], sw[1], sw[2]
        if r < 0 or r >= rows or c < 0 or c >= cols:
            raise ValueError(f"Switch coordinates ({r}, {c}) out of bounds")
        if grid[r][c] not in ('O', 'X', 'T'):
            raise ValueError(f"Switch placed on invalid tile '{grid[r][c]}' at ({r}, {c})")
        parsed_actions = []
        for act in actions:
            if len(act) < 2:
                raise ValueError(f"Invalid switch action format: {act}")
            b_idx, b_action = act[0], act[1]
            if not (0 <= b_idx < len(raw_bridges)):
                raise ValueError(f"Switch at ({r}, {c}) references invalid bridge index {b_idx} (total bridges: {len(raw_bridges)})")
            if b_action not in VALID_SWITCH_ACTIONS:
                raise ValueError(f"Switch at ({r}, {c}) contains invalid action '{b_action}'")
            parsed_actions.append((b_idx, b_action))
        switches[(r, c)] = parsed_actions

    teleports = {}
    for tp in data.get("teleports", []):
        if len(tp) < 7:
            raise ValueError(f"Invalid teleport configuration format: {tp}")
        r, c, r1, c1, r2, c2, active = tp[0], tp[1], tp[2], tp[3], tp[4], tp[5], tp[6]
        if r < 0 or r >= rows or c < 0 or c >= cols:
            raise ValueError(f"Teleport switch ({r}, {c}) out of bounds")
        if grid[r][c] != 'T':
            raise ValueError(f"Teleport switch at ({r}, {c}) is not tile 'T', got '{grid[r][c]}'")
        for dest_r, dest_c in [(r1, c1), (r2, c2)]:
            if dest_r < 0 or dest_r >= rows or dest_c < 0 or dest_c >= cols:
                raise ValueError(f"Teleport destination ({dest_r}, {dest_c}) out of bounds")
            if grid[dest_r][dest_c] == ' ':
                raise ValueError(f"Teleport destination ({dest_r}, {dest_c}) cannot be void ' '")
        if active not in (0, 1):
            raise ValueError(f"Teleport active cube must be 0 or 1, got {active}")
        teleports[(r, c)] = (r1, c1, r2, c2, active)

    return Stage(
        name=data.get("name", path.stem),
        grid=grid,
        rows=rows,
        cols=cols,
        start_pos=start_pos,
        goal_pos=goal_pos,
        bridges=bridges,
        initial_bridges=tuple(initial_bridges_list),
        switches=switches,
        teleports=teleports,
        passcode=data.get("passcode", "")
    )
