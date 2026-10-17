# Mô hình Hóa Bài Toán Bloxorz Solver (Problem Formulation)
> **Môn học:** Cơ sở Trí tuệ Nhân tạo — HCMUS  
> **Thành viên chịu trách nhiệm:** TV1 (Leader) — System Architect  
> **Mục đích:** Cung cấp mô hình toán học chuẩn xác 100% để đưa vào Mục 2 của Báo cáo PDF (chiếm 10/30 điểm).

---

## 1. ĐẶT VẤN ĐỀ (PROBLEM STATEMENT)

Trò chơi **Bloxorz** là bài toán tìm kiếm đường đi trong không gian trạng thái tiền định (deterministic), quan sát toàn phần (fully observable) và rời rạc (discrete).

Một bài toán tìm kiếm hình thức (Formal Search Problem) được định nghĩa bởi bộ 5 thành phần:
$$\mathcal{P} = \langle S, s_0, A, T, G, c \rangle$$

Trong đó:
- $S$: Không gian trạng thái (State Space).
- $s_0 \in S$: Trạng thái bắt đầu (Initial State).
- $A$: Không gian hành động (Action Space).
- $T: S \times A \rightarrow S \cup \{\emptyset\}$: Mô hình chuyển trạng thái (Transition Model).
- $G \subseteq S$: Tập trạng thái đích (Goal Test).
- $c: S \times A \times S \rightarrow \mathbb{R}^+$: Hàm chi phí bước đi (Step Cost Function).

---

## 2. KHÔNG GIAN TRẠNG THÁI (STATE SPACE $S$)

### 2.1 Biểu diễn Trạng thái (State Representation)
Khối sắt $1 \times 1 \times 2$ có thể đứng thẳng, nằm ngang, nằm dọc hoặc bị tách thành hai khối lập phương $1 \times 1 \times 1$.

Một trạng thái $s \in S$ được biểu diễn bằng một bộ (tuple) bất biến:
$$s = \langle (r_1, c_1), (r_2, c_2), a_{cube}, B \rangle$$

Trong đó:
1. **Tọa độ chuẩn hóa (Canonical Coordinates):** $(r_1, c_1)$ và $(r_2, c_2)$ là tọa độ các ô khối chiếm giữ trên lưới, luôn được sắp xếp theo thứ tự hàng - cột (Row-Major Order):
   $$(r_1 < r_2) \lor (r_1 = r_2 \land c_1 \le c_2)$$
2. **Tư thế khối (Orientation):**
   - **Đứng thẳng (Standing):** $r_1 = r_2 \land c_1 = c_2$ (chiếm đúng 1 ô $(r_1, c_1)$).
   - **Nằm ngang (Lying Row):** $r_1 = r_2 \land c_1 + 1 = c_2$ (chiếm 2 ô liên tiếp trên cùng 1 hàng).
   - **Nằm dọc (Lying Col):** $r_1 + 1 = r_2 \land c_1 = c_2$ (chiếm 2 ô liên tiếp trên cùng 1 cột).
3. **Trạng thái phân tách (Split State):**
   - $a_{cube} = -1$: Khối nguyên $1 \times 1 \times 2$.
   - $a_{cube} \in \{0, 1\}$: Khối bị tách thành 2 khối lập phương $1 \times 1 \times 1$; $a_{cube} = 0$ nghĩa là đang điều khiển khối tại $(r_1, c_1)$, $a_{cube} = 1$ nghĩa là đang điều khiển khối tại $(r_2, c_2)$.
4. **Trạng thái cầu (Bridges Configuration):**
   $$B = (b_0, b_1, \dots, b_{k-1}) \in \{0, 1\}^k$$
   Với $b_i = 1$ là cầu thứ $i$ đang mở (đi được), $b_i = 0$ là cầu đóng (vực thẳm).

