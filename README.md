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
│       ├── ui/                     # WebGL UI và local frontend server
│       │   ├── app.py              # UI Ursina cũ, giữ để tham khảo
│       │   ├── web_server.py       # Static server cho WebGL
│       │   └── web/                # Bloxorz game clone đã tích hợp
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

### 2. Chạy GUI 3D

GUI chính là bản WebGL đã tích hợp từ
[binary-signal/bloxorz-game-clone](https://github.com/binary-signal/bloxorz-game-clone)
và được đặt trong `src/bloxorz/ui/web/`. Python tự khởi động static server cho
frontend, API solver và mở trình duyệt. GUI hỗ trợ chơi thủ công bằng phím mũi
tên, nút `Solve BFS/DFS/UCS/A*`, và tự động replay đường đi từng bước.

```bash
python -m bloxorz.main
```

### 3. Chạy Unit Test kiểm thử
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
4. Tham khảo thiết kế GUI 3D, camera và animation: [chaitanya100100/Bloxorz](https://github.com/chaitanya100100/Bloxorz)
5. Tài liệu rule/help nội bộ của project: [Google Docs](https://docs.google.com/document/d/1Yy9aPwW1z4ImLbhfvEvJebeBONpqBlGOLsTu5EFYhTA/edit?tab=t.0#heading=h.7d63fgbldyxf)

## Phạm vi của GUI & Animation Lead

GUI không cài đặt lại các thuật toán tìm kiếm. Các nút `Solve BFS/DFS/UCS/A*`
chỉ gọi solver do nhóm cung cấp và nhận `SearchResult` hoặc Dictionary chuẩn.
Nếu solver chưa được triển khai, GUI hiển thị thông báo thay vì tạo kết quả giả.
Khi có path, GUI bắt buộc dùng danh sách action để phát lại từng bước qua engine.

## Quyết định kiến trúc GUI WebGL và solver Python

Từ ngày 18/10/2026, nhóm thống nhất dùng
[binary-signal/bloxorz-game-clone](https://github.com/binary-signal/bloxorz-game-clone)
làm nền tảng giao diện 3D. Repo này là frontend **HTML/JavaScript WebGL**, không
phải ứng dụng Java. Vì vậy kiến trúc tích hợp dự kiến là:

```text
WebGL frontend (HTML/JavaScript)
        │ HTTP/JSON
        ▼
Python backend/API
        │
        ├── stage_loader + transition
        └── BFS / DFS / UCS / A*
```

Frontend chịu trách nhiệm render board, điều khiển manual cơ bản, chọn 10 stage,
gọi nút Solve và animate/replay danh sách action. Python vẫn là nơi duy nhất
cài đặt và chạy bốn thuật toán AI. Stage API hiện trả cả metadata fragile,
bridge, switch, teleport và `/transition` dùng chung engine để kiểm tra một
move. Output API dùng giao ước:

```json
{
  "status": "SUCCESS",
  "path": ["RIGHT", "DOWN"],
  "solution_length": 2,
  "search_time": 0.042,
  "peak_memory_mb": 1.25,
  "expanded_nodes": 450
}
```

Nếu bắt buộc dùng Java thay vì JavaScript WebGL, repo tham khảo này không phù
hợp trực tiếp; khi đó cần một client Java riêng (ví dụ JavaFX/OpenGL) gọi cùng
Python API. Không nên port các thuật toán Python sang JavaScript/Java vì yêu cầu
4 thuật toán AI phải được cài đặt bằng Python.

### Chạy WebGL frontend và Python API

Có thể chạy cả frontend và Python API bằng một lệnh:

```powershell
cd "D:\Kì 1 năm 3\CSAI\CSAI-Bloxorz-Solver"
$env:PYTHONPATH = "src"
python -m bloxorz.main
```

Lệnh này tự mở [http://127.0.0.1:8000](http://127.0.0.1:8000). Các nút Solve
trong [`src/bloxorz/ui/web/index.html`](src/bloxorz/ui/web/index.html) gọi API
Python, nhận path và phát lại bằng animation WebGL. API có hai endpoint:

- `/stage?level=1`: lấy grid Python để frontend nạp đúng map trước replay.
- `/solve?level=1&solver=bfs`: lấy kết quả solver theo output contract.

Frontend dùng ô sàn xám trắng kiểu kim loại có viền tối và block màu nâu
cam/rỉ sắt loang theo phong cách hình mẫu. Các texture màu này được tạo trực
tiếp bằng WebGL để hiển thị ổn định; `barel.gif` vẫn được giữ trong repo làm
tài nguyên tham khảo. Camera gần hơn và canvas lớn hơn để bàn cờ rõ hơn.
Layout responsive sẽ đưa sidebar xuống dưới trên màn hình hẹp. Frontend cũng
chặn scroll bằng wheel trên canvas để không làm trượt trang khi chơi, và hiển
thị thông báo/hiệu ứng khi người chơi rơi mất life. Adapter map chuyển floor
`.` của Python thành tile WebGL `p`, đồng thời kiểm tra cả vị trí ngoài biên
trong manual play để block không thể đi xuyên board. Bridge đóng `b` được coi
như void `x` cho tới khi switch mở bridge; block không thể đứng hoặc đi trên
bridge đóng.

Nếu lệnh báo không mở được server, hãy đóng cửa sổ Bloxorz cũ hoặc kiểm tra và
giải phóng hai cổng `8000` và `8001`, rồi chạy lại lệnh. Nếu trình duyệt không
tự bật, mở thủ công [http://127.0.0.1:8000/index.html](http://127.0.0.1:8000/index.html).
