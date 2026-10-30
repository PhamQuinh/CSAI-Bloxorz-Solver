"""Benchmark protocol, replay validation, failure reporting, and chart inputs."""
import contextlib
import csv
import io
import json
import math
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

from bloxorz.config import STAGES_DIR
from bloxorz.domain.actions import Action
from bloxorz.domain.models import Stage
from bloxorz.engine.stage_loader import load_stage
from bloxorz.experiments import benchmark, report_data
from bloxorz.metrics.export import export_to_csv
from bloxorz.solvers.base import SearchResult
from bloxorz.solvers.bfs import BFSSolver


def tiny_stage():
    return Stage("tiny", ["S..H"], 1, 4, (0, 0), (0, 3), [], (), {}, {})


def good_result(**kwargs):
    fields = dict(found=True, actions=[Action.RIGHT, Action.RIGHT],
                  solution_length=2, search_time=1.25, peak_memory_mb=2.5,
                  expanded_nodes=7)
    fields.update(kwargs)
    return SearchResult(**fields)


def raw_row(stage="level_01_basic", group="Sàn thường", algorithm="BFS",
            repeat=1, status="Thành công", found="Có", search_time_s=1.25,
            peak_memory_mb=2.5, expanded_nodes=7, solution_length=2,
            path_cost=4, roll_count=2, error="", **overrides):
    row = {
        "Màn chơi": stage, "Nhóm màn chơi": group, "Thuật toán": algorithm,
        "Lần chạy": repeat, "Trạng thái": status, "Tìm thấy lời giải": found,
        "Thời gian tìm kiếm (giây)": search_time_s, "Bộ nhớ đỉnh (MiB)": peak_memory_mb,
        "Số nút mở rộng": expanded_nodes, "Độ dài lời giải (số hành động)": solution_length,
        "Chi phí đường đi": path_cost, "Số lần lăn": roll_count,
        "Chuỗi hành động": "RIGHT RIGHT", "Lỗi": error,
    }
    row.update(overrides)
    return row


class TestReplay(unittest.TestCase):
    def test_split_switch_actions_count_and_use_shared_cost(self):
        stage = load_stage(STAGES_DIR / "level_08_split_basic.json")
        result = BFSSolver(stage).solve()
        # The first two RIGHT actions land on T. Switching twice leaves the
        # position/active cube unchanged while adding two actions and cost 2.
        base_cost, base_rolls = benchmark.validate_solution(stage, result)
        result.actions[2:2] = [Action.SWITCH_BLOCK, Action.SWITCH_BLOCK]
        result.solution_length = len(result.actions)
        cost, rolls = benchmark.validate_solution(stage, result)
        self.assertEqual(cost, base_cost + 2)
        self.assertEqual(rolls, base_rolls)
        self.assertEqual(result.solution_length, rolls + 2)
        result.solution_length = rolls
        with self.assertRaisesRegex(ValueError, "len\\(actions\\)"):
            benchmark.validate_solution(stage, result)

    def test_illegal_transition_and_non_goal_are_rejected(self):
        for actions, error in (([Action.UP], "Chuyển trạng thái không hợp lệ"),
                               ([Action.RIGHT], "không kết thúc ở trạng thái đích")):
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                benchmark.validate_solution(
                    tiny_stage(), good_result(actions=actions, solution_length=len(actions)))

    def test_initial_bridge_configuration_is_used(self):
        stage = Stage("bridge", ["SBBH"], 1, 4, (0, 0), (0, 3),
                      [[(0, 1), (0, 2)]], (True,), {}, {})
        self.assertEqual(benchmark.validate_solution(stage, good_result()), (4, 2))
        stage.initial_bridges = (False,)
        with self.assertRaisesRegex(ValueError, "Chuyển trạng thái không hợp lệ"):
            benchmark.validate_solution(stage, good_result())

    def test_groups_follow_actual_json(self):
        expected = ["Sàn thường", "Công tắc và cầu", "Sàn thường", "Ô dễ vỡ",
                    "Công tắc và cầu", "Sàn thường", "Công tắc và cầu",
                    "Tách khối", "Tách khối", "Tách khối kết hợp công tắc và cầu"]
        self.assertEqual([
            benchmark.classify_stage(load_stage(STAGES_DIR / name))
            for name in benchmark.STAGE_FILES
        ], expected)