### 2.2 Đánh giá Kích thước Không gian Trạng thái ($|S|$)
Với bản đồ có kích thước $R \times C$ và $k$ hệ thống cầu:
- Số trạng thái khi khối nguyên: $3 \times R \times C \times 2^k$.
- Số trạng thái khi khối bị split: $\binom{R \times C}{2} \times 2 \times 2^k \approx R^2 C^2 \times 2^k$.
$$\Rightarrow |S| \le O(R \cdot C \cdot 2^k + R^2 C^2 \cdot 2^k)$$
Trong thực tế, số ô hợp lệ trên map rất hạn chế nên không gian trạng thái thực tế chỉ dao động từ $10^2$ đến $10^4$ states, hoàn toàn phù hợp để giải bằng BFS, UCS và A*.

---

## 3. KHÔNG GIAN HÀNH ĐỘNG (ACTION SPACE $A$)

$$A = \{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}, \text{SWITCH\_BLOCK}\}$$

- Khi khối nguyên ($a_{cube} = -1$): Chỉ có 4 hành động di chuyển $\{\text{UP}, \text{DOWN}, \text{LEFT}, \text{RIGHT}\}$.
- Khi khối bị split ($a_{cube} \in \{0, 1\}$): Bổ sung thêm hành động $\text{SWITCH\_BLOCK}$ để đổi quyền điều khiển khối lập phương ($a_{cube} \leftarrow 1 - a_{cube}$).

---

## 4. MÔ HÌNH CHUYỂN TRẠNG THÁI (TRANSITION MODEL $T(s, a)$)

### 4.1 Bảng chuyển hướng khi lăn khối nguyên:
| Tư thế hiện tại | Hành động | Tư thế tiếp theo | Tọa độ mới |
|---|:---:|:---:|---|
| **Standing** $(r, c)$ | UP | Lying Col | $(r-2, c)$ và $(r-1, c)$ |
| Standing $(r, c)$ | DOWN | Lying Col | $(r+1, c)$ và $(r+2, c)$ |
| Standing $(r, c)$ | LEFT | Lying Row | $(r, c-2)$ và $(r, c-1)$ |
| Standing $(r, c)$ | RIGHT | Lying Row | $(r, c+1)$ và $(r, c+2)$ |
| **Lying Row** $(r, c), (r, c+1)$ | UP | Lying Row | $(r-1, c)$ và $(r-1, c+1)$ |
| Lying Row $(r, c), (r, c+1)$ | DOWN | Lying Row | $(r+1, c)$ và $(r+1, c+1)$ |
| Lying Row $(r, c), (r, c+1)$ | LEFT | Standing | $(r, c-1)$ |
| Lying Row $(r, c), (r, c+1)$ | RIGHT | Standing | $(r, c+2)$ |
| **Lying Col** $(r, c), (r+1, c)$ | UP | Standing | $(r-1, c)$ |
| Lying Col $(r, c), (r+1, c)$ | DOWN | Standing | $(r+2, c)$ |
| Lying Col $(r, c), (r+1, c)$ | LEFT | Lying Col | $(r, c-1)$ và $(r+1, c-1)$ |
| Lying Col $(r, c), (r+1, c)$ | RIGHT | Lying Col | $(r, c+1)$ và $(r+1, c+1)$ |

### 4.2 Điều kiện Hợp lệ (Move Validation):
Nước đi $T(s, a) = \emptyset$ (thua cuộc / không hợp lệ) nếu:
1. Bất kỳ phần nào của khối nằm ngoài biên lưới ($r < 0 \lor r \ge R \lor c < 0 \lor c \ge C$).
2. Bất kỳ phần nào của khối rơi vào ô Void (`' '`).
3. Khối đè lên ô cầu đang đóng ($b_i = 0$).
4. Khối ở tư thế **Standing đè lên ô dễ vỡ (Fragile tile `'-'`)**.

