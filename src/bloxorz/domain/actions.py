"""Action definitions for Bloxorz."""
from enum import Enum

class Action(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    SWITCH_BLOCK = "SWITCH_BLOCK"  # Dùng khi khối bị split (tách thành 2 khối 1x1)
