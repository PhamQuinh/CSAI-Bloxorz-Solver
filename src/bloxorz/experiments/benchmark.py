"""Đo tuần tự và kiểm tra lời giải trên mười màn chơi cố định."""
import argparse
import hashlib
import json
import math
import platform
import statistics
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from bloxorz.config import RESULTS_DIR, STAGES_DIR
from bloxorz.domain.actions import Action
from bloxorz.domain.rules import is_goal_state
from bloxorz.domain.state import State
from bloxorz.engine.stage_loader import load_stage
from bloxorz.engine.transitions import transition
from bloxorz.metrics.export import export_to_csv
from bloxorz.solvers.astar import AStarSolver
from bloxorz.solvers.bfs import BFSSolver
from bloxorz.solvers.costs import step_cost
from bloxorz.solvers.dfs import DFSSolver
from bloxorz.solvers.heuristics import _landing_lower_bounds
from bloxorz.solvers.ucs import UCSSolver


# These names identify the inputs, not their feature groups or difficulty.
STAGE_FILES = (
    "level_01_basic.json", "level_02_basic.json", "level_03_basic.json",
    "level_04_fragile.json", "level_05_fragile.json",
    "level_06_switch_bridge.json", "level_07_switch_bridge.json",
    "level_08_split_basic.json", "level_09_combined.json",
    "level_10_split_complex.json",
)
SOLVERS = {"BFS": BFSSolver, "DFS": DFSSolver, "UCS": UCSSolver, "A*": AStarSolver}
MEASUREMENTS = ("Thời gian tìm kiếm (giây)", "Bộ nhớ đỉnh (MiB)", "Số nút mở rộng")
SOLUTION_FIELDS = ("Độ dài lời giải (số hành động)", "Chi phí đường đi", "Số lần lăn")
STABLE_FIELDS = ("Tìm thấy lời giải", "Số nút mở rộng") + SOLUTION_FIELDS
RAW_COLUMNS = (
    "Màn chơi", "Nhóm màn chơi", "Thuật toán", "Lần chạy", "Trạng thái", "Tìm thấy lời giải",
    "Thời gian tìm kiếm (giây)", "Bộ nhớ đỉnh (MiB)", "Số nút mở rộng",
    "Độ dài lời giải (số hành động)", "Chi phí đường đi", "Số lần lăn", "Chuỗi hành động", "Lỗi",
)
SUMMARY_COLUMNS = (
    "Màn chơi", "Nhóm màn chơi", "Thuật toán", "Trạng thái", "Số lần chạy thành công",
    "Tìm thấy lời giải", "Thời gian tìm kiếm (giây)", "Bộ nhớ đỉnh (MiB)", "Số nút mở rộng",
    "Độ dài lời giải (số hành động)", "Chi phí đường đi", "Số lần lăn", "Lỗi",
)
METADATA_DESCRIPTIONS = {
    "measurement_method": (
        "Lấy trực tiếp SearchResult do measure_performance của từng bộ giải đo: "
        "thời gian bằng perf_counter (giây); bộ nhớ đỉnh là lượng cấp phát Python "
        "được tracemalloc theo dõi, chia cho 1024**2 (MiB). Phạm vi đo gồm tìm kiếm "
        "và dựng lại đường đi. Chạy tuần tự, khởi tạo bộ giải mới cho mỗi lần chạy, "
        "không có lượt chạy khởi động. Xóa bộ nhớ đệm heuristic trước mỗi lượt A* "
        "và trước khi bắt đầu đo; tính lại dữ liệu heuristic trong phạm vi đo."
    ),
    "summary_method": (
        "Lấy trung vị thời gian và bộ nhớ của các lần chạy thành công, đã kiểm tra "
        "lời giải bằng cách phát lại hành động. Kết quả tìm thấy lời giải, số nút "
        "mở rộng, độ dài lời giải, chi phí đường đi và số lần lăn phải ổn định "
        "giữa các lần chạy; mọi khác biệt đều được báo lỗi, không lấy trung bình."
    ),
    "solution_length_convention": (
        "Độ dài lời giải (số hành động) = len(actions), tính cả SWITCH_BLOCK. "
        "Số lần lăn chỉ đếm UP, DOWN, LEFT và RIGHT."
    ),
}


def configure_console():
    """Keep Vietnamese output readable on Windows redirected streams."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def classify_stage(stage):
    """Classify parsed JSON features, independently of the stage's name."""
    tiles = set("".join(stage.grid))
    switches = bool(stage.bridges or stage.switches or tiles & set("OXBb"))
    split = bool(stage.teleports or "T" in tiles)
    if split:
        return "Tách khối kết hợp công tắc và cầu" if switches else "Tách khối"
    if switches:
        return "Công tắc và cầu"
    return "Ô dễ vỡ" if "-" in tiles else "Sàn thường"


