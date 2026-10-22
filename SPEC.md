# SPEC.md — Đặc tả Kỹ thuật Đồ án AI: Bloxorz Solver
**Môn học:** Cơ sở Trí tuệ Nhân tạo — HCMUS  
**Nhóm:** 5 thành viên | **Mục tiêu:** Sprint 7 ngày hoàn thành

---

## 1. TỔNG QUAN ĐỀ BÀI

Xây dựng hệ thống giải trò chơi **Bloxorz** (lăn khối sắt 1×1×2 trên lưới ô vuông, đưa khối đứng thẳng vào lỗ đích) bao gồm:
- Game hoàn chỉnh với GUI **3D** (theo yêu cầu Q&A của Giảng viên)
- 4 thuật toán tìm kiếm: **BFS, DFS (hoặc IDS), UCS, A\***
- Tối thiểu 10 test cases, đo đạc 4 chỉ số hiệu năng (Time, Memory, Nodes Expanded, Path Length)
- Báo cáo PDF + Video Demo YouTube

### Điểm số theo barem:
| Hạng mục | Điểm |
|---|---|
| Game cơ bản (Core mechanics) | 10đ |
| Advanced tiles (Fragile, Switch, Bridge, Split) | 10đ |
| BFS | 10đ |
| DFS/IDS | 10đ |
| UCS | 10đ |
| A* | 10đ |
| Báo cáo PDF | 30đ |
| Video Demo YouTube | 10đ |

---

## 2. QUY TẮC "SỐNG CÒN" TỪ BẢNG Q&A GIẢNG VIÊN

| # | Câu hỏi | Trả lời chính thức |
|---|---|---|
| 1 | GUI dạng gì? | **3D nha** |
| 2 | Số test cases? | **Tối thiểu 10** |
| 3 | Bấm Solve thì hiện gì? | **GUI tự cho khối sắt lăn đến đích luôn** (Animation) |
| 4 | Dùng source code có sẵn? | **Được (nhớ cite đầy đủ)** |
| 5 | GUI code ngôn ngữ khác? | **Được, chỉ riêng thuật toán thì bằng Python** |
| 6 | UCS uniform cost? | **Phải thiết kế non-uniform cost và biện luận** |
| 7 | Báo cáo tiếng gì? | **Tùy, nhưng thống nhất, tránh nửa Việt nửa Anh** |

---

## 3. LUẬT CHƠI — MÔ HÌNH HÓA BÀI TOÁN

### 3.1 Khối sắt 1×1×2 — 3 hướng (Orientation):
```
STANDING:    Chiếm đúng 1 ô (r, c)
LYING_ROW:   Chiếm 2 ô kề nhau (r, c) và (r, c+1)  — nằm ngang
LYING_COL:   Chiếm 2 ô kề nhau (r, c) và (r+1, c)  — nằm dọc
```

### 3.2 Bảng chuyển trạng thái (Transition Table):
```
Từ STANDING + UP    → LYING_COL   tại (r-2, c)&(r-1, c)
Từ STANDING + DOWN  → LYING_COL   tại (r+1, c)&(r+2, c)
Từ STANDING + LEFT  → LYING_ROW   tại (r, c-2)&(r, c-1)
Từ STANDING + RIGHT → LYING_ROW   tại (r, c+1)&(r, c+2)

Từ LYING_COL + UP    → STANDING   tại (r-1, c)
Từ LYING_COL + DOWN  → STANDING   tại (r+2, c)
Từ LYING_COL + LEFT  → LYING_COL  tại (r, c-1)&(r+1, c-1)
Từ LYING_COL + RIGHT → LYING_COL  tại (r, c+1)&(r+1, c+1)

Từ LYING_ROW + UP    → LYING_ROW  tại (r-1, c)&(r-1, c+1)
Từ LYING_ROW + DOWN  → LYING_ROW  tại (r+1, c)&(r+1, c+1)
Từ LYING_ROW + LEFT  → STANDING   tại (r, c-1)
Từ LYING_ROW + RIGHT → STANDING   tại (r, c+2)
```

### 3.3 Ký hiệu ô trên bản đồ (chuẩn map format):
```
' '  → Void (ô trống — rơi xuống = thua)
'.'  → Floor (sàn bình thường)
'-'  → Fragile (ô dễ vỡ — không đứng thẳng lên được)
'S'  → Start (vị trí ban đầu)
'H'  → Hole/Goal (lỗ đích)
'O'  → Soft switch (bật khi khối đứng/nằm đè lên)
'X'  → Heavy switch (chỉ bật khi khối ĐỨNG THẲNG lên)
'B'  → Bridge đang MỞ (đi được)
'b'  → Bridge đang ĐÓNG (= void)
'T'  → Teleport/Split switch (đứng thẳng lên → tách 2 khối nhỏ)
```

