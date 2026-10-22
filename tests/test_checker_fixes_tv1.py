"""Unit tests verifying fixes for checker issues R2 and R3 (TV1)."""
import json
import tempfile
import unittest
from pathlib import Path

from bloxorz.config import STAGES_DIR
from bloxorz.domain.actions import Action
from bloxorz.domain.models import Stage
from bloxorz.domain.rules import is_goal_state
from bloxorz.domain.state import State
from bloxorz.engine.stage_loader import load_stage
from bloxorz.engine.transitions import transition
from bloxorz.engine.validation import is_valid_position, is_valid_cube_position
from bloxorz.solvers.bfs import BFSSolver


class TestCheckerFixesTV1(unittest.TestCase):
    def test_split_switch_triggers_source_bridge(self):
        """R2: Stepping on a split switch 'T' triggers bridge actions linked to 'T'."""
        data = {
            "name": "split_with_switch",
            "grid": [
                "S..T..H",
                "   b   "
            ],
            "bridges": [[[1, 3]]],  # Bridge 0 at (1, 3) is closed ('b')
            "switches": [
                [0, 3, [[0, "on"]]]   # 'T' at (0, 3) turns Bridge 0 ON
            ],
            "teleports": [
                [0, 3, 0, 0, 0, 6, 0]  # Teleport to (0, 0) and (0, 6)
            ]
        }
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "map.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            stage = load_stage(p)

        # Start standing at (0, 0)
        s0 = State(r1=0, c1=0, r2=0, c2=0, bridges=(False,), active_cube=-1)
        # Move RIGHT -> lying row at (0, 1) & (0, 2)
        s1 = transition(s0, Action.RIGHT, stage)
        self.assertIsNotNone(s1)
        # Move RIGHT -> standing on 'T' at (0, 3)
        s2 = transition(s1, Action.RIGHT, stage)
        self.assertIsNotNone(s2)

        # Check: Bridge 0 was turned ON by the switch at (0, 3)!
        self.assertEqual(s2.bridges, (True,))
        # Check: Block is now split at destinations (0, 0) and (0, 6)
        self.assertTrue(s2.is_split)
        self.assertEqual((s2.r1, s2.c1), (0, 0))
        self.assertEqual((s2.r2, s2.c2), (0, 6))

    def test_single_cube_cannot_activate_heavy_switch(self):
        """R2: Single cube cannot activate a Heavy switch 'X'."""
        data = {
            "name": "cube_on_heavy_switch",
            "grid": [
                "S...H",
                "  X  ",
                "  b  "
            ],
            "bridges": [[[2, 2]]],
            "switches": [
                [1, 2, [[0, "on"]]]  # Heavy switch 'X'
            ],
            "teleports": []
        }
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "map.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            stage = load_stage(p)

        # Split block with cube 0 at (0, 2) and cube 1 at (0, 4)
        s_split = State(r1=0, c1=2, r2=0, c2=4, bridges=(False,), active_cube=0)
        # Move cube 0 DOWN to (1, 2) which is 'X'
        s_next = transition(s_split, Action.DOWN, stage)
        self.assertIsNotNone(s_next)
        # Bridge MUST remain False (closed) because a single cube cannot trigger 'X'!
        self.assertEqual(s_next.bridges, (False,))

    def test_teleport_destinations_validated_void_and_closed_bridge(self):
        """R3: Teleporting into void or closed bridge results in None (falling)."""
        # Map where teleport destination is void ' '
        data_void = {
            "name": "tp_into_void",
            "grid": [
                "S.T",
                "..H"
            ],
            "bridges": [],
            "switches": [],
            "teleports": [
                [0, 2, 0, 0, 1, 0, 0]  # Destination 2 is (1, 0) which is void in next test or padded
            ]
        }
        # Destination with void character
        data_void["grid"] = [
            "S.TH",
            "    "
        ]
        data_void["teleports"] = [[0, 2, 0, 0, 1, 1, 0]]
        # Stage loader rejects void destination at load time
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "map_void.json"
            p.write_text(json.dumps(data_void), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_stage(p)

        # Map where destination 2 is on a closed bridge
        data_closed = {
            "name": "tp_into_closed_bridge",
            "grid": [
                "S..T",
                "...H",
                "..b."
            ],
            "bridges": [[[2, 2]]],  # Closed bridge at (2, 2)
            "switches": [],
            "teleports": [
                [0, 3, 0, 0, 2, 2, 0]  # Destination 2 is on closed bridge
            ]
        }
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "map_closed.json"
            p.write_text(json.dumps(data_closed), encoding="utf-8")
            stage = load_stage(p)

        # Roll block onto 'T' at (0, 3)
        s0 = State(r1=0, c1=0, r2=0, c2=0, bridges=(False,), active_cube=-1)
        s1 = transition(s0, Action.RIGHT, stage)
        s2 = transition(s1, Action.RIGHT, stage)
        # Destination 2 is closed bridge -> must return None (block falls)!
        self.assertIsNone(s2)

    def test_symmetrical_soft_switch_trigger_on_teleport(self):
        """R2: Symmetrical trigger of soft switches at both teleport destinations."""
        data = {
            "name": "tp_symmetrical_switches",
            "grid": [
                "S..T.",
                "O..O.",
                "b..b.",
                "....H"
            ],
            "bridges": [[[2, 0]], [[2, 3]]],
            "switches": [
                [1, 0, [[0, "on"]]],  # Dest 1 switch
                [1, 3, [[1, "on"]]]   # Dest 2 switch
            ],
            "teleports": [
                [0, 3, 1, 0, 1, 3, 0]  # Teleport to (1, 0) and (1, 3)
            ]
        }
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "map.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            stage = load_stage(p)

        s0 = State(r1=0, c1=0, r2=0, c2=0, bridges=(False, False), active_cube=-1)
        s1 = transition(s0, Action.RIGHT, stage)
        s2 = transition(s1, Action.RIGHT, stage)
        self.assertIsNotNone(s2)
        # BOTH switches at destination 1 and destination 2 must trigger!
        self.assertEqual(s2.bridges, (True, True))

    def test_two_cubes_at_goal_cannot_win(self):
        """R3: Two split cubes at the goal cannot trigger victory."""
        stage_data = {
            "name": "goal_test",
            "grid": ["S...H"],
            "bridges": [],
            "switches": [],
            "teleports": []
        }
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "map.json"
            p.write_text(json.dumps(stage_data), encoding="utf-8")
            stage = load_stage(p)

        # Both cubes happen to occupy the goal position (0, 4), but active_cube is 0 (split)
        split_at_goal = State(r1=0, c1=4, r2=0, c2=4, bridges=(), active_cube=0)
        self.assertFalse(split_at_goal.is_standing)
        self.assertFalse(is_goal_state(split_at_goal, stage))

        # Real standing block at goal
        whole_at_goal = State(r1=0, c1=4, r2=0, c2=4, bridges=(), active_cube=-1)
        self.assertTrue(whole_at_goal.is_standing)
        self.assertTrue(is_goal_state(whole_at_goal, stage))

    def test_stage_loader_rejects_malformed_maps(self):
        """R3: Loader raises ValueError on malformed stage configurations."""
        # 1. Multiple 'S'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "multi_s.json"
            p.write_text(json.dumps({"name": "multi_s", "grid": ["S.S.H"]}), encoding="utf-8")
            with self.assertRaises(ValueError) as cm:
                load_stage(p)
            self.assertIn("start position 'S'", str(cm.exception))

        # 2. Multiple 'H'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "multi_h.json"
            p.write_text(json.dumps({"name": "multi_h", "grid": ["S.H.H"]}), encoding="utf-8")
            with self.assertRaises(ValueError) as cm:
                load_stage(p)
            self.assertIn("goal position 'H'", str(cm.exception))

        # 3. Invalid character
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "invalid_ch.json"
            p.write_text(json.dumps({"name": "bad_ch", "grid": ["S.@.H"]}), encoding="utf-8")
            with self.assertRaises(ValueError) as cm:
                load_stage(p)
            self.assertIn("invalid tile '@'", str(cm.exception))

        # 4. Orphan bridge tile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "orphan_b.json"
            p.write_text(json.dumps({"name": "orphan", "grid": ["S.b.H"], "bridges": []}), encoding="utf-8")
            with self.assertRaises(ValueError) as cm:
                load_stage(p)
            self.assertIn("orphan bridge tiles", str(cm.exception))

        # 5. Switch referencing out-of-bounds bridge index
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad_switch.json"
            p.write_text(json.dumps({
                "name": "bad_sw",
                "grid": ["S.O.H"],
                "bridges": [],
                "switches": [[0, 2, [[5, "on"]]]]
            }), encoding="utf-8")
            with self.assertRaises(ValueError) as cm:
                load_stage(p)
            self.assertIn("invalid bridge index 5", str(cm.exception))

    def test_bfs_solver_with_measurement(self):
        """R4/R5: BFSSolver uses measure_performance cleanly."""
        stage = load_stage(STAGES_DIR / "level_01_basic.json")
        res = BFSSolver(stage).solve()
        self.assertTrue(res.found)
        self.assertEqual(res.solution_length, 7)
        self.assertGreaterEqual(res.search_time, 0.0)
        self.assertGreaterEqual(res.peak_memory_mb, 0.0)
        self.assertGreater(res.expanded_nodes, 0)


if __name__ == "__main__":
    unittest.main()
