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

    start_pos = None
    goal_pos = None
    ch_B = set()
    ch_b = set()

    for r in range(rows):
        for c in range(cols):
            ch = grid[r][c]
            if ch == "S":
                start_pos = (r, c)
            elif ch == "H":
                goal_pos = (r, c)
            elif ch == "B":
                ch_B.add((r, c))
            elif ch == "b":
                ch_b.add((r, c))

    if start_pos is None:
        raise ValueError(f"Stage {data.get('name')} missing start position 'S'")
    if goal_pos is None:
        raise ValueError(f"Stage {data.get('name')} missing goal position 'H'")

    raw_bridges = data.get("bridges", [])
    initial_bridges_list = [False] * len(raw_bridges)
    bridges = []

    for i, b in enumerate(raw_bridges):
        coords = [tuple(pos) for pos in b]
        bridges.append(coords)
        if coords and coords[0] in ch_B:
            initial_bridges_list[i] = True

    switches = {}
    for sw in data.get("switches", []):
        r, c, actions = sw[0], sw[1], sw[2]
        switches[(r, c)] = [(act[0], act[1]) for act in actions]

    teleports = {}
    for tp in data.get("teleports", []):
        r, c, r1, c1, r2, c2, active = tp[0], tp[1], tp[2], tp[3], tp[4], tp[5], tp[6]
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
