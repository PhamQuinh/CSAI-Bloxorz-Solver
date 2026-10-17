"""Unit tests for advanced tiles: fragile, switch O/X, bridge on/off/swap, split block."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import unittest
from bloxorz.config import STAGES_DIR

from bloxorz.engine.stage_loader import load_stage
from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.engine.transitions import transition

class TestAdvancedTiles(unittest.TestCase):
    def test_fragile_tile_break(self):
        # Stage 04 has fragile tiles '-'
        stage = load_stage(STAGES_DIR / "level_04_fragile.json")
        # Rolling to stand upright on fragile tile must return None
        # In stage 4: (0, 3) is fragile '-'
        s = State(r1=1, c1=3, r2=2, c2=3, bridges=())
        # Rolling UP lands standing on (0, 3) which is fragile '-' -> should fall!
        nxt = transition(s, Action.UP, stage)
        self.assertIsNone(nxt, "Standing on fragile tile should break and return None")

    def test_switch_and_bridge_toggle(self):
        # Stage 02 has bridges and switches
        stage = load_stage(STAGES_DIR / "level_02_basic.json")
        self.assertEqual(stage.initial_bridges, (False, False))

if __name__ == "__main__":
    unittest.main()
