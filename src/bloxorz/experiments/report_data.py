"""Tạo lại năm biểu đồ báo cáo từ CSV tổng hợp bằng tiếng Việt."""
import argparse
import csv
import math
import re
import sys
from pathlib import Path

from bloxorz.config import RESULTS_DIR


ALGORITHMS = ("BFS", "DFS", "UCS", "A*")
METRICS = {
    "Thời gian tìm kiếm (giây)": ("Thời gian tìm kiếm", "Giây", "benchmark_search_time_s.png"),
    "Bộ nhớ đỉnh (MiB)": ("Bộ nhớ đỉnh được tracemalloc theo dõi", "MiB", "benchmark_peak_memory_mb.png"),
    "Số nút mở rộng": ("Số nút mở rộng", "Số nút mở rộng", "benchmark_expanded_nodes.png"),
    "Độ dài lời giải (số hành động)": ("Độ dài lời giải (số hành động)", "Số hành động", "benchmark_solution_length.png"),
    "Số lần lăn": ("Số lần lăn", "Số lần lăn", "benchmark_roll_count.png"),
}


def configure_console():
    """Keep Vietnamese output readable on Windows redirected streams."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def read_result_rows(path, required):
    """Read CSV columns as written, without translating keys or values."""
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        missing = set(required) - set(headers)
        if missing:
            raise ValueError("CSV thiếu cột: " + ", ".join(sorted(missing)))
        if len(headers) != len(set(headers)):
            raise ValueError("CSV có tiêu đề cột trùng lặp")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("Số ô dữ liệu không khớp với số cột CSV")
            rows.append(row)
    return rows


def read_summary(summary_path):
    """Read unique stage/algorithm pairs; missing pairs remain visible in plots."""
    rows = {}
    required = {"Màn chơi", "Thuật toán", "Trạng thái", *METRICS}
    for row in read_result_rows(summary_path, required):
        match = re.fullmatch(r"level_(\d{2})_.+", row["Màn chơi"])
        if not match or not 1 <= int(match[1]) <= 10:
            raise ValueError(f"Màn chơi không thuộc bộ đánh giá: {row['Màn chơi']!r}")
        if row["Thuật toán"] not in ALGORITHMS:
            raise ValueError(f"Thuật toán không thuộc bộ đánh giá: {row['Thuật toán']!r}")
        key = (int(match[1]), row["Thuật toán"])
        if key in rows:
            raise ValueError(f"Cặp màn chơi/thuật toán trùng lặp: {key}")
        rows[key] = row
    return rows


def metric_values(rows, algorithm, metric):
    """Use gaps for failed, absent, or malformed measurements, never zero."""
    values = []
    for stage in range(1, 11):
        row = rows.get((stage, algorithm), {})
        try:
            value = float(row.get(metric, ""))
        except (ValueError, TypeError):
            value = math.nan
        if row.get("Trạng thái") != "Thành công" or not math.isfinite(value) or value < 0:
            value = math.nan
        values.append(value)
    return values


def generate_report_plots(summary_path=RESULTS_DIR / "benchmark_summary.csv", output_dir=None):
    """Save five headless PNGs in numeric stage order and return their paths."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import rc_context

    summary_path = Path(summary_path)
    output_dir = Path(output_dir) if output_dir is not None else summary_path.parent
    rows = read_summary(summary_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    # DejaVu Sans is bundled with Matplotlib and supports Vietnamese diacritics.
    with rc_context({"font.family": "DejaVu Sans"}):
        return _save_plots(plt, rows, output_dir)


def _save_plots(plt, rows, output_dir):
    outputs = []
    markers = ("o", "s", "^", "D")
    colors = ("#0072B2", "#D55E00", "#009E73", "#CC79A7")
    for metric, (title, unit, filename) in METRICS.items():
        fig, ax = plt.subplots(figsize=(11, 5.5))
        try:
            unavailable = []
            for algorithm, marker, color in zip(ALGORITHMS, markers, colors):
                values = metric_values(rows, algorithm, metric)
                ax.plot(range(1, 11), values, label=algorithm, marker=marker,
                        color=color, linewidth=1.7, markersize=5)
                absent = [f"{index:02d}" for index, value in enumerate(values, 1)
                          if math.isnan(value)]
                if absent:
                    unavailable.append(f"{algorithm}: {', '.join(absent)}")
            ax.set(title=title, xlabel="Màn chơi (thứ tự cố định)", ylabel=unit)
            ax.set_xticks(range(1, 11))
            ax.set_xticklabels([f"{stage:02d}" for stage in range(1, 11)])
            ax.set_ylim(bottom=0)
            ax.grid(axis="y", alpha=0.3)
            ax.legend(title="Thuật toán", ncol=4)
            note = "Lời giải đã được kiểm tra bằng cách phát lại hành động."
            if metric in ("Thời gian tìm kiếm (giây)", "Bộ nhớ đỉnh (MiB)"):
                note += " Số liệu là trung vị các lần chạy thành công."
            elif metric == "Số nút mở rộng":
                note += " Đếm số lượt mở rộng; một trạng thái có thể được mở rộng lại."
            elif metric == "Độ dài lời giải (số hành động)":
                note += " Độ dài lời giải tính cả SWITCH_BLOCK."
            else:
                note += " Chỉ đếm UP, DOWN, LEFT và RIGHT; không tính SWITCH_BLOCK."
            note += "\nThứ tự màn chơi không biểu thị độ khó tăng dần."
            if unavailable:
                note += "\nSố liệu thiếu hoặc không đạt yêu cầu (để trống trên biểu đồ):\n" + "\n".join(unavailable)
            fig.text(0.08, 0.02, note, ha="left", va="bottom", fontsize=8)
            footer = 0.09 + 0.025 * (1 + len(unavailable)) if unavailable else 0.09
            fig.tight_layout(rect=(0, footer, 1, 1))
            path = output_dir / filename
            fig.savefig(path, dpi=200)
            outputs.append(path)
        finally:
            plt.close(fig)
    return outputs


def main(argv=None):
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=RESULTS_DIR / "benchmark_summary.csv")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        paths = generate_report_plots(args.summary, args.output_dir)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Không tạo được biểu đồ báo cáo: {exc}\n")
    for path in paths:
        print(path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
