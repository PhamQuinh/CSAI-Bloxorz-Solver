"""Unit tests for DFS and UCS solvers (TV2)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import json
import tempfile
import unittest

from bloxorz.config import STAGES_DIR
from bloxorz.domain.state import State
from bloxorz.domain.rules import is_goal_state
from bloxorz.engine.stage_loader import load_stage
from bloxorz.engine.transitions import transition
from bloxorz.solvers.bfs import BFSSolver
from bloxorz.solvers.dfs import DFSSolver
from bloxorz.solvers.ucs import UCSSolver
from bloxorz.solvers.costs import step_cost, MIN_STEP_COST

STAGE_FILES = sorted(Path(STAGES_DIR).glob("*.json"))


def replay(stage, actions):
    """Replay actions on the real engine; return (total_cost, final_state)."""
    sr, sc = stage.start_pos
    s = State(r1=sr, c1=sc, r2=sr, c2=sc,
              bridges=stage.initial_bridges, active_cube=-1)
    total = 0
    for a in actions:
        n = transition(s, a, stage)
        assert n is not None, f"illegal move {a} in solution"
        total += step_cost(stage, s, a, n)
        s = n
    return total, s


class TestDFSUCS(unittest.TestCase):
    def test_solutions_are_valid_on_all_stages(self):
        for path in STAGE_FILES:
            with self.subTest(stage=path.name):
                stage = load_stage(path)
                bfs = BFSSolver(stage).solve()
                for cls in (DFSSolver, UCSSolver):
                    res = cls(stage).solve()
                    self.assertEqual(res.found, bfs.found)
                    if res.found:
                        _, final = replay(stage, res.actions)
                        self.assertTrue(is_goal_state(final, stage))
                        self.assertEqual(res.solution_length, len(res.actions))
                        self.assertGreaterEqual(res.solution_length, bfs.solution_length)

    def test_ucs_cost_is_minimal_on_all_stages(self):
        for path in STAGE_FILES:
            with self.subTest(stage=path.name):
                stage = load_stage(path)
                ucs_cost, _ = replay(stage, UCSSolver(stage).solve().actions)
                bfs_cost, _ = replay(stage, BFSSolver(stage).solve().actions)
                dfs_cost, _ = replay(stage, DFSSolver(stage).solve().actions)
                self.assertLessEqual(ucs_cost, bfs_cost)
                self.assertLessEqual(ucs_cost, dfs_cost)

    def test_ucs_known_values(self):
        # (stage file, expected length, expected optimal cost) from compare.py
        cases = [("level_01_basic.json", 7, 14),
                 ("level_02_basic.json", 17, 32),
                 ("level_04_fragile.json", 28, 84),
                 ("level_05_fragile.json", 33, 62),
                 ("level_08_split_basic.json", 11, 20)]
        for name, length, cost in cases:
            with self.subTest(stage=name):
                stage = load_stage(STAGES_DIR / name)
                res = UCSSolver(stage).solve()
                self.assertEqual(res.solution_length, length)
                self.assertEqual(replay(stage, res.actions)[0], cost)

    def test_dfs_is_not_optimal_on_level_10(self):
        stage = load_stage(STAGES_DIR / "level_10_split_complex.json")
        dfs = DFSSolver(stage).solve()
        bfs = BFSSolver(stage).solve()
        self.assertTrue(dfs.found)
        self.assertGreater(dfs.solution_length, bfs.solution_length)

    def test_min_step_cost_is_positive(self):
        self.assertGreaterEqual(MIN_STEP_COST, 1)

    def test_unsolvable_stage_returns_not_found(self):
        data = {"name": "unsolvable", "grid": ["S.  H"], "bridges": [],
                "switches": [], "teleports": []}
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "unsolvable.json"
            f.write_text(json.dumps(data), encoding="utf-8")
            stage = load_stage(f)
        for cls in (DFSSolver, UCSSolver):
            res = cls(stage).solve()
            self.assertFalse(res.found)
            self.assertEqual(res.actions, [])


if __name__ == "__main__":
    unittest.main()