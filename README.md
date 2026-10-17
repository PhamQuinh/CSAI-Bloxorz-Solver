# Bloxorz AI Solver — HCMUS CSAI Project 1

Đồ án môn **Cơ sở Trí tuệ Nhân tạo** — Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM.

---

## 👥 Phân công Công việc Nhóm (5 thành viên)

| Thành viên | Vai trò | Trách nhiệm chính | Deliverables |
|---|---|---|---|
| **TV1 (Leader)** | System Architect & BFS | • Thiết kế Core Engine (`domain/`, `engine/`)<br>• Cài đặt thuật toán `BFS`<br>• Viết bộ Unit Tests (`tests/`)<br>• Quản trị kiến trúc dự án & Git | `src/bloxorz/domain/`<br>`src/bloxorz/engine/`<br>`src/bloxorz/solvers/bfs.py`<br>`tests/` |
| **TV2** | Algorithm Specialist 1 | • Cài đặt `DFS/IDS`<br>• Cài đặt `UCS` với Non-Uniform Cost Function<br>• Biện luận hàm chi phí trong báo cáo | `src/bloxorz/solvers/dfs.py`<br>`src/bloxorz/solvers/ucs.py` |
| **TV3** | Algorithm Specialist 2 | • Cài đặt `A* Search`<br>• Thiết kế các hàm Heuristic (chứng minh Admissible & Consistent)<br>• Cài đặt module đo lường `metrics/` (RAM `tracemalloc`, thời gian, số node) | `src/bloxorz/solvers/astar.py`<br>`src/bloxorz/solvers/heuristics.py`<br>`src/bloxorz/metrics/` |
| **TV4** | GUI & Animation Lead | • Thiết kế giao diện 3D (3D Board & Khối sắt)<br>• Chế độ chơi thủ công (Manual play)<br>• Hoạt ảnh tự động lăn khối sắt khi giải (Auto-replay animation) | `src/bloxorz/ui/`<br>`src/bloxorz/main.py` |
| **TV5** | QA, Benchmark & Report | • Chuẩn bị 10 map test cases JSON độ khó tăng dần<br>• Viết script chạy benchmark tự động 4 thuật toán<br>• Soạn thảo báo cáo PDF & quay dựng Video Demo YouTube | `stages/`<br>`src/bloxorz/experiments/`<br>`results/`<br>`docs/` |

---

## 📁 Cấu trúc Dự án (Clean Architecture & DDD)

```text
bloxorz-project/
├── .gitignore                      # Cấu hình bỏ qua file tạm, cache, ref_*
├── README.md                       # Tài liệu hướng dẫn & phân công
├── requirements.txt                # Thư viện phụ thuộc
├── pyproject.toml                  # Cấu hình package bloxorz chuẩn
├── SPEC.md                         # Đặc tả kỹ thuật chi tiết
│
├── src/
│   └── bloxorz/
│       ├── __init__.py
│       ├── main.py                 # Điểm khởi chạy ứng dụng
│       ├── config.py               # Hằng số cấu hình hệ thống
│       │
│       ├── domain/                 # Mô hình hóa thực thể & luật khái niệm
│       │   ├── __init__.py
│       │   ├── models.py           # TileType, SwitchType, Bridge, Stage
│       │   ├── state.py            # State bất biến, hashable O(1)
│       │   ├── actions.py          # UP, DOWN, LEFT, RIGHT, SWITCH_BLOCK
│       │   └── rules.py            # Luật thắng, vỡ gạch, cơ chế switch
│       │
│       ├── engine/                 # Bộ máy luật chuyển trạng thái
│       │   ├── __init__.py
│       │   ├── transitions.py      # Hàm duy nhất roll_block() dùng chung cho GUI & Solvers
│       │   ├── validation.py       # Kiểm tra hợp lệ (ngoài bảng, rơi vực, fragile)
│       │   └── stage_loader.py     # Đọc file stage JSON thành đối tượng Stage
│       │
│       ├── solvers/                # 4 thuật toán tìm kiếm
│       │   ├── __init__.py
│       │   ├── base.py             # BaseSolver & dataclass SearchResult
│       │   ├── bfs.py              # BFS
│       │   ├── dfs.py              # DFS / IDS
│       │   ├── ucs.py              # UCS với non-uniform cost
│       │   ├── astar.py            # A* Search
│       │   └── heuristics.py       # Hàm Heuristic
│       │
│       ├── metrics/                # Đo đạc hiệu năng chuẩn xác
│       │   ├── __init__.py
│       │   ├── measurement.py      # Đo time, RAM (tracemalloc), expanded nodes
│       │   └── export.py           # Xuất kết quả ra CSV
│       │
│       ├── ui/                     # Giao diện 3D (dành riêng cho TV4)
│       │   └── .gitkeep
│       │
│       └── experiments/            # Thực nghiệm & Benchmark
│           ├── __init__.py
│           ├── benchmark.py        # Benchmark 4 thuật toán x 10 maps
│           └── report_data.py      # Xử lý dữ liệu bảng/biểu đồ
│
├── stages/                         # 10 test case JSON phân loại theo độ khó
├── tests/                          # Bộ Unit Tests tự động
├── results/                        # Dữ liệu CSV kết quả thực nghiệm
└── docs/                           # Báo cáo PDF & Tư liệu video
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### 1. Cài đặt môi trường
Khuyến khích sử dụng môi trường ảo Python (Python 3.9 trở lên):
```bash
# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# Cài đặt package bloxorz ở chế độ editable (giúp import bloxorz ở mọi nơi)
pip install -e .
```

### 2. Chạy Unit Test kiểm thử
```bash
pytest tests/
# hoặc dùng unittest có sẵn của Python:
python -m unittest discover tests
```

---

## 📚 Nguồn tham khảo (Citations)
1. Coolmath Games: [Bloxorz Original Game](https://www.coolmathgames.com/0-bloxorz)
2. Bộ dữ liệu bản đồ & Ground truth: [tkoz0/bloxorz-solver](https://github.com/tkoz0/bloxorz-solver)
3. Tham khảo cơ chế split block: [dpquoc/bloxorz](https://github.com/dpquoc/bloxorz)
