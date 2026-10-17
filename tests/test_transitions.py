"""Unit tests for block rolling transition table and orientations."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import unittest
from bloxorz.domain.state import State

from bloxorz.domain.actions import Action
from bloxorz.domain.models import Stage
from bloxorz.engine.transitions import transition

class TestTransitions(unittest.TestCase):
    def setUp(self):
        # 10x10 empty floor
        grid = ["." * 10 for _ in range(10)]
        self.dummy_stage = Stage(
            name="Dummy",
            grid=grid,
            rows=10,
            cols=10,
            start_pos=(5, 5),
            goal_pos=(9, 9),
            bridges=[],
            initial_bridges=(),
            switches={},
            teleports={}
        )

    def test_standing_roll(self):
        s = State(r1=5, c1=5, r2=5, c2=5, bridges=())
        self.assertTrue(s.is_standing)

        # UP -> lying col at (3, 5) and (4, 5)
        nxt = transition(s, Action.UP, self.dummy_stage)
        self.assertIsNotNone(nxt)
        self.assertTrue(nxt.is_lying_col)
        self.assertEqual((nxt.r1, nxt.c1, nxt.r2, nxt.c2), (3, 5, 4, 5))

        # DOWN -> lying col at (6, 5) and (7, 5)
        nxt = transition(s, Action.DOWN, self.dummy_stage)
        self.assertIsNotNone(nxt)
        self.assertTrue(nxt.is_lying_col)
        self.assertEqual((nxt.r1, nxt.c1, nxt.r2, nxt.c2), (6, 5, 7, 5))

        # LEFT -> lying row at (5, 3) and (5, 4)
        nxt = transition(s, Action.LEFT, self.dummy_stage)
        self.assertIsNotNone(nxt)
        self.assertTrue(nxt.is_lying_row)
        self.assertEqual((nxt.r1, nxt.c1, nxt.r2, nxt.c2), (5, 3, 5, 4))

        # RIGHT -> lying row at (5, 6) and (5, 7)
        nxt = transition(s, Action.RIGHT, self.dummy_stage)
        self.assertIsNotNone(nxt)
        self.assertTrue(nxt.is_lying_row)
        self.assertEqual((nxt.r1, nxt.c1, nxt.r2, nxt.c2), (5, 6, 5, 7))

if __name__ == "__main__":
    unittest.main()