def validate_solution(stage, result):
    """Replay outside solver timing; return weighted cost and roll count."""
    if result.solution_length != len(result.actions):
        raise ValueError("Độ dài lời giải phải bằng len(actions), tính cả SWITCH_BLOCK")
    row, col = stage.start_pos
    state = State(row, col, row, col, stage.initial_bridges, active_cube=-1)
    cost = rolls = 0
    for index, action in enumerate(result.actions, start=1):
        if not isinstance(action, Action):
            raise ValueError(f"Hành động không xác định tại bước {index}: {action!r}")
        nxt = transition(state, action, stage)
        if nxt is None:
            raise ValueError(f"Chuyển trạng thái không hợp lệ tại bước {index}: {action.value}")
        cost += step_cost(stage, state, action, nxt)
        rolls += action != Action.SWITCH_BLOCK
        state = nxt
    if not is_goal_state(state, stage):
        raise ValueError("Đường đi phát lại không kết thúc ở trạng thái đích")
    return cost, rolls


def _error_text(exc):
    return f"{type(exc).__name__}: {exc}"


def _run_once(stage, solver_type, row):
    # Construction, validation, and I/O are deliberately outside .solve().
    try:
        if solver_type is AStarSolver:
            # Measure each solve from an empty heuristic cache, including preprocessing.
            _landing_lower_bounds.cache_clear()
        result = solver_type(stage).solve()
    except Exception as exc:
        row.update({"Trạng thái": "Lỗi thực thi", "Lỗi": _error_text(exc)})
        return row
    row.update({
        "Tìm thấy lời giải": "Có" if result.found else "Không",
        "Thời gian tìm kiếm (giây)": result.search_time,
        "Bộ nhớ đỉnh (MiB)": result.peak_memory_mb,
        "Số nút mở rộng": result.expanded_nodes,
    })
    try:
        row["Chuỗi hành động"] = " ".join(
            action.value if isinstance(action, Action) else repr(action)
            for action in result.actions
        )
        for key in MEASUREMENTS:
            if not math.isfinite(row[key]) or row[key] < 0:
                raise ValueError(f"Số đo không hợp lệ — {key}: {row[key]}")
        if not result.found:
            row.update({"Trạng thái": "Không tìm thấy lời giải",
                        "Lỗi": "Thuật toán không tìm thấy lời giải (found=False)"})
            return row
        cost, rolls = validate_solution(stage, result)
        row.update({"Trạng thái": "Thành công",
                    "Độ dài lời giải (số hành động)": result.solution_length,
                    "Chi phí đường đi": cost, "Số lần lăn": rolls})
    except Exception as exc:
        row.update({"Trạng thái": "Không hợp lệ", "Lỗi": _error_text(exc)})
    return row


def summarize_runs(rows):
    """Median successful timings; never average deterministic search results."""
    summary = dict.fromkeys(SUMMARY_COLUMNS, "")
    summary.update({key: rows[0][key] for key in ("Màn chơi", "Nhóm màn chơi", "Thuật toán")})
    successful = [row for row in rows if row["Trạng thái"] == "Thành công"]
    summary["Số lần chạy thành công"] = len(successful)
    statuses = {row["Trạng thái"] for row in rows}
    summary["Trạng thái"] = next(iter(statuses)) if len(statuses) == 1 else "Thất bại"
    errors = [f"Lần chạy {row['Lần chạy']}: {row['Lỗi']}" for row in rows if row["Lỗi"]]
    for key in ("Thời gian tìm kiếm (giây)", "Bộ nhớ đỉnh (MiB)"):
        if successful:
            summary[key] = statistics.median(row[key] for row in successful)
    discrepancies = []
    for key in STABLE_FIELDS:
        values = {row[key] for row in rows if row[key] != ""}
        if len(values) == 1:
            summary[key] = next(iter(values))
        elif len(values) > 1:
            discrepancies.append(f"{key} khác nhau giữa các lần chạy: {sorted(values)}")
    if discrepancies:
        summary["Trạng thái"] = "Không nhất quán"
    summary["Lỗi"] = "; ".join(errors + discrepancies)
    return summary