### 3.4 Luật thắng/thua:
- **Thắng:** Khối **ĐỨNG THẲNG** vào ô 'H' (nằm đè qua lỗ thì KHÔNG thắng)
- **Thua:** Bất kỳ phần nào của khối rơi vào Void hoặc ngoài bản đồ
- **Fragile:** Khối STANDING đè lên → ô vỡ → thua

### 3.5 Cơ chế Split Block:
- Đứng thẳng lên 'T' → tách thành 2 khối lập phương 1×1×1
- Điều khiển từng khối bằng phím đổi khối (hoặc mở rộng action space)
- Khối nhỏ kích hoạt được Soft switch, KHÔNG kích hoạt Heavy switch
- Khối nhỏ KHÔNG thể vào đích
- 2 khối nhỏ đi sát nhau → tự ghép lại thành khối 1×1×2

---

## 4. MÔ HÌNH HÓA STATE SPACE

### 4.1 Định nghĩa State (Trạng thái):
```python
State = (block_status, bridges_state)

# Trường hợp 1 khối 1×1×2:
block_status = (orientation, row, col)
# orientation ∈ {'STANDING', 'LYING_ROW', 'LYING_COL'}

# Trường hợp bị tách (split):
block_status = ('SPLIT', r1, c1, r2, c2, active_cube)
# active_cube ∈ {0, 1} — khối nào đang được điều khiển

# Trạng thái cầu (immutable tuple để có thể hash):
bridges_state = (True, False, True, ...)
```

### 4.2 Hành động (Actions):
```
Chuẩn 4 hành động: "UP", "DOWN", "LEFT", "RIGHT"
Khi bị split: bổ sung "SWITCH_BLOCK" (đổi điều khiển)
```

### 4.3 Output chuẩn của mọi Solver:
```python
{
    "status": "SUCCESS",           # hoặc "FAILED"
    "path": ["RIGHT", "DOWN", ...], # danh sách bước đi
    "solution_length": 15,          # số bước
    "search_time": 0.042,           # giây
    "peak_memory_mb": 1.25,         # MB (đo bằng tracemalloc)
    "expanded_nodes": 450           # số node đã duyệt
}
```

---

## 5. CẤU TRÚC THƯ MỤC DỰ ÁN

```
Bloxorz-AI-Solver/
├── .gitignore
├── README.md                    # Mô tả dự án, cài đặt, phân công nhóm
├── requirements.txt
├── maps/                        # 10+ file map test case
│   ├── level_01.json            # Map cơ bản (từ coolmath.json của tkoz0)
│   ├── level_02.json
│   ├── ...
│   └── level_10.json
├── src/
│   ├── engine/                  # Logic game cốt lõi
│   │   ├── __init__.py
│   │   ├── state.py             # Class State (vị trí, orientation, bridges)
│   │   └── game.py              # BloxorzProblem: get_actions, get_successor, is_goal
│   ├── solvers/                 # 4 thuật toán tìm kiếm
│   │   ├── __init__.py
│   │   ├── base_solver.py       # Lớp cơ sở + đo metrics (tracemalloc, time)
│   │   ├── bfs.py
│   │   ├── dfs.py               # DFS/IDS với visited set
│   │   ├── ucs.py               # UCS với non-uniform cost function
│   │   ├── astar.py             # A* với heuristic admissible
│   │   └── heuristics.py        # Các hàm heuristic + chứng minh admissible
│   ├── gui/                     # Giao diện 3D
│   │   ├── __init__.py
│   │   └── main_gui.py          # GUI chính (Ursina/Pygame 2.5D/Three.js)
│   └── benchmark/               # Đo lường hiệu năng
│       ├── __init__.py
│       ├── metrics.py           # Hàm đo time, RAM, nodes
│       └── benchmark.py         # Chạy tự động 4 thuật toán × 10 maps
├── docs/                        # Tài liệu
│   ├── Report.pdf
│   └── figures/                 # Ảnh biểu đồ benchmark
└── main.py                      # Entry point: chạy GUI
```

---

## 6. ĐẶC TẢ KỸ THUẬT CÁC MODULE

### 6.1 `src/engine/game.py` — Interface bắt buộc:
```python
class BloxorzProblem:
    def get_initial_state(self) -> State:
        """Trả về trạng thái ban đầu"""
        pass

    def get_actions(self, state: State) -> List[str]:
        """Trả về ['UP', 'DOWN', 'LEFT', 'RIGHT', ...] hợp lệ từ state này"""
        pass

    def get_successor(self, state: State, action: str) -> Optional[State]:
        """Trả về trạng thái tiếp theo, None nếu bước đi không hợp lệ"""
        pass

    def is_goal(self, state: State) -> bool:
        """True nếu khối đang STANDING trên ô 'H'"""
        pass

    def get_cost(self, state: State, action: str) -> float:
        """Chi phí bước đi (dùng cho UCS, A*)"""
        pass
```

