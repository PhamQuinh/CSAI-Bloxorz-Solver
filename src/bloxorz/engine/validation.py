"""State and move validation logic for Bloxorz."""
from bloxorz.domain.state import State
from bloxorz.domain.models import Stage

def is_valid_position(r1: int, c1: int, r2: int, c2: int, bridges: tuple, stage: Stage) -> bool:
    """Check if the given block position is supported and within board bounds."""
    # Bounds check
    if r1 < 0 or r1 >= stage.rows or c1 < 0 or c1 >= stage.cols:
        return False
    if r2 < 0 or r2 >= stage.rows or c2 < 0 or c2 >= stage.cols:
        return False

    cell1 = stage.grid[r1][c1]
    cell2 = stage.grid[r2][c2]

    # Void check
    if cell1 == ' ' or cell2 == ' ':
        return False

    # Bridge check
    for r, c, cell in [(r1, c1, cell1), (r2, c2, cell2)]:
        if cell in ('B', 'b'):
            # Find which bridge this cell belongs to
            bridge_idx = None
            for idx, b_cells in enumerate(stage.bridges):
                if (r, c) in b_cells:
                    bridge_idx = idx
                    break
            if bridge_idx is not None and not bridges[bridge_idx]:
                return False  # Bridge is closed -> void

    # Fragile tile check: standing upright on fragile tile breaks and falls
    if r1 == r2 and c1 == c2 and cell1 == '-':
        return False

    return True