class TestSummaries(unittest.TestCase):
    def test_medians_exclude_failures_and_partial_success_is_visible(self):
        rows = [raw_row(repeat=1, search_time_s=1, peak_memory_mb=8),
                raw_row(repeat=2, search_time_s=5, peak_memory_mb=2),
                raw_row(repeat=3, status="Lỗi thực thi", found="", search_time_s="",
                        peak_memory_mb="", expanded_nodes="", solution_length="",
                        path_cost="", roll_count="", error="RuntimeError: failed")]
        summary = benchmark.summarize_runs(rows)
        self.assertEqual(summary["Thời gian tìm kiếm (giây)"], 3)
        self.assertEqual(summary["Bộ nhớ đỉnh (MiB)"], 5)
        self.assertEqual(summary["Số nút mở rộng"], 7)
        self.assertEqual(summary["Số lần chạy thành công"], 2)
        self.assertEqual(summary["Trạng thái"], "Thất bại")
        self.assertIn("Lần chạy 3: RuntimeError", summary["Lỗi"])

    def test_discrepancies_are_reported_and_never_averaged(self):
        for field in benchmark.STABLE_FIELDS:
            with self.subTest(field=field):
                changed = "Không" if field == "Tìm thấy lời giải" else 100
                summary = benchmark.summarize_runs([raw_row(), raw_row(repeat=2, **{field: changed})])
                self.assertEqual(summary["Trạng thái"], "Không nhất quán")
                self.assertEqual(summary[field], "")
                self.assertIn(field, summary["Lỗi"])


