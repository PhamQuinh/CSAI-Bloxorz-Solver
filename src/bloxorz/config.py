"""System-wide configurations and constants for Bloxorz."""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGES_DIR = PROJECT_ROOT / "stages"
RESULTS_DIR = PROJECT_ROOT / "results"
DOCS_DIR = PROJECT_ROOT / "docs"

# Tile representations in stage maps
TILE_VOID = ' '
TILE_FLOOR = '.'
TILE_FRAGILE = '-'
TILE_START = 'S'
TILE_GOAL = 'H'
TILE_SOFT_SWITCH = 'O'
TILE_HEAVY_SWITCH = 'X'
TILE_BRIDGE_OPEN = 'B'
TILE_BRIDGE_CLOSED = 'b'
TILE_SPLIT = 'T'