### 4.3 Kích hoạt Công tắc & Cầu:
- **Soft Switch (`'O'`):** Kích hoạt khi có bất kỳ phần nào của khối lăn đè lên (kể cả đứng hay nằm).
- **Heavy Switch (`'X'`):** Chỉ kích hoạt khi khối **Standing** đè lên. Khối nằm đè qua hoặc khối nhỏ 1x1 không kích hoạt được.
- **Tác động lên cầu:**
  - `swap`: $b_i \leftarrow 1 - b_i$
  - `on`: $b_i \leftarrow 1$
  - `off`: $b_i \leftarrow 0$

### 4.4 Phân tách & Ghép khối (Split & Merge):
- Khi khối đứng thẳng đè lên ô Split (`'T'`), khối được dịch chuyển tức thời tới hai vị trí $(r_1', c_1')$ và $(r_2', c_2')$ định trước và chuyển thành $a_{cube} = 0$.
- **Cơ chế ghép lại (Auto-Merge):** Sau mỗi bước đi của khối nhỏ, nếu khoảng cách Manhattan giữa 2 khối nhỏ bằng 1:
  $$|r_1 - r_2| + |c_1 - c_2| = 1$$
  $\rightarrow$ Hai khối lập phương tự động sáp nhập lại thành khối $1 \times 1 \times 2$ ($a_{cube} \leftarrow -1$).

---

## 5. KIỂM TRA MỤC TIÊU (GOAL TEST $G(s)$)

$$G(s) = \text{True} \iff \text{is\_standing}(s) \land (r_1, c_1) = (r_{goal}, c_{goal})$$

Khối sắt bắt buộc phải **đứng thẳng** trên ô đích `'H'`. Mọi trường hợp khối nằm ngang/dọc đè lên ô đích đều không được công nhận là chiến thắng.

---

## 6. HÀM CHI PHÍ (COST FUNCTION $c(s, a, s')$)

- **Với BFS / Uniform Search:**
  $$c(s, a, s') = 1 \quad \forall s, a$$
- **Với UCS (Non-Uniform Cost Function — Đề xuất có biện luận):**
  $$c(s, a, s') = \begin{cases}
  1 & \text{khi kích hoạt công tắc mở đường (khuyến khích tiến trình)} \\
  2 & \text{bước lăn thông thường trên sàn} \\
  3 & \text{thao tác điều khiển trong trạng thái split} \\
  4 & \text{lăn qua ô dễ vỡ fragile (rủi ro cao, gạch có nguy cơ nứt)}
  \end{cases}$$
  *Biện luận:* Giúp UCS ưu tiên tìm đường đi an toàn nhất, ít rủi ro sập gạch nhất thay vì chỉ đếm số bước thuần túy.

---

## 7. HÀM HEURISTIC CHO A* SEARCH ($h(s)$)

### 7.1 Heuristic 1: Manhattan Distance chia đôi ($h_1$)
$$h_1(s) = \frac{|\bar{r} - r_{goal}| + |\bar{c} - c_{goal}|}{2}$$
- **Chứng minh Admissible:** Vì một lần lật khối di chuyển khối đi tối đa 2 ô trên lưới, nên số bước đi tối thiểu cần thiết luôn $\ge \frac{\text{Khoảng cách}}{2}$. Do đó $h_1(s) \le h^*(s)$ với mọi $s$.
- **Chứng minh Consistent:** Khi di chuyển một bước từ $s \rightarrow s'$, khoảng cách Manhattan thay đổi tối đa 2 đơn vị $\Rightarrow h_1(s) - h_1(s') \le \frac{2}{2} = 1 \le c(s, a, s')$.

### 7.2 Heuristic 2: Manhattan chia đôi kèm Phạt tư thế ($h_2$)
$$h_2(s) = h_1(s) + \begin{cases} 0 & \text{nếu } s \text{ is Standing} \\ 1 & \text{nếu } s \text{ is Lying / Split} \end{cases}$$
- **Lập luận:** Để vào được lỗ đích, khối bắt buộc phải đứng thẳng. Nếu khối đang nằm, tối thiểu cần thêm 1 bước lật để dựng đứng khối $\Rightarrow h_2(s)$ vẫn là cận dưới hợp lệ (Admissible) và chặt hơn $h_1(s)$.
