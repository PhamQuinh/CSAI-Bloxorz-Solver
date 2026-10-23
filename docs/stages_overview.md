# Tổng quan và quy ước 10 map Bloxorz

Tài liệu này là tài liệu thống nhất của nhóm về dữ liệu map, cơ chế đặc biệt
và cách hiển thị trong GUI. Tọa độ sử dụng chỉ số 0-based `(row, column)`,
bắt đầu từ góc trên bên trái.

## 1. Quy ước ký hiệu

| Ký hiệu | Ý nghĩa |
|---|---|
| ` ` | Void, không có ô |
| `.` | Ô sàn bình thường |
| `S` | Vị trí bắt đầu |
| `H` | Đích |
| `-` | Ô fragile |
| `B` | Bridge mở ban đầu |
| `b` | Bridge đóng ban đầu |
| `O` | Soft switch |
| `X` | Heavy switch |
| `T` | Split/teleport switch |

Action của switch:

- `on`: mở bridge;
- `off`: đóng bridge;
- `swap`: đảo trạng thái bridge.

## 2. Danh sách map

| Level | File | Kích thước | Cơ chế | Passcode | Ground truth |
|---:|---|---:|---|---|---:|
| 1 | `level_01_basic.json` | 6 x 10 | Basic | `780464` | 7 |
| 2 | `level_02_basic.json` | 6 x 15 | 2 bridge, 2 switch | `290299` | 17 |
| 3 | `level_03_basic.json` | 6 x 15 | Narrow path | `918660` | 19 |
| 4 | `level_04_fragile.json` | 9 x 14 | Fragile tiles | `520967` | 28 |
| 5 | `level_05_fragile.json` | 10 x 15 | Fragile, 3 bridge, 4 switch | `028431` | 33 |
| 6 | `level_06_switch_bridge.json` | 10 x 15 | Maze layout | `524383` | 35 |
| 7 | `level_07_switch_bridge.json` | 8 x 15 | 1 bridge, 1 switch | `189493` | 44 |
| 8 | `level_08_split_basic.json` | 9 x 15 | Split, teleport | `499707` | 10 rolls |
| 9 | `level_09_combined.json` | 5 x 15 | Split, teleport | `074355` | 24 rolls |
| 10 | `level_10_split_complex.json` | 10 x 14 | Split, teleport, 3 bridge, 2 switch | `300590` | 57 rolls |

Ground truth nằm trong `stages/ground_truth_solutions.txt`. Dấu gạch dưới `_`
trong nghiệm là thao tác đổi cube đang active bằng Spacebar.

## 3. Map có bridge và switch

### Level 2 — Bridges and Switches

- Bridge 0: `(4,4), (4,5)`, đóng ban đầu.
- Bridge 1: `(4,10), (4,11)`, đóng ban đầu.
- Switch `(2,2)`: `swap` bridge 0.
- Switch `(1,8)`: `swap` bridge 1.
- Nghiệm chuẩn: `URDRRRRUUDRDRRURU` — 17 lượt lăn.

### Level 5 — Fragile and Multiple Switches

- Bridge 0: `(1,5), (1,6)`, mở ban đầu (`BB`).
- Bridge 1: `(5,8), (5,9)`, mở ban đầu (`BB`).
- Bridge 2: `(8,5), (8,6)`, mở ban đầu (`BB`).
- Switch `(1,8)`: `swap` bridge 0.
- Switch `(3,3)`: `on` bridge 2.
- Switch `(5,6)`: `off` bridge 2.
- Switch `(6,14)`: `swap` bridge 2.
- Nghiệm chuẩn: `LLLRLLLLLDRDDRRRRDRRRRLLLLDLLLLLL` — 33 lượt lăn.

**Quyết định của nhóm:** giữ nguyên map, không đổi bridge 2 từ `BB` thành `bb`.
Switch `(3,3)` là switch cứu hộ để mở lại bridge 2 nếu bridge đã bị đóng.
Action `on` có tính lũy đẳng, nên kích hoạt khi bridge đang mở sẽ không tạo
thay đổi hình ảnh. Đây là hành vi đúng, không phải lỗi map.