def _atomic_csv(rows, path):
    """Use the shared CSV exporter, then publish a complete file."""
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".csv", delete=False) as f:
        temporary = Path(f.name)
    try:
        export_to_csv(rows, temporary, encoding="utf-8-sig")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_json(data, path):
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, suffix=".json", delete=False
    ) as f:
        temporary = Path(f.name)
        try:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        except Exception:
            f.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def run_benchmark(repeats=5, stages_dir=STAGES_DIR, results_dir=RESULTS_DIR):
    """Write all run/summary rows and charts; return whether every pair passed."""
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("Số lần lặp phải là số nguyên dương")
    stages_dir, results_dir = Path(stages_dir), Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = results_dir / "benchmark_metadata.json"
    raw_path = results_dir / "benchmark_raw.csv"
    summary_path = results_dir / "benchmark_summary.csv"
    metadata = {
        "status": "Đang chạy", "started_at": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(), "python_executable": sys.executable,
        "platform": platform.platform(), "machine": platform.machine(),
        "processor": platform.processor(), "repeats": repeats,
        "algorithm_order": list(SOLVERS), "stage_order": list(STAGE_FILES),
        "stages_dir": str(stages_dir.resolve()),
        **METADATA_DESCRIPTIONS,
        "output_language": "vi-VN", "schema_version": 2,
        "stages": [],
    }
    # A running/failed marker distinguishes old artifacts from a completed run.
    _atomic_json(metadata, metadata_path)
    raw_rows, summaries = [], []
    for filename in STAGE_FILES:
        path = stages_dir / filename
        stage, group, load_error = None, "Chưa xác định", ""
        stage_metadata = {"stage": path.stem}
        try:
            stage_metadata["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            stage = load_stage(path)
            group = classify_stage(stage)
            stage_metadata.update(group=group, tiles=sorted(set("".join(stage.grid))))
        except Exception as exc:
            load_error = _error_text(exc)
            stage_metadata["error"] = load_error
        metadata["stages"].append(stage_metadata)
        stage_summaries = []
        for algorithm, solver_type in SOLVERS.items():
            rows = []
            for repeat in range(1, repeats + 1):
                row = dict.fromkeys(RAW_COLUMNS, "")
                row.update({"Màn chơi": path.stem, "Nhóm màn chơi": group,
                            "Thuật toán": algorithm, "Lần chạy": repeat})
                if load_error:
                    row.update({"Trạng thái": "Lỗi thực thi", "Lỗi": load_error})
                else:
                    _run_once(stage, solver_type, row)
                rows.append(row)
            raw_rows.extend(rows)
            stage_summaries.append(summarize_runs(rows))
        summaries.extend(stage_summaries)
        # Checkpoint complete rows, including failures, without exposing truncated CSVs.
        _atomic_csv(raw_rows, raw_path)
        _atomic_csv(summaries, summary_path)
        print(f"{path.stem}: " + " | ".join(
            f"{row['Thuật toán']}: {row['Trạng thái']} ({row['Số lần chạy thành công']}/{repeats})"
            for row in stage_summaries
        ), flush=True)
        for row in stage_summaries:
            if row["Lỗi"]:
                print(f"  {row['Thuật toán']}: {row['Lỗi']}", file=sys.stderr, flush=True)

    passed = all(row["Trạng thái"] == "Thành công" for row in summaries)
    try:
        from bloxorz.experiments.report_data import generate_report_plots
        charts = generate_report_plots(summary_path, results_dir)
        metadata["charts"] = [str(path.resolve()) for path in charts]
    except Exception as exc:
        passed = False
        metadata["chart_error"] = _error_text(exc)
        print(f"Không tạo được biểu đồ: {_error_text(exc)}", file=sys.stderr)
    metadata.update(
        status="Thành công" if passed else "Thất bại",
        completed_at=datetime.now(timezone.utc).isoformat(),
        raw_rows=len(raw_rows), summary_rows=len(summaries),
    )
    _atomic_json(metadata, metadata_path)
    print(f"Đánh giá: {'Thành công' if passed else 'Thất bại'}. Thư mục kết quả: {results_dir.resolve()}")
    print(f"  {raw_path.name}, {summary_path.name}, {metadata_path.name}")
    for path in metadata.get("charts", []):
        print(f"  {Path(path).name}")
    return passed


def _positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("phải là số nguyên dương")
    return number


def regenerate_existing_results(results_dir=RESULTS_DIR):
    """Regenerate Vietnamese outputs without remeasuring or converting labels."""
    from bloxorz.experiments.report_data import generate_report_plots, read_result_rows

    results_dir = Path(results_dir)
    raw_path = results_dir / "benchmark_raw.csv"
    summary_path = results_dir / "benchmark_summary.csv"
    metadata_path = results_dir / "benchmark_metadata.json"
    raw = read_result_rows(raw_path, RAW_COLUMNS)
    summary = read_result_rows(summary_path, SUMMARY_COLUMNS)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    old_status = metadata["status"]
    metadata["status"] = "Đang chạy"
    _atomic_json(metadata, metadata_path)
    _atomic_csv(raw, raw_path)
    _atomic_csv(summary, summary_path)
    try:
        charts = generate_report_plots(summary_path, results_dir)
        metadata["charts"] = [str(path.resolve()) for path in charts]
        metadata["status"] = old_status
    except Exception as exc:
        metadata.update(status="Thất bại", chart_error=_error_text(exc))
        _atomic_json(metadata, metadata_path)
        raise
    _atomic_json(metadata, metadata_path)
    print(f"Đã xuất lại {len(raw)} dòng chi tiết, {len(summary)} dòng tổng hợp "
          f"và {len(charts)} biểu đồ bằng tiếng Việt: {results_dir.resolve()}")
    return old_status == "Thành công"


def main(argv=None):
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=_positive_int, default=5)
    parser.add_argument("--stages-dir", type=Path, default=STAGES_DIR)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--regenerate-existing", "--localize-existing", action="store_true",
                        help="Tạo lại CSV, metadata và biểu đồ từ bộ kết quả tiếng Việt, giữ nguyên số liệu")
    args = parser.parse_args(argv)
    if args.regenerate_existing:
        return 0 if regenerate_existing_results(args.results_dir) else 1
    return 0 if run_benchmark(args.repeats, args.stages_dir, args.results_dir) else 1


if __name__ == "__main__":
    raise SystemExit(main())
