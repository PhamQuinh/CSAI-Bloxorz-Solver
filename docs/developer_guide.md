# Hướng Dẫn Phát Triển Dành Cho Các Thành Viên (Developer Guide)
> **Môn học:** Cơ sở Trí tuệ Nhân tạo — HCMUS  
> **Tác giả:** TV1 (Leader) — System Architect  
> **Dành cho:** TV2, TV3, TV4, TV5

---

## 1. KHỞI TẠO MÔI TRƯỜNG LÀM VIỆC

Khi clone repo về máy, mỗi thành viên mở terminal trong thư mục dự án và chạy:
```bash
# 1. Cài đặt các thư viện cơ bản
pip install -r requirements.txt

# 2. Cài đặt package bloxorz ở chế độ editable
pip install -e .

# 3. Chạy thử bộ unit test để đảm bảo môi trường hoạt động tốt:
python -m unittest discover tests
```

---

## 2. QUY TẮC PHỐI HỢP GIT (TRÁNH CONFLICT)

1. **Tuyệt đối không push thẳng lên `main`**.
2. Mỗi thành viên tạo một nhánh (branch) riêng mang tên mình:
   - TV2: `git checkout -b feat/tv2-dfs-ucs`
   - TV3: `git checkout -b feat/tv3-astar-metrics`
   - TV4: `git checkout -b feat/tv4-3d-gui`
   - TV5: `git checkout -b feat/tv5-benchmark-report`
3. Khi hoàn thành, push nhánh lên GitHub và tạo **Pull Request (PR)** để Leader review merge vào `main`.

---

## 3. HƯỚNG DẪN DÀNH CHO TV2 (DFS & UCS)

### Tệp phụ trách:
- `src/bloxorz/solvers/dfs.py`
- `src/bloxorz/solvers/ucs.py`

### 3.1 Cài đặt DFS / IDS (`dfs.py`)
- Kế thừa lớp `BaseSolver` từ `bloxorz.solvers.base`.
- Dùng `list` làm `stack` (LIFO) và `set` làm `visited` để tránh chu trình lặp vô hạn.
- Mẫu code gợi ý:
```python
from collections import deque
from bloxorz.domain.state import State
from bloxorz.domain.actions import Action
from bloxorz.domain.rules import is_goal_state
from bloxorz.engine.transitions import transition
from bloxorz.solvers.base import BaseSolver, SearchResult
from bloxorz.metrics.measurement import measure_performance

class DFSSolver(BaseSolver):
    def solve(self) -> SearchResult:
        with measure_performance() as m:
            # Dùng stack = [(initial_state, [path])]
            # Duyệt LIFO và cập nhật m["expanded_nodes"]
            pass
```

### 3.2 Cài đặt UCS (`ucs.py`)
- Dùng `heapq` làm Priority Queue: `heapq.heappush(pq, (cost, count, state, path))`.
- Định nghĩa hàm chi phí Non-Uniform Cost theo gợi ý ở `docs/problem_formulation.md`.

---

## 4. HƯỚNG DẪN DÀNH CHO TV3 (A* & METRICS)

### Tệp phụ trách:
- `src/bloxorz/solvers/astar.py`
- `src/bloxorz/solvers/heuristics.py`
- `src/bloxorz/metrics/measurement.py`

### 4.1 Cài đặt A* Search (`astar.py`)
- Dùng Priority Queue với độ ưu tiên $f(n) = g(n) + h(n)$.
- $g(n)$: Chi phí tích lũy từ gốc đến node hiện tại.
- $h(n)$: `manhattan_half` trong `heuristics.py`. Hàm này là cận dưới của `step_cost`, kể cả khi đường đi đứng lên ô tách. `manhattan_half_with_orientation_penalty` cộng thêm một bước khi khối chưa đứng; lượng cộng thêm có thể vượt chi phí còn lại, nên không đưa vào A*.
- Duy trì từ điển `cost_so_far: Dict[State, float]` để cập nhật đường đi tốt hơn nếu tìm thấy $g(n)$ nhỏ hơn.

---

## 5. HƯỚNG DẪN DÀNH CHO TV4 (GUI 3D & ANIMATION)

### Tệp phụ trách:
- `src/bloxorz/ui/`
- `src/bloxorz/main.py`

### 5.1 Cách nạp bản đồ:
```python
from bloxorz.config import STAGES_DIR
from bloxorz.engine.stage_loader import load_stage

# Nạp một màn chơi JSON
stage = load_stage(STAGES_DIR / "level_01_basic.json")
# Các thuộc tính: stage.rows, stage.cols, stage.grid, stage.start_pos, stage.goal_pos
```

### 5.2 Cách gọi Solver và lấy đường đi:
```python
from bloxorz.solvers.bfs import BFSSolver

solver = BFSSolver(stage)
result = solver.solve()

if result.found:
    print(f"Số bước: {result.solution_length}")
    print(f"Thời gian: {result.search_time:.4f}s")
    actions = result.actions  # Danh sách các Action: [Action.RIGHT, Action.DOWN, ...]
```

### 5.3 Cách làm hoạt ảnh tự lăn (Auto-replay Animation):
Chỉ cần gọi hàm `transition()` duy nhất của Engine để lấy trạng thái tiếp theo của khối:
```python
from bloxorz.engine.transitions import transition

current_state = initial_state
for act in result.actions:
    current_state = transition(current_state, act, stage)
    # Cập nhật vị trí và góc xoay 3D của khối sắt trên màn hình
```

---

## 6. HƯỚNG DẪN DÀNH CHO TV5 (BENCHMARK & REPORT)

### Tệp phụ trách:
- `src/bloxorz/experiments/benchmark.py`
- `src/bloxorz/experiments/report_data.py`
- `results/`
- `docs/report/`

### 6.1 Chạy Benchmark tự động:
- Lặp qua 10 files trong thư mục `stages/`:
  - `level_01_basic.json` đến `level_10_split_complex.json`.
- Với mỗi map, chạy lần lượt 4 Solvers (`BFS`, `DFS`, `UCS`, `A*`).
- Thu thập 4 thông số: `Search Time`, `Peak Memory MB`, `Expanded Nodes`, `Solution Length`.
- Ghi vào `results/benchmark_results.csv` bằng hàm `export_to_csv()`.
- So sánh nghiệm của BFS/A* với file chuẩn `stages/ground_truth_solutions.txt`.