Theo nghiệm chuẩn:

| Bước | Switch | Thay đổi |
|---:|---|---|
| 3 | `(1,8)` | Bridge 0 mở -> đóng |
| 5 | `(1,8)` | Bridge 0 đóng -> mở |
| 14 | `(5,6)` | Bridge 2 mở -> đóng |
| 22 | `(6,14)` | Bridge 2 đóng -> mở |

### Level 7 — Single Tile Bridge

- Bridge 0: `(6,3)`, đóng ban đầu.
- Switch `(4,9)`: `swap` bridge 0.
- Nghiệm chuẩn: `DLURRRRRDRLULLLLLDRDRDRRRUURDLURUURRRDRDRDLU` — 44 lượt lăn.

### Level 10 — Advanced Split and Multi-Bridge

- Bridge 0: `(1,3), (1,4)`, đóng ban đầu.
- Bridge 1: `(1,6), (1,7)`, đóng ban đầu.
- Bridge 2: `(2,12), (3,12)`, đóng ban đầu.
- Switch `(9,5)`: `on` bridge 0.
- Switch `(9,11)`: `swap` bridge 1 và bridge 2.
- Nghiệm chuẩn: 57 lượt lăn.

Switch `(9,5)` dùng `on` là đúng vì bridge 0 đang đóng.

## 4. Map split và teleport

### Level 8 — Split Block Intro

- Split/teleport switch: `(4,4)`.
- Cube 0 đến `(1,10)`.
- Cube 1 đến `(7,10)`.
- Cube active ban đầu: cube 0.
- Ground truth: `RRDDDD_UURR`.

### Level 9 — Long Bridge Split

- Split/teleport switch: `(1,13)`.
- Cube 0 đến `(1,2)`.
- Cube 1 đến `(1,12)`.
- Cube active ban đầu: cube 1.
- Ground truth: `RDRRRRRRUR_D_D_RRRRRU_LLLLLD`.

## 5. Quy ước đếm bước và replay GUI

Ground truth của game gốc chỉ đếm các lượt lăn theo hướng:

```text
UP, DOWN, LEFT, RIGHT
```

`SWITCH_BLOCK` chỉ đổi cube đang active, không phải một lượt lăn. Vì vậy:

| Level | Ground truth | Solver actions |
|---:|---:|---:|
| 8 | 10 rolls | 11 actions = 10 rolls + 1 `SWITCH_BLOCK` |
| 9 | 24 rolls | 25 actions = 24 rolls + 1 `SWITCH_BLOCK` |
| 10 | 57 rolls | 58 actions = 57 rolls + 1 `SWITCH_BLOCK` |

Khi replay:

```python
for action in result.actions:
    if action in (UP, DOWN, LEFT, RIGHT):
        play_roll_animation(action)
        roll_count += 1
    elif action == SWITCH_BLOCK:
        switch_active_cube()
        play_switch_cube_effect()
```

GUI phải dùng trạng thái bridge từ backend. Khi nhận `on` cho bridge đang mở,
giữ nguyên bridge; không tự đóng hoặc ẩn bridge để tạo hiệu ứng giả.

## 6. Các map còn lại

- Level 1: map basic, không có cơ chế đặc biệt.
- Level 3: map narrow path, không có bridge hoặc switch.
- Level 4: map fragile tiles.
- Level 6: map maze layout, không có bridge hoặc switch trong dữ liệu hiện tại.

## 7. Kiểm tra sau khi thay đổi map hoặc GUI

Từ thư mục gốc project:

```powershell
python -m unittest discover -s tests -t . -v
python -m compileall -q src tests
```

Không sửa JSON chỉ để làm khớp số action của solver với số lượt lăn trong
ground truth. Cần giữ nhất quán giữa map, engine, solver, ground truth và GUI.