### 6.2 `src/solvers/ucs.py` — Hàm Chi phí Non-Uniform:
```python
# Gợi ý thiết kế cost (phải biện luận trong báo cáo):
BASE_COST = 2           # Lăn thông thường
FRAGILE_COST = 4        # Lăn qua ô fragile (rủi ro cao)
SWITCH_COST = 1         # Đạp switch mở đường (khuyến khích)
SPLIT_COST = 3          # Thao tác khi ở trạng thái split

# Lý do UCS ≠ BFS: cost không đồng nhất → UCS tìm
# đường ít chi phí nhất, không nhất thiết ít bước nhất
```

### 6.3 `src/solvers/heuristics.py` — Heuristic cho A\*:
```python
def manhattan_half(state, stage) -> float:
    """
    Cận dưới chi phí còn lại của step_cost, có tính ô tách.
    Không teleport: c_min * max(khoảng cách tâm / 2, số nước để ghép).
    Có teleport: lấy min với đường qua từng ô T rồi từ chỗ rơi tới lỗ.
    Một nước T có thể giảm h nhiều hơn chi phí nước đó, nên không
    kết luận consistent; A* mở lại node khi g nhỏ hơn.
    """

def manhattan_half_with_orientation_penalty(state, stage) -> float:
    """
    h1 cộng thêm c_min khi khối chưa đứng nguyên.
    Phần cộng thêm có thể vượt chi phí còn lại. A* không dùng hàm này.
    """
```

### 6.4 Định dạng File Map JSON:
```json
{
    "name": "Stage 01",
    "grid": [
        "...       ",
        ".S....    ",
        "......... ",
        " .........",
        "     ..H..",
        "      ... "
    ],
    "passcode": "780464",
    "bridges": [
        [[4,4],[4,5]],
        [[4,10],[4,11]]
    ],
    "switches": [
        [2, 2, [[0, "swap"]]],
        [1, 8, [[1, "swap"]]]
    ],
    "teleports": [
        [3, 5, 1, 2, 5, 8, 0]
    ]
}
```

---

## 7. 10 TEST CASES PHÂN LOẠI ĐỘ KHÓ

| Level | File | Nội dung | Nguồn |
|---|---|---|---|
| 1–3 | level_01 → 03 | **Cơ bản**: chỉ sàn và đích | Từ coolmath.json Stage 1–3 |
| 4–5 | level_04 → 05 | **Có ô fragile** | Stage 4–5 |
| 6–7 | level_06 → 07 | **Có bridge + soft/heavy switch** | Stage 6–8 |
| 8–9 | level_08 → 09 | **Kết hợp nhiều tính năng** | Stage 10–15 |
| 10 | level_10 | **Có teleport/split block** | Stage có 'T' |

**Bộ đáp án chuẩn (Ground Truth từ `tkoz0/solution.txt`):**  
Stage 1–10: 7, 17, 19, 28, 33, 35, 44, 10, 24, 57 (số bước tối ưu)  
→ Dùng để kiểm tra BFS/A* có cho ra nghiệm tối ưu không.

---

## 8. PHÂN CHIA CÔNG VIỆC NHÓM 5 NGƯỜI

| Thành viên | Vai trò | Công việc | Deliverables |
|---|---|---|---|
| **TV1 (Leader)** | System Architect + BFS | Thiết kế `State`, `BloxorzProblem`; cài `game.py` đầy đủ (core + advanced); cài `bfs.py`; quản lý GitHub | `src/engine/`, `src/solvers/bfs.py` |
| **TV2** | Algorithm Specialist 1 | Cài `dfs.py` (với visited set), `ucs.py` (non-uniform cost); biện luận cost function | `src/solvers/dfs.py`, `ucs.py` |
| **TV3** | Algorithm Specialist 2 | Cài `astar.py`, `heuristics.py` (≥2 heuristic, chứng minh admissible/consistent), module đo metrics | `src/solvers/astar.py`, `heuristics.py`, `metrics.py` |
| **TV4** | GUI & Animation Lead | Giao diện 3D (Ursina/Pygame/Web); render bàn cờ + khối sắt; manual play; **Auto-replay animation** | `src/gui/` |
| **TV5** | QA + Report + Video | 10 file map JSON; script `benchmark.py`; biểu đồ; `Report.pdf`; Video YouTube | `maps/`, `benchmark.py`, `Report.pdf`, YouTube link |

---

## 9. DEADLINE 7 NGÀY (SPRINT)

