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

A* dùng $h_1$. $g$ là tổng `step_cost` trong `costs.py`: mỗi bước tốn ít nhất $c_{\min} = 1$ (bước rẻ nhất), bước lăn thường tốn 2, ô fragile tốn 4. $h_1(s)$ không vượt chi phí còn lại tối ưu của chính hàm này.

Ký hiệu $\mathrm{roll}(s, p) = c_{\min} \cdot \max(d(s, p) / 2,\ m(s))$:
- $d(s, p)$ là khoảng cách Manhattan từ tâm khối tới ô $p$.
- $m(s) = 0$ nếu khối còn nguyên; nếu đang tách và hai khối con cách nhau $k$ ô thì $m(s) = \max(0, k - 1)$.

Một nước không đứng lên ô tách chỉ kéo tâm tối đa 1.5 ô, nên chia 2 là cận dưới số nước. Muốn đứng vào lỗ hoặc đứng lên ô tách thì khối phải nguyên, nên cần ít nhất $m(s)$ nước. Hai việc đó dùng chung các nước đã đi, nên lấy $\max$, không cộng. Nhân $c_{\min}$ ra cận dưới chi phí của đoạn đường không teleport.

### 7.1 Heuristic 1 ($h_1$) — có tính teleport

Với mỗi ô tách $j$, gọi $L_j$ là vị trí hai khối con ngay sau khi đứng lên $j$ (đã ghép lại nếu hai ô đích kề nhau). $H(L_j)$ là cận dưới chi phí từ $L_j$ tới lỗ, tính bằng đường đi ngắn nhất trên đồ thị cổng:
- cạnh $L_j \to$ lỗ nặng $\mathrm{roll}(L_j, \text{lỗ})$;
- cạnh $L_j \to L_k$ nặng $\mathrm{roll}(L_j, \text{ô } k)$. Trọng số này đã gồm nước đứng lên ô $k$, và nước đó kết thúc tại $L_k$.

$$h_1(s) = \min\Big(\mathrm{roll}(s, \text{lỗ}),\ \min_j \mathrm{roll}(s, \text{ô } j) + H(L_j)\Big)$$

**Vì sao $h_1(s)$ không lớn hơn chi phí còn lại tối ưu.** Lấy một đường tối ưu và cắt tại các lần đứng lên ô tách.

- Đường không dùng ô tách: mọi nước kéo tâm tối đa 1.5 ô, và khối tách phải ghép trước khi đứng vào lỗ. Chi phí $\ge \mathrm{roll}(s, \text{lỗ})$.
- Đường có teleport, cổng đầu tiên là $j$: đoạn trước $L_j$ không teleport nên tốn ít nhất $\mathrm{roll}(s, \text{ô } j)$. Phần sau xuất phát từ $L_j$. Quy nạp theo số lần teleport còn lại, phần đó tốn ít nhất $H(L_j)$. Mỗi cạnh teleport nặng ít nhất $c_{\min} > 0$ nên đường tối ưu không lặp vô hạn.

$h_1$ lấy min của các trường hợp này nên không vượt chi phí của trường hợp nào. Tường và cầu chỉ làm đường dài thêm, nên bỏ chúng khỏi cận dưới vẫn an toàn.

Một nước teleport có thể làm $h_1$ giảm nhiều hơn chi phí của chính nước đó, nên $h_1$ không được xem là consistent trên map có ô tách. A* vẫn lấy được nghiệm tối ưu vì khi tìm thấy $g$ nhỏ hơn thì node được mở lại; lần đầu pop trạng thái lỗ, $g$ là tối ưu.

### 7.2 Heuristic 2 ($h_2$) — không dùng cho A*

$$h_2(s) = h_1(s) + \begin{cases} 0 & \text{nếu khối đang đứng nguyên} \\ c_{\min} & \text{nếu khối đang nằm hoặc đang tách} \end{cases}$$

Nước dựng khối đứng lên lỗ đã nằm một phần trong $h_1$. Nếu cộng thêm $c_{\min}$ trên một cạnh chỉ tốn $c_{\min}$, $h_2$ có thể lớn hơn chi phí còn lại. A* dùng $h_1$.

### 7.3 Map hai teleport dùng để kiểm tra

Một hàng 28 ô, cột đánh số từ 0:

```text
...T..S..T..............H...
```

- `S` ở cột 6, `H` ở cột 24.
- `T` cột 3 thả hai khối con vào cột 20 và 23.
- `T` cột 9 thả hai khối con vào cột 18 và 20.

Đường rẻ: LEFT, LEFT, RIGHT, RIGHT, RIGHT, tổng chi phí 9. Đường kia: sáu lần RIGHT, tổng chi phí 11. Heuristic chỉ lấy $d/2$ trả chi phí 11, vì sau nước LEFT đầu tâm còn cách lỗ 19.5 nên ước lượng 9.75 trong khi chi phí còn lại chỉ là 7. $h_1$ hiện tại và A* với $h = 0$ đều cho chi phí 9.
