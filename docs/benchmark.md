# Chạy benchmark và sử dụng kết quả trong báo cáo

Chạy từ thư mục gốc bằng PowerShell và môi trường `.venv` (Python từ 3.9;
môi trường hiện tại dùng Python 3.14.0):

```powershell
# Mặc định: 5 lần lặp, 200 dòng chi tiết, 40 dòng tổng hợp và 4 biểu đồ.
.\.venv\Scripts\python.exe -m bloxorz.experiments.benchmark

# Chạy thử một lần cho mỗi cặp màn chơi/thuật toán.
.\.venv\Scripts\python.exe -m bloxorz.experiments.benchmark --repeats 1

# Tạo lại các tệp từ bộ kết quả tiếng Việt hiện có, giữ nguyên từng số liệu.
.\.venv\Scripts\python.exe -m bloxorz.experiments.benchmark --regenerate-existing

# Tạo lại biểu đồ từ CSV tổng hợp tiếng Việt, không chạy lại tìm kiếm.
.\.venv\Scripts\python.exe -m bloxorz.experiments.report_data

# Chạy toàn bộ kiểm thử.
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

`benchmark` nhận `--repeats N` (số nguyên dương), `--stages-dir PATH`,
`--results-dir PATH` và `--regenerate-existing`. Hai thư mục mặc định là
`bloxorz.config.STAGES_DIR` và `RESULTS_DIR`, tương ứng `stages/` và `results/`.
`report_data` nhận `--summary PATH`, `--output-dir PATH`; mặc định lưu biểu đồ
cùng thư mục với CSV đầu vào. Thư mục màn chơi tùy chọn phải chứa đúng mười tên
tệp được khai báo trong `STAGE_FILES`.

`--regenerate-existing` đọc bộ CSV tiếng Việt hiện có, xuất lại cả hai CSV,
metadata và bốn PNG ngay tại các tên tệp cũ. Lệnh giữ nguyên chuỗi số trong từng
ô, đường đi, số lần lặp, thời điểm đo, môi trường, đường dẫn và mã hash; không
chạy solver. Có thể dùng lặp lại mà không làm thay đổi số liệu. Tên tùy chọn cũ
`--localize-existing` vẫn được chấp nhận như một bí danh của lệnh này; lệnh không
còn chuyển đổi CSV tiếng Anh. Chạy benchmark mới sẽ đo lại thời gian/bộ nhớ nên
các giá trị đó có thể thay đổi theo điều kiện máy.

## Quy trình đo và nhóm màn chơi

Chạy trên cùng máy, đóng GUI và tránh tác vụ nặng. Thứ tự cố định: màn 01–10;
mỗi màn chạy BFS, DFS, UCS, A*. Mỗi thuật toán chạy các lần lặp liên tiếp, dùng
solver mới cho từng lần, không có lượt khởi động. Lấy trực tiếp số đo trong
`SearchResult`: phạm vi `.solve()` gồm tìm kiếm và dựng lại đường đi. Việc nạp
màn, kiểm tra lời giải, tính chi phí, ghi CSV và vẽ biểu đồ nằm ngoài phạm vi đo.
Bộ nhớ là cấp phát Python được tracemalloc theo dõi, tính bằng **MiB**, không
phải toàn bộ RAM của tiến trình. Thời gian và bộ nhớ có thể dao động giữa các lần chạy.

Mỗi lời giải phải phát lại hợp lệ từ vị trí xuất phát với cấu hình cầu ban đầu,
`active_cube=-1`, và kết thúc bằng khối đứng trên đích. Trạng thái gồm vị trí,
hướng khối, trạng thái cầu và khối con đang điều khiển khi tách. Mười JSON dùng
chung cho cả bốn thuật toán. Nhóm được xác định từ nội dung, không suy từ tên tệp:

| Nhóm màn chơi | Màn | Đặc điểm |
| --- | --- | --- |
| Sàn thường | 01, 03, 06 | Không có ô đặc biệt; 06 là mê cung lớn hơn |
| Ô dễ vỡ | 04 | Có ô `-` |
| Công tắc và cầu | 02, 05, 07 | Công tắc mềm/nặng và cầu; 05 có on/off/swap |
| Tách khối | 08, 09 | Công tắc tách, hai khối con, ghép lại; 09 có đường đi dài hơn |
| Tách khối kết hợp công tắc và cầu | 10 | Tách khối, công tắc mềm/nặng và cầu |

Màn 05 không có ô dễ vỡ; màn 06 không có công tắc hay cầu. Thứ tự màn không
biểu thị độ khó tăng dần.

## Tệp kết quả và các cột CSV

Tên tệp giữ nguyên để các lệnh và đường dẫn hoạt động ổn định:

- `benchmark_raw.csv`: từng lần chạy, kể cả thất bại.
- `benchmark_summary.csv`: một dòng cho mỗi cặp màn chơi/thuật toán.
- `benchmark_metadata.json`: thông tin lần đo, môi trường, quy ước và mã hash.
- `benchmark_search_time_s.png`: thời gian tìm kiếm.
- `benchmark_peak_memory_mb.png`: bộ nhớ đỉnh.
- `benchmark_expanded_nodes.png`: số nút mở rộng.
- `benchmark_solution_length.png`: độ dài lời giải (số hành động).

CSV dùng **UTF-8 có BOM** để Excel nhận đúng dấu tiếng Việt. Ô số không chứa
đơn vị; ô trống biểu thị thiếu dữ liệu. Giá trị tìm thấy lời giải là **Có/Không**.
Tên biến, hàm và thuộc tính của solver vẫn dùng tiếng Anh. Các dòng kết quả
trong `benchmark.py` dùng trực tiếp khóa và giá trị hiển thị tiếng Việt, ví dụ
`row["Số nút mở rộng"] = result.expanded_nodes`. `report_data.py` đọc nguyên
những tiêu đề đó; không có lớp ánh xạ hoặc chuyển đổi ngôn ngữ khi ghi/đọc.

| Tiêu đề CSV | Ý nghĩa / đơn vị |
| --- | --- |
| Màn chơi | Tên tệp JSON bỏ phần `.json`, giữ nguyên định danh |
| Nhóm màn chơi | Nhóm ở bảng trên; Chưa xác định nếu không nạp được |
| Thuật toán | BFS, DFS, UCS, A* |
| Lần chạy | Đánh số từ 1, chỉ có trong CSV chi tiết |
| Trạng thái | Nhãn kết quả tiếng Việt bên dưới |
| Tìm thấy lời giải | Kết quả do solver trả về; trống khi chưa nhận được kết quả |
| Số lần chạy thành công | Số lần thành công đã kiểm tra lời giải, chỉ có trong CSV tổng hợp |
| Thời gian tìm kiếm (giây) | `SearchResult.search_time` |
| Bộ nhớ đỉnh (MiB) | `SearchResult.peak_memory_mb` |
| Số nút mở rộng | Số lượt mở rộng, không đếm đích; một trạng thái có thể được mở rộng lại |
| Độ dài lời giải (số hành động) | `len(actions)`, tính cả **SWITCH_BLOCK** |
| Chi phí đường đi | Tổng `step_cost` khi phát lại lời giải |
| Số lần lăn | Chỉ đếm UP/DOWN/LEFT/RIGHT |
| Chuỗi hành động | Giữ nguyên định danh hành động, phân cách bằng dấu cách; chỉ có trong CSV chi tiết |
| Lỗi | Lỗi kiểm tra, ngoại lệ hoặc chênh lệch giữa các lần chạy |

CSV tổng hợp lấy **trung vị các lần thành công đã kiểm tra** cho thời gian và
bộ nhớ. Các trường kết quả ổn định không được lấy trung bình; trường khác nhau
để trống và báo lỗi. Nếu một số lần thất bại, trung vị thành công có thể còn
trong CSV để kiểm tra, nhưng biểu đồ chỉ vẽ các cặp có trạng thái Thành công.
Không có lần thành công thì để trống trung vị; số đo của lần tìm kiếm không có
lời giải vẫn được giữ ở CSV chi tiết. Ngoại lệ không được thay bằng số đo 0.

| Trạng thái | Ý nghĩa |
| --- | --- |
| Đang chạy | Metadata: chưa hoàn tất |
| Thành công | Lời giải đã qua kiểm tra |
| Không tìm thấy lời giải | Solver trả `found=False` |
| Lỗi thực thi | Ngoại lệ nạp màn hoặc tìm kiếm |
| Không hợp lệ | Số đo sai, đường đi sai, không đến đích hoặc sai độ dài |
| Thất bại | Các lần có trạng thái khác nhau hoặc lỗi tạo biểu đồ |
| Không nhất quán | Khác kết quả tìm thấy, số nút, độ dài, chi phí hoặc số lần lăn |

Solver có thể trả tìm thấy **Có** nhưng kiểm tra báo **Không hợp lệ**. Trạng thái
quyết định lời giải có được chấp nhận. Tên lớp và thông tin gốc của ngoại lệ được
giữ làm dữ liệu kỹ thuật để chẩn đoán; thông báo do benchmark tạo dùng tiếng Việt.

Metadata giữ tên khóa JSON kỹ thuật (`status`, `started_at`, `completed_at`,
`python_version`, `python_executable`, `platform`, `machine`, `processor`,
`repeats`, `algorithm_order`, `stage_order`, `stages_dir`, `stages`, `charts`,
`raw_rows`, `summary_rows`, `chart_error` khi có). Trạng thái, tên nhóm và ba
mô tả `measurement_method`, `summary_method`, `solution_length_convention`
đều bằng tiếng Việt. `output_language="vi-VN"`, `schema_version=2` nhận diện
định dạng mới. Thời điểm UTC, phiên bản, đường dẫn, định danh và SHA-256 giữ nguyên.

Mọi cặp dự kiến đều có dòng kể cả thiếu màn. Lỗi tìm kiếm, lời giải sai, kết quả
không nhất quán hoặc lỗi biểu đồ làm lệnh trả mã khác 0 sau khi ghi chẩn đoán.
CSV được thay thế nguyên tử sau mỗi màn. Nếu ngắt giữa chừng, metadata ghi
**Đang chạy** và có thể còn CSV chưa đủ hoặc ảnh cũ; chỉ dùng bộ kết quả có
metadata **Thành công** và đủ số dòng. Biểu đồ PNG 200 dpi dùng Agg và DejaVu Sans,
hiển thị dữ liệu lỗi/thiếu bằng khoảng trống kèm danh sách bên dưới.
