"""Unit tests for A* and the TV3 heuristics / metrics."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import json
import tempfile
import unittest

from bloxorz.config import STAGES_DIR
from bloxorz.domain.actions import Action
from bloxorz.domain.models import Stage
from bloxorz.domain.rules import is_goal_state
from bloxorz.domain.state import State
from bloxorz.engine.stage_loader import load_stage
from bloxorz.engine.transitions import get_valid_actions, transition
from bloxorz.metrics.measurement import measure_performance
from bloxorz.solvers.astar import AStarSolver
from bloxorz.solvers.costs import COST_NORMAL, step_cost
from bloxorz.solvers.heuristics import (
    manhattan_half,
    manhattan_half_with_orientation_penalty,
)
from bloxorz.solvers.ucs import UCSSolver

# Least-move lengths from stages/ground_truth_solutions.txt.
OPTIMAL_LENGTHS = {
    "level_01_basic.json": 7,
    "level_02_basic.json": 17,
    "level_03_basic.json": 19,
    "level_04_fragile.json": 28,
    "level_05_fragile.json": 33,
    "level_06_switch_bridge.json": 35,
    "level_07_switch_bridge.json": 44,
    "level_08_split_basic.json": 10,
    "level_09_combined.json": 24,
    "level_10_split_complex.json": 57,
}


def _initial(stage):
    sr, sc = stage.start_pos
    return State(r1=sr, c1=sc, r2=sr, c2=sc,
                 bridges=stage.initial_bridges, active_cube=-1)


def _replay(stage, actions):
    """Replay actions. Return (total step_cost, final state), or None."""
    state = _initial(stage)
    total = 0
    for act in actions:
        nxt = transition(state, act, stage)
        if nxt is None:
            return None
        total += step_cost(stage, state, act, nxt)
        state = nxt
    return total, state


class TestAStar(unittest.TestCase):
    def test_basic_maps_match_ground_truth_length(self):
        # On stages 01-03 the minimum-cost path also has the ground-truth
        # number of moves.
        for name in ("level_01_basic.json", "level_02_basic.json", "level_03_basic.json"):
            with self.subTest(stage=name):
                stage = load_stage(STAGES_DIR / name)
                res = AStarSolver(stage).solve()
                played = _replay(stage, res.actions)
                self.assertIsNotNone(played)
                _, final = played
                self.assertTrue(res.found)
                self.assertEqual(res.solution_length, OPTIMAL_LENGTHS[name])
                self.assertTrue(is_goal_state(final, stage))

    def test_cost_matches_ucs_on_every_stage(self):
        for name in OPTIMAL_LENGTHS:
            with self.subTest(stage=name):
                stage = load_stage(STAGES_DIR / name)
                astar = AStarSolver(stage).solve()
                ucs = UCSSolver(stage).solve()
                astar_play = _replay(stage, astar.actions)
                ucs_play = _replay(stage, ucs.actions)
                self.assertTrue(astar.found)
                self.assertIsNotNone(astar_play)
                self.assertEqual(astar_play[0], ucs_play[0])
                self.assertTrue(is_goal_state(astar_play[1], stage))

    def test_metrics_are_populated(self):
        stage = load_stage(STAGES_DIR / "level_01_basic.json")
        res = AStarSolver(stage).solve()
        self.assertGreater(res.search_time, 0.0)
        self.assertGreater(res.peak_memory_mb, 0.0)
        self.assertGreater(res.expanded_nodes, 0)

    def test_unsolvable_stage(self):
        data = {"name": "unsolvable", "grid": ["S.  H"], "bridges": [],
                "switches": [], "teleports": []}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "unsolvable.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            stage = load_stage(path)
        res = AStarSolver(stage).solve()
        self.assertFalse(res.found)
        self.assertEqual(res.actions, [])
        self.assertEqual(res.solution_length, 0)

    def test_h1_is_zero_on_a_standing_goal_and_never_negative(self):
        stage = load_stage(STAGES_DIR / "level_01_basic.json")
        goal_r, goal_c = stage.goal_pos
        standing_on_goal = State(
            r1=goal_r, c1=goal_c, r2=goal_r, c2=goal_c,
            bridges=stage.initial_bridges, active_cube=-1,
        )
        self.assertEqual(manhattan_half(standing_on_goal, stage), 0.0)
        self.assertGreaterEqual(manhattan_half(_initial(stage), stage), 0.0)

    def test_h1_consistent_on_maps_without_a_teleport(self):
        for name in ("level_01_basic.json", "level_04_fragile.json"):
            with self.subTest(stage=name):
                stage = load_stage(STAGES_DIR / name)
                self.assertFalse(stage.teleports)
                seen = set()
                stack = [_initial(stage)]
                seen.add(stack[0])
                while stack:
                    current = stack.pop()
                    h_here = manhattan_half(current, stage)
                    for act in get_valid_actions(current, stage):
                        nxt = transition(current, act, stage)
                        h_next = manhattan_half(nxt, stage)
                        edge = step_cost(stage, current, act, nxt)
                        self.assertLessEqual(h_here, edge + h_next + 1e-9)
                        if nxt not in seen:
                            seen.add(nxt)
                            stack.append(nxt)

    def test_h1_never_exceeds_remaining_optimal_cost(self):
        for name in OPTIMAL_LENGTHS:
            with self.subTest(stage=name):
                stage = load_stage(STAGES_DIR / name)
                actions = UCSSolver(stage).solve().actions
                state = _initial(stage)
                remaining = _replay(stage, actions)[0]
                for act in actions:
                    self.assertLessEqual(manhattan_half(state, stage), remaining + 1e-9)
                    nxt = transition(state, act, stage)
                    remaining -= step_cost(stage, state, act, nxt)
                    state = nxt
                self.assertEqual(manhattan_half(state, stage), 0.0)

    def test_orientation_penalty_can_exceed_the_true_cost(self):
        """One normal roll from the hole: h1 = 0.75, h2 = 1.75, step cost = 2."""
        stage = Stage(
            name="one-roll",
            grid=["....H"],
            rows=1,
            cols=5,
            start_pos=(0, 0),
            goal_pos=(0, 4),
            bridges=[],
            initial_bridges=(),
            switches={},
            teleports={},
        )
        lying = State(r1=0, c1=2, r2=0, c2=3, bridges=(), active_cube=-1)
        self.assertAlmostEqual(manhattan_half(lying, stage), 0.75)
        self.assertAlmostEqual(
            manhattan_half_with_orientation_penalty(lying, stage), 1.75
        )
        stood = transition(lying, Action.RIGHT, stage)
        self.assertTrue(is_goal_state(stood, stage))
        self.assertEqual(step_cost(stage, lying, Action.RIGHT, stood), COST_NORMAL)
        self.assertLessEqual(manhattan_half(lying, stage), COST_NORMAL)


class TestMeasurePerformance(unittest.TestCase):
    def test_records_time_memory_and_keeps_node_count(self):
        with measure_performance() as metrics:
            _ = sum(range(1000))
            metrics["expanded_nodes"] = 12
        self.assertGreaterEqual(metrics["search_time"], 0.0)
        self.assertGreaterEqual(metrics["peak_memory_mb"], 0.0)
        self.assertEqual(metrics["expanded_nodes"], 12)
        self.assertFalse(__import__("tracemalloc").is_tracing())


if __name__ == "__main__":
    unittest.main()
