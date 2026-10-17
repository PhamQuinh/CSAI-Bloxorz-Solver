"""Unit tests for stage loader."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import unittest
from bloxorz.config import STAGES_DIR

from bloxorz.engine.stage_loader import load_stage

class TestStageLoader(unittest.TestCase):
    def test_load_stage_01(self):
        stage1_path = STAGES_DIR / "level_01_basic.json"
        stage = load_stage(stage1_path)
        self.assertEqual(stage.start_pos, (1, 1))
        self.assertEqual(stage.goal_pos, (4, 7))
        self.assertEqual(stage.rows, 6)
        self.assertEqual(len(stage.bridges), 0)

    def test_load_all_10_stages(self):
        for i in range(1, 11):
            pattern = f"level_{i:02d}_*.json"
            matches = list(STAGES_DIR.glob(pattern))
            self.assertEqual(len(matches), 1, f"Missing or duplicate stage file for level {i}")
            stage = load_stage(matches[0])
            self.assertIsNotNone(stage.start_pos)
            self.assertIsNotNone(stage.goal_pos)

if __name__ == "__main__":
    unittest.main()