| Ngày | Mục tiêu |
|---|---|
| **Ngày 1** | Tạo GitHub repo, up cấu trúc thư mục. TV5 up 5 map đầu. TV4 dựng khung GUI 3D |
| **Ngày 2** | TV1 hoàn thành `game.py` (core + advanced) + `bfs.py`. TV5 hoàn thành 10 map |
| **Ngày 3** | TV2 xong `dfs.py` + `ucs.py`. TV3 xong `astar.py` + `metrics.py` |
| **Ngày 4** | TV4 tích hợp thuật toán vào GUI, hoàn thiện Auto-replay animation |
| **Ngày 5** | TV3+TV5 chạy benchmark 4 thuật toán × 10 map, vẽ biểu đồ |
| **Ngày 6** | TV5+TV1 hoàn thành `Report.pdf`. TV4+TV5 quay/dựng Video Demo YouTube |
| **Ngày 7** | Họp vấn đáp thử nội bộ, đóng gói `.zip` theo MSSV, nộp bài |

---

## 10. REPO THAM KHẢO ĐÃ PHÂN TÍCH

| Repo | Đánh giá | Dùng vào việc gì |
|---|---|---|
| **`tkoz0/bloxorz-solver`** ⭐⭐⭐⭐⭐ | Python, 33 map chuẩn JSON, có đáp án tối ưu | **Lấy `coolmath.json`** làm 10 map; lấy `solution.txt` làm ground truth |
| **`dpquoc/bloxorz`** ⭐⭐⭐⭐ | Python, có class State/Map, có BFS/DFS/A*, có logic split block | Tham khảo `Class/state.py` (bảng chuyển trạng thái), logic switch/bridge |
| **`chaitanya100100/Bloxorz`** ⚠️ | C++ OpenGL — **KHÔNG DÙNG CODE** | Chỉ xem demo GIF để biết giao diện 3D trông như thế nào |

---

## 11. HƯỚNG DẪN LỰA CHỌN CÔNG NGHỆ GUI 3D

| Lựa chọn | Ưu điểm | Nhược điểm |
|---|---|---|
| **Python Ursina Engine** ⭐ Khuyên dùng | Thuần Python, dễ kết nối solver, 3D thật, code ngắn | Cần cài đặt gói ursina |
| **Pygame 2.5D Isometric** | Quen thuộc, nhiều tài liệu | Chỉ là 2.5D giả |
| **Web Three.js + Python FastAPI** | Đồ họa 3D cực đẹp | Cần setup backend API, phức tạp hơn |

---

## 12. YÊU CẦU BÁO CÁO PDF (30 điểm)

Cấu trúc bắt buộc:
1. **Bảng phân công** (% đóng góp từng người)
2. **Mô hình hóa bài toán (10đ):** State $S$, Action $A$, Transition $T$, Goal Test, Cost Function, Heuristic Function
3. **Thực nghiệm (20đ):**
   - Bảng số liệu 4 thông số × 4 thuật toán × 10 maps
   - Biểu đồ so sánh (Bar chart/Line plot)
   - Nhận xét phân tích ưu/nhược điểm từng thuật toán
4. **Chứng minh Heuristic:** Admissible + Consistent
5. **Biện luận Non-uniform Cost** của UCS
6. **References & Phụ lục:** Link repo tham khảo, các prompt AI/LLM đã dùng

---

## 13. YÊU CẦU VIDEO DEMO (10 điểm)

- Upload YouTube (Public hoặc Unlisted), thời lượng 5–7 phút, 1080p
- Có voice-over hoặc phụ đề (Việt hoặc Anh)
- Nội dung:
  1. Demo giao diện 3D (5đ)
  2. Demo chơi bằng tay (Manual play)
  3. Demo chọn thuật toán → bấm Solve → **khối sắt tự lăn đến đích** (5đ)
- Dán link YouTube vào Report.pdf

---

## 14. ĐỊNH DẠNG NỘP BÀI

```
MSSV1_MSSV2_MSSV3_MSSV4_MSSV5.zip
├── Source/
│   ├── main.py
│   ├── src/
│   ├── maps/
│   ├── requirements.txt
│   └── README.md
└── Report.pdf     ← đã chèn link YouTube video demo
```

---

## 15. CÁC CÔNG THỨC TOÁN HỌC CẦN TRÌNH BÀY TRONG BÁO CÁO

### Heuristic Admissible (A\*):
$$h_1(n) = \frac{|r_n - r_{goal}| + |c_n - c_{goal}|}{2}$$
*Mỗi bước lăn khối tối đa dịch 2 ô → /2 luôn ≤ chi phí thực tế → Admissible*

### Heuristic Consistent:
$$h(n) \leq c(n, n') + h(n') \quad \forall \text{ bước đi } n \rightarrow n'$$

### Điểm cá nhân:
$$\text{Điểm cá nhân} = \text{Điểm nhóm} \times \% \text{ hoàn thành}$$

---
*Tài liệu tóm tắt đầy đủ để nạp ngữ cảnh vào conversation mới.*
