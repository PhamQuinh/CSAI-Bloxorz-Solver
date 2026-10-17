"""Immutable, hashable State representation for Bloxorz."""
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass(frozen=True)
class State:
    """Immutable state representation.
    
    Coordinates are stored in canonical row-major order:
    (r1, c1) and (r2, c2) where (r1, c1) <= (r2, c2).
    
    - Standing: r1 == r2 and c1 == c2
    - Lying Row (horizontal): r1 == r2 and c1 + 1 == c2
    - Lying Col (vertical): r1 + 1 == r2 and c1 == c2
    - Split: r1, c1 and r2, c2 are separated into two 1x1x1 cubes.
      active_cube in {0, 1} identifies which cube is currently controlled.
    """
    r1: int
    c1: int
    r2: int
    c2: int
    bridges: Tuple[bool, ...]
    active_cube: int = -1  # -1 means single 1x1x2 block, 0 or 1 means split state

    @property
    def is_standing(self) -> bool:
        return self.r1 == self.r2 and self.c1 == self.c2

    @property
    def is_split(self) -> bool:
        return self.active_cube != -1

    @property
    def is_lying_row(self) -> bool:
        return (not self.is_split) and (self.r1 == self.r2) and (self.c1 + 1 == self.c2)

    @property
    def is_lying_col(self) -> bool:
        return (not self.is_split) and (self.c1 == self.c2) and (self.r1 + 1 == self.r2)

    def cells(self) -> Tuple[Tuple[int, int], ...]:
        """Return distinct cells occupied by the block."""
        if self.is_standing:
            return ((self.r1, self.c1),)
        return ((self.r1, self.c1), (self.r2, self.c2))
