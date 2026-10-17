"""Unit tests for BFS solver on Stage 01 and Stage 02."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import unittest
from bloxorz.config import STAGES_DIR

from bloxorz.engine.stage_loader import load_stage
from bloxorz.solvers.bfs import BFSSolver

class TestSolvers(unittest.TestCase):
    def test_bfs_stage_01(self):
        stage1 = load_stage(STAGES_DIR / "level_01_basic.json")
        solver = BFSSolver(stage1)
        res = solver.solve()
        self.assertTrue(res.found, "BFS should find a solution for Stage 01")
        self.assertEqual(res.solution_length, 7, "Stage 01 optimal length must be exactly 7")
        print(f"\n[PASS] Stage 01 solved in {res.solution_length} steps: {[a.value for a in res.actions]}")

    def test_bfs_stage_02(self):
        stage2 = load_stage(STAGES_DIR / "level_02_basic.json")
        solver = BFSSolver(stage2)
        res = solver.solve()
        self.assertTrue(res.found, "BFS should find a solution for Stage 02")
        self.assertEqual(res.solution_length, 17, "Stage 02 optimal length must be exactly 17")
        print(f"\n[PASS] Stage 02 solved in {res.solution_length} steps: {[a.value for a in res.actions]}")

if __name__ == "__main__":
    unittest.main()