class TestRunner(unittest.TestCase):
    def test_each_astar_run_rebuilds_a_previously_warm_cache(self):
        cache = benchmark._landing_lower_bounds
        self.addCleanup(cache.cache_clear)
        stage = load_stage(STAGES_DIR / "level_08_split_basic.json")
        benchmark.AStarSolver(stage).solve()
        self.assertGreater(cache.cache_info().currsize, 0)
        original_search = benchmark.AStarSolver._search
        cache_sizes_at_start = []

        def search(solver):
            cache_sizes_at_start.append(cache.cache_info().currsize)
            return original_search(solver)

        with patch.object(benchmark.AStarSolver, "_search", search):
            for _ in range(2):
                row = benchmark._run_once(stage, benchmark.AStarSolver, raw_row())
                self.assertEqual(row["Trạng thái"], "Thành công")
                self.assertGreater(cache.cache_info().currsize, 0)
                self.assertEqual(cache.cache_info().misses, 1)
        self.assertEqual(cache_sizes_at_start, [0, 0])

    def test_other_solvers_do_not_clear_the_heuristic_cache(self):
        cache = benchmark._landing_lower_bounds
        self.addCleanup(cache.cache_clear)
        stage = load_stage(STAGES_DIR / "level_08_split_basic.json")
        benchmark.AStarSolver(stage).solve()
        before = cache.cache_info()
        self.assertGreater(before.currsize, 0)
        for solver_type in (benchmark.BFSSolver, benchmark.DFSSolver, benchmark.UCSSolver):
            row = benchmark._run_once(stage, solver_type, raw_row())
            self.assertEqual(row["Trạng thái"], "Thành công")
            self.assertEqual(cache.cache_info(), before)

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.output = Path(self.folder.name)
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stderr = contextlib.redirect_stderr(io.StringIO())
        self.stdout.__enter__()
        self.stderr.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)
        self.addCleanup(self.stderr.__exit__, None, None, None)

    def read_csv(self, name):
        columns = benchmark.RAW_COLUMNS if name == "benchmark_raw.csv" else benchmark.SUMMARY_COLUMNS
        return report_data.read_result_rows(self.output / name, columns)

    def test_default_five_repeats_fixed_order_and_fresh_solvers(self):
        instances = []

        class FakeSolver:
            def __init__(self, stage):
                self.stage = stage
                self.used = False
                self.index = len(instances)
                instances.append(self)

            def solve(self):
                if self.used:
                    raise AssertionError("reused solver")
                self.used = True
                value = (9, 1, 5, 3, 7)[self.index % 5]
                return good_result(search_time=value, peak_memory_mb=10 * value)

        solvers = dict.fromkeys(report_data.ALGORITHMS, FakeSolver)
        with patch.object(benchmark, "SOLVERS", solvers), \
                patch.object(benchmark, "load_stage", return_value=tiny_stage()) as loader, \
                patch.object(report_data, "generate_report_plots", return_value=[]):
            self.assertTrue(benchmark.run_benchmark(results_dir=self.output))
        raw = self.read_csv("benchmark_raw.csv")
        summary = self.read_csv("benchmark_summary.csv")
        self.assertEqual(len(raw), 200)
        self.assertEqual(len(summary), 40)
        self.assertEqual(len(instances), 200)
        self.assertEqual(loader.call_count, 10)
        self.assertEqual([row["Màn chơi"] for row in summary[::4]],
                         [Path(name).stem for name in benchmark.STAGE_FILES])
        self.assertEqual([row["Thuật toán"] for row in summary[:4]], list(solvers))
        self.assertEqual([row["Lần chạy"] for row in raw[:5]], ["1", "2", "3", "4", "5"])
        for row in summary:
            self.assertEqual(row["Trạng thái"], "Thành công")
            self.assertEqual(row["Thời gian tìm kiếm (giây)"], "5")
            self.assertEqual(row["Bộ nhớ đỉnh (MiB)"], "50")
            self.assertEqual(row["Chi phí đường đi"], "4")
        metadata = json.loads((self.output / "benchmark_metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "Thành công")
        self.assertEqual(metadata["repeats"], 5)
        self.assertEqual(len(metadata["stages"]), 10)
        self.assertIn("python_version", metadata)
        self.assertEqual(metadata["output_language"], "vi-VN")
        self.assertIn("MiB", metadata["measurement_method"])
        self.assertIn("số nút mở rộng", metadata["summary_method"])
        self.assertIn("tính cả SWITCH_BLOCK", metadata["solution_length_convention"])

    def test_one_repeat_keeps_unsolved_exception_and_invalid_rows_and_exits_nonzero(self):
        class OK:
            def __init__(self, stage):
                pass

            def solve(self):
                return good_result()

        class Unsolved(OK):
            def solve(self):
                return good_result(found=False, actions=[], solution_length=0)

        class Error(OK):
            def solve(self):
                raise RuntimeError("search broke")

        class Invalid(OK):
            def solve(self):
                return good_result(solution_length=1)

        with patch.object(benchmark, "SOLVERS", dict(zip(report_data.ALGORITHMS,
                                                       (OK, Unsolved, Error, Invalid)))), \
                patch.object(benchmark, "load_stage", return_value=tiny_stage()), \
                patch.object(report_data, "generate_report_plots", return_value=[]):
            code = benchmark.main(["--repeats", "1", "--results-dir", str(self.output)])
        self.assertEqual(code, 1)
        raw = self.read_csv("benchmark_raw.csv")
        summary = self.read_csv("benchmark_summary.csv")
        self.assertEqual(len(raw), 40)
        self.assertEqual(len(summary), 40)
        self.assertEqual([row["Trạng thái"] for row in raw[:4]],
                         ["Thành công", "Không tìm thấy lời giải", "Lỗi thực thi", "Không hợp lệ"])
        for row in raw[1:4]:
            for field in benchmark.SOLUTION_FIELDS:
                self.assertEqual(row[field], "")
            self.assertTrue(row["Lỗi"])
        self.assertEqual(raw[1]["Tìm thấy lời giải"], "Không")
        self.assertEqual(raw[1]["Thời gian tìm kiếm (giây)"], "1.25")
        self.assertEqual(raw[1]["Số nút mở rộng"], "7")
        for field in benchmark.MEASUREMENTS:
            self.assertEqual(raw[2][field], "")
        self.assertEqual(summary[1]["Thời gian tìm kiếm (giây)"], "")
        self.assertEqual(summary[1]["Số nút mở rộng"], "7")
        self.assertEqual(json.loads((self.output / "benchmark_metadata.json").read_text(encoding="utf-8"))["status"], "Thất bại")

    def test_missing_inputs_preserve_all_pairs_and_replace_previous_success(self):
        export_to_csv([raw_row()], self.output / "benchmark_summary.csv")
        with patch.object(report_data, "generate_report_plots", return_value=[]):
            self.assertFalse(benchmark.run_benchmark(
                repeats=1, stages_dir=self.output / "missing", results_dir=self.output))
        raw = self.read_csv("benchmark_raw.csv")
        summary = self.read_csv("benchmark_summary.csv")
        self.assertEqual(len(raw), 40)
        self.assertEqual(len(summary), 40)
        self.assertTrue(all(row["Trạng thái"] == "Lỗi thực thi" for row in summary))
        self.assertTrue(all("FileNotFoundError" in row["Lỗi"] for row in raw))
        self.assertTrue(all(row["Thời gian tìm kiếm (giây)"] == "" for row in raw))

    def test_chart_errors_mark_run_failed_after_csvs_are_written(self):
        with patch.object(report_data, "generate_report_plots", side_effect=RuntimeError("plot broke")):
            self.assertFalse(benchmark.run_benchmark(
                repeats=1, stages_dir=self.output / "missing", results_dir=self.output))
        self.assertEqual(len(self.read_csv("benchmark_raw.csv")), 40)
        metadata = json.loads((self.output / "benchmark_metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "Thất bại")
        self.assertIn("plot broke", metadata["chart_error"])

    def test_invalid_repeats_are_rejected(self):
        for repeats in (0, -1, 1.5, True):
            with self.subTest(repeats=repeats), self.assertRaises(ValueError):
                benchmark.run_benchmark(repeats, results_dir=self.output)
        with self.assertRaises(SystemExit) as error:
            benchmark.main(["--repeats", "0"])
        self.assertEqual(error.exception.code, 2)


class TestVietnameseResults(unittest.TestCase):
    def test_console_uses_utf8_even_with_windows_cp1258(self):
        for module in (benchmark, report_data):
            with self.subTest(module=module.__name__):
                buffer = io.BytesIO()
                stream = io.TextIOWrapper(buffer, encoding="cp1258")
                with patch("sys.stdout", stream), patch("sys.stderr", stream):
                    module.configure_console()
                    stream.write("Thư mục kết quả: Thành công")
                    stream.flush()
                self.assertEqual(buffer.getvalue().decode("utf-8"), "Thư mục kết quả: Thành công")

    def test_csv_writes_vietnamese_rows_directly(self):
        statuses = ("Thành công", "Không tìm thấy lời giải", "Lỗi thực thi",
                    "Không hợp lệ", "Thất bại", "Không nhất quán")
        groups = ("Sàn thường", "Ô dễ vỡ", "Công tắc và cầu", "Tách khối",
                  "Tách khối kết hợp công tắc và cầu", "Chưa xác định")
        rows = [raw_row(status=status, group=group, found=found)
                for status in statuses for group in groups for found in ("Có", "Không", "")]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "raw.csv"
            benchmark._atomic_csv(rows, path)
            self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
            with path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, list(benchmark.RAW_COLUMNS))
                exported = list(reader)
            self.assertEqual({row["Trạng thái"] for row in exported}, set(statuses))
            self.assertEqual({row["Nhóm màn chơi"] for row in exported}, set(groups))
            self.assertEqual({row["Tìm thấy lời giải"] for row in exported}, {"Có", "Không", ""})
            actual = report_data.read_result_rows(path, benchmark.RAW_COLUMNS)
        self.assertEqual(actual, [{key: str(value) for key, value in row.items()} for row in rows])

    def test_metadata_is_written_without_converting_keys_or_values(self):
        original = {
            "status": "Thành công", "python_version": "3.14.0", "repeats": 5,
            "stages_dir": "D:\\CSAI-Bloxorz-Solver\\stages", "started_at": "2026-10-21T14:32:52+00:00",
            "stages": [{"stage": "level_01_basic", "group": "Sàn thường", "sha256": "abcdef123"}],
            **benchmark.METADATA_DESCRIPTIONS,
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "metadata.json"
            benchmark._atomic_json(original, path)
            actual = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(actual, original)

    def test_regenerate_existing_keeps_every_cell_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            row = raw_row(search_time_s="0.000001230000000456", peak_memory_mb="0.123456789012345")
            summary = benchmark.summarize_runs([raw_row()])
            summary.update({"Thời gian tìm kiếm (giây)": row["Thời gian tìm kiếm (giây)"],
                            "Bộ nhớ đỉnh (MiB)": row["Bộ nhớ đỉnh (MiB)"]})
            benchmark._atomic_csv([row], output / "benchmark_raw.csv")
            benchmark._atomic_csv([summary], output / "benchmark_summary.csv")
            metadata = {"status": "Thành công", "repeats": 5, "completed_at": "2026-10-21T14:32:59+00:00"}
            (output / "benchmark_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
            old_raw = report_data.read_result_rows(output / "benchmark_raw.csv", benchmark.RAW_COLUMNS)
            old_summary = report_data.read_result_rows(output / "benchmark_summary.csv", benchmark.SUMMARY_COLUMNS)
            with patch.object(report_data, "generate_report_plots", return_value=[]) as plots, \
                    patch.object(benchmark, "_run_once") as solve, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(benchmark.main(["--regenerate-existing", "--results-dir", folder]), 0)
                first_bytes = {path.name: path.read_bytes() for path in output.iterdir()}
                self.assertEqual(benchmark.main(["--localize-existing", "--results-dir", folder]), 0)
                self.assertEqual(first_bytes, {path.name: path.read_bytes() for path in output.iterdir()})
            solve.assert_not_called()
            self.assertEqual(plots.call_count, 2)
            self.assertEqual(report_data.read_result_rows(output / "benchmark_raw.csv", benchmark.RAW_COLUMNS), old_raw)
            self.assertEqual(report_data.read_result_rows(output / "benchmark_summary.csv", benchmark.SUMMARY_COLUMNS), old_summary)
            actual = json.loads((output / "benchmark_metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(actual["completed_at"], metadata["completed_at"])

    def test_english_headers_are_not_silently_converted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "summary.csv"
            export_to_csv([{"stage": "level_01_basic", "algorithm": "BFS"}], path)
            with self.assertRaisesRegex(ValueError, "thiếu cột"):
                report_data.read_summary(path)


class TestReportData(unittest.TestCase):
    def test_numeric_order_missing_failed_and_invalid_metrics(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "summary.csv"
            export_to_csv([
                raw_row(stage="level_10_split_complex", solution_length=10),
                raw_row(stage="level_02_basic", solution_length=0),
                raw_row(status="Không hợp lệ", solution_length=99),
                raw_row(stage="level_03_basic", solution_length="nan"),
            ], path)
            rows = report_data.read_summary(path)
        values = report_data.metric_values(rows, "BFS", "Độ dài lời giải (số hành động)")
        self.assertTrue(math.isnan(values[0]))
        self.assertEqual(values[1], 0)  # A real zero is distinct from missing data.
        self.assertTrue(all(math.isnan(value) for value in values[2:9]))
        self.assertEqual(values[9], 10)

    def test_duplicate_pairs_and_missing_columns_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "summary.csv"
            for rows, message in (([raw_row(), raw_row()], "trùng lặp"),
                                  ([{"Màn chơi": "level_01_basic"}], "thiếu cột")):
                export_to_csv(rows, path)
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    report_data.read_summary(path)

    def test_headless_charts_are_saved_for_incomplete_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "summary.csv"
            export_to_csv([benchmark.summarize_runs([raw_row(roll_count=1)])], path)
            # Check rendered labels, footer, Unicode font coverage, and bounds.
            from matplotlib.figure import Figure
            from matplotlib.font_manager import FontProperties, findfont
            from matplotlib.ft2font import FT2Font
            savefig = Figure.savefig
            labels = []

            def inspect_figure(fig, output, **kwargs):
                fig.canvas.draw()
                ax = fig.axes[0]
                if ax.get_title() == "Số lần lăn":
                    self.assertEqual(ax.lines[0].get_ydata()[0], 1)
                    self.assertTrue(math.isnan(ax.lines[0].get_ydata()[1]))
                    self.assertTrue(any("không tính SWITCH_BLOCK" in text.get_text()
                                        for text in fig.texts))
                    self.assertFalse(any("Độ dài lời giải tính cả" in text.get_text()
                                         for text in fig.texts))
                texts = [ax.title, ax.xaxis.label, ax.yaxis.label,
                         ax.get_legend().get_title(), *fig.texts]
                characters = FT2Font(findfont(FontProperties(family="DejaVu Sans"))).get_charmap()
                for text in texts:
                    labels.append(text.get_text())
                    self.assertTrue(all(ord(char) in characters or char.isspace()
                                        for char in text.get_text()))
                    bbox = text.get_window_extent(fig.canvas.get_renderer())
                    self.assertGreaterEqual(bbox.x0, 0)
                    self.assertGreaterEqual(bbox.y0, 0)
                    self.assertLessEqual(bbox.x1, fig.bbox.width)
                    self.assertLessEqual(bbox.y1, fig.bbox.height)
                return savefig(fig, output, **kwargs)

            with warnings.catch_warnings(record=True) as caught, \
                    patch.object(Figure, "savefig", inspect_figure):
                paths = report_data.generate_report_plots(path)
            self.assertFalse(any("Glyph" in str(item.message) for item in caught))
            self.assertIn("Số nút mở rộng", labels)
            self.assertIn("Độ dài lời giải (số hành động)", labels)
            self.assertIn("Số lần lăn", labels)
            self.assertEqual(len(paths), 5)
            self.assertIn("benchmark_roll_count.png", {p.name for p in paths})
            self.assertIn("Thuật toán", labels)
            self.assertTrue(any("tính cả SWITCH_BLOCK" in label for label in labels))
            self.assertTrue(any("Số liệu thiếu" in label for label in labels))
            self.assertEqual({p.name for p in paths},
                             {settings[2] for settings in report_data.METRICS.values()})
            for output in paths:
                self.assertGreater(output.stat().st_size, 1000)
                self.assertEqual(output.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            import matplotlib
            self.assertEqual(matplotlib.get_backend().lower(), "agg")


if __name__ == "__main__":
    unittest.main()
