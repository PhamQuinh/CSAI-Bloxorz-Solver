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

    def test_bfs_stage_04(self):
        stage4 = load_stage(STAGES_DIR / "level_04_fragile.json")
        solver = BFSSolver(stage4)
        res = solver.solve()
        self.assertTrue(res.found, "BFS should find a solution for Stage 04")
        self.assertEqual(res.solution_length, 28, "Stage 04 optimal length must be exactly 28")
        print(f"\n[PASS] Stage 04 solved in {res.solution_length} steps: {[a.value for a in res.actions]}")

    def test_bfs_stage_05(self):
        stage5 = load_stage(STAGES_DIR / "level_05_fragile.json")
        solver = BFSSolver(stage5)
        res = solver.solve()
        self.assertTrue(res.found, "BFS should find a solution for Stage 05")
        self.assertEqual(res.solution_length, 33, "Stage 05 optimal length must be exactly 33")
        print(f"\n[PASS] Stage 05 solved in {res.solution_length} steps: {[a.value for a in res.actions]}")


if __name__ == "__main__":
    unittest.main()

