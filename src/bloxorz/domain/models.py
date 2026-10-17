"""Core domain models for Bloxorz stages, tiles, and switches."""
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Dict, Any

class TileType(str, Enum):
    VOID = ' '
    FLOOR = '.'
    FRAGILE = '-'
    START = 'S'
    GOAL = 'H'
    SOFT_SWITCH = 'O'
    HEAVY_SWITCH = 'X'
    BRIDGE_OPEN = 'B'
    BRIDGE_CLOSED = 'b'
    SPLIT = 'T'

class SwitchAction(str, Enum):
    SWAP = "swap"
    ON = "on"
    OFF = "off"

@dataclass(frozen=True)
class SwitchTrigger:
    bridge_index: int
    action: SwitchAction

@dataclass(frozen=True)
class Switch:
    r: int
    c: int
    triggers: Tuple[SwitchTrigger, ...]

@dataclass(frozen=True)
class Teleport:
    r: int
    c: int
    r1: int
    c1: int
    r2: int
    c2: int
    active_block: int

@dataclass
class Stage:
    name: str
    grid: List[str]
    rows: int
    cols: int
    start_pos: Tuple[int, int]
    goal_pos: Tuple[int, int]
    bridges: List[List[Tuple[int, int]]]
    initial_bridges: Tuple[bool, ...]
    switches: Dict[Tuple[int, int], List[Tuple[int, str]]]
    teleports: Dict[Tuple[int, int], Tuple[int, int, int, int, int]]
    passcode: str = ""
