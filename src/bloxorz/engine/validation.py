"""State and move validation logic for Bloxorz."""
from bloxorz.domain.state import State
from bloxorz.domain.models import Stage

def is_valid_cube_position(r: int, c: int, bridges: tuple, stage: Stage) -> bool:
    """Check if a single 1x1x1 cube position is supported and within board bounds."""
    # Bounds check
    if r < 0 or r >= stage.rows or c < 0 or c >= stage.cols:
        return False

    cell = stage.grid[r][c]

    # Void check
    if cell == ' ':
        return False

    # Bridge check
    if cell in ('B', 'b'):
        bridge_idx = None
        for idx, b_cells in enumerate(stage.bridges):
            if (r, c) in b_cells:
                bridge_idx = idx
                break
        # If bridge tile is orphan (not defined in stage.bridges) or bridge is closed -> void
        if bridge_idx is None or not bridges[bridge_idx]:
            return False

    # A single 1x1x1 cube does not break fragile tile '-'
    return True

def is_valid_position(r1: int, c1: int, r2: int, c2: int, bridges: tuple, stage: Stage, is_split: bool = False) -> bool:
    """Check if the given block position is supported and within board bounds."""
    if not is_valid_cube_position(r1, c1, bridges, stage):
        return False
    if not is_valid_cube_position(r2, c2, bridges, stage):
        return False

    # Fragile tile check: whole block standing upright on fragile tile breaks and falls
    if not is_split and r1 == r2 and c1 == c2 and stage.grid[r1][c1] == '-':
        return False

    return True
