# Bloxorz AI Solver — HCMUS CSAI Project 1

Đồ án môn học **Cơ sở Trí tuệ Nhân tạo** (CSAI / CS202) — Khoa Công nghệ Thông tin, Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM.

Dự án xây dựng hệ thống tự động giải trò chơi giải đố **Bloxorz** bằng các thuật toán tìm kiếm trong không gian trạng thái, tích hợp giao diện tương tác **3D WebGL** hiện đại với cơ chế phát lại hoạt ảnh tự động (Auto-replay animation).

---

## 🌟 Tính năng Nổi bật

* **4 Thuật toán Tìm kiếm Cốt lõi (Python):**
  * **BFS (Breadth-First Search):** Tìm kiếm theo chiều rộng, đảm bảo tìm ra lời giải tối ưu về số bước đi (Step-optimal).
  * **DFS (Depth-First Search):** Tìm kiếm theo chiều sâu với tập `visited` kiểm soát chu trình, tối ưu bộ nhớ.
  * **UCS (Uniform-Cost Search):** Tìm kiếm với chi phí cực tiểu theo mô hình chi phí bước đi không đồng nhất (Non-uniform Cost Function).
  * **A\* Search:** Tìm kiếm có thông tin với hàm Heuristic khoảng cách kết hợp đồ thị dịch chuyển (Portal Graph với Floyd-Warshall), chứng minh đạt tính chất Chấp nhận được (Admissible) và Nhất quán (Consistent).
* **Giao diện 3D WebGL Tương tác:**
  * Mô phỏng không gian 3D trực quan, hỗ trợ chơi thủ công (Manual play bằng các phím mũi tên và Spacebar khi tách khối).
  * Chế độ tự động giải: Khối sắt tự động lật từng bước theo đường đi tối ưu tìm được đến đích.
* **Cơ chế Vật lý & Địa hình Nâng cao (Advanced Tiles):**
  * Xử lý toàn diện các loại địa hình: Ô dễ vỡ (Fragile tiles), Công tắc mềm (Soft switch), Công tắc nặng (Heavy switch), Cầu đóng/mở (Bridges).
  * Cơ chế phân tách khối lập phương $1 \times 1 \times 1$ độc lập qua cổng Teleport và tự động sáp nhập (Auto-merge) khi đứng kề nhau.
* **Hệ thống Đo lường & Benchmark Toàn diện:**
  * Đo đạc 4 chỉ số hiệu năng chuẩn xác: Thời gian tìm kiếm, Dung lượng RAM sử dụng đỉnh (`tracemalloc`), Số nút mở rộng (Expanded nodes), và Độ dài lời giải.
  * Bộ 10 màn chơi kiểm thử phân loại theo độ khó tăng dần kèm bộ nghiệm chuẩn (Ground Truth).

---

## 📁 Cấu trúc Dự án (Clean Architecture)

Hệ thống được thiết kế theo kiến trúc phân tầng (Clean Architecture & Domain-Driven Design), tách biệt hoàn toàn giữa lõi nghiệp vụ vật lý, thuật toán tìm kiếm và giao diện hiển thị:

```text
bloxorz-project/
├── src/
│   └── bloxorz/
│       ├── domain/                 # Mô hình hóa thực thể: State, Action, Stage, Rules
│       ├── engine/                 # Động cơ chuyển trạng thái Single-Source-of-Truth
│       ├── solvers/                # 4 thuật toán AI: BFS, DFS, UCS, A* Search
│       ├── metrics/                # Hệ thống đo đạc hiệu năng (Time, Peak RAM, Nodes)
│       ├── experiments/            # Benchmark tự động 10 màn chơi & xuất biểu đồ
│       ├── ui/                     # Giao diện WebGL 3D và Python API Server
│       └── main.py                 # Điểm khởi chạy toàn bộ hệ thống
├── stages/                         # 10 màn chơi chuẩn format JSON
├── tests/                          # Bộ 55 Unit Tests tự động kiểm thử toàn diện
├── results/                        # Dữ liệu CSV kết quả thực nghiệm & biểu đồ
├── docs/                           # Tài liệu kỹ thuật, báo cáo & phụ lục
├── requirements.txt                # Thư viện phụ thuộc
└── README.md                       # Hướng dẫn cài đặt và sử dụng
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### 1. Cài đặt Môi trường
Khuyến nghị sử dụng Python 3.9 trở lên. Cài đặt các thư viện phụ thuộc bằng lệnh:

```bash
pip install -r requirements.txt
```

---

### 2. Khởi chạy Giao diện 3D WebGL & AI Solver

Chạy toàn bộ hệ thống bằng một câu lệnh duy nhất từ thư mục gốc:

```bash
python -m bloxorz.main
```

Hệ thống sẽ đồng thời:
1. Khởi động Web server phục vụ giao diện 3D tại cổng `8000`.
2. Khởi động Python API Server phục vụ 4 thuật toán giải đố tại cổng `8001`.
3. Tự động mở trình duyệt web tại địa chỉ: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

**Hướng dẫn thao tác trên giao diện:**
* **Chơi thủ công:** Sử dụng các phím mũi tên `↑`, `↓`, `←`, `→` để điều khiển khối sắt. Nhấn `Spacebar` để chuyển đổi khối khi đang ở trạng thái phân tách.
* **Tự động giải:** Chọn màn chơi (Level 1–10) từ thanh điều khiển, chọn thuật toán (`Solve BFS`, `Solve DFS`, `Solve UCS`, hoặc `Solve A*`). Khối sắt sẽ tự động lăn theo nghiệm tìm được đến khi rơi vào lỗ đích.

---

### 3. Chạy Benchmark Tự động 10 Màn chơi

Để chạy kiểm thử tự động toàn bộ 4 thuật toán trên 10 màn chơi và xuất dữ liệu thống kê:

```bash
python -m bloxorz.experiments.benchmark
```

Kết quả sẽ được tự động xuất ra file tổng hợp tại `results/benchmark_summary.csv` và tạo các biểu đồ phân tích trực quan trong thư mục `results/`.

---

### 4. Chạy Bộ Kiểm thử Đơn vị (Unit Tests)

Hệ thống tích hợp bộ 55 Unit Tests tự động kiểm tra chặt chẽ tính đúng đắn của logic vật lý, cơ chế nâng cao và kết quả của các thuật toán:

```bash
python -m unittest discover tests
```

---

## 📚 Nguồn Tham khảo (Citations)

1. **Coolmath Games:** [Bloxorz Original Flash Game](https://www.coolmathgames.com/0-bloxorz) — Luật chơi và thiết kế màn chơi gốc.
2. **tkoz0/bloxorz-solver:** [Dataset & Ground Truth Solutions](https://github.com/tkoz0/bloxorz-solver) — Bộ dữ liệu bản đồ mẫu và nghiệm tối ưu.
3. **binary-signal/bloxorz-game-clone:** [WebGL 3D Engine](https://github.com/binary-signal/bloxorz-game-clone) — Khung nền tảng WebGL 3D, camera và shader.
4. **Stuart Russell & Peter Norvig:** *Artificial Intelligence: A Modern Approach (4th Edition)* — Lý thuyết nền tảng về các thuật toán tìm kiếm trong không gian trạng thái.
