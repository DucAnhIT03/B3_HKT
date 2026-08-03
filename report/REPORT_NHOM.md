# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**
> *1 câu — ví dụ: thư viện + đăng ký môn học.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `rmit-borrowing-returning` | FixedSizeChunker (`fixed_size`, 400) | 9 | 394.78 | Thấp — có thể cắt giữa bảng quota, danh sách hoặc một mục quy định. |
| `rmit-borrowing-returning` | SentenceChunker (`by_sentences`, 3 câu) | 8 | 441.38 | Trung bình — giữ câu trọn vẹn nhưng các dòng bullet ít dấu kết câu có thể bị gộp thành chunk dài. |
| `rmit-borrowing-returning` | RecursiveChunker (`recursive`, 400) | 10 | 353.50 | Khá — ưu tiên ranh giới đoạn và dòng nên giữ các nhóm quy định tốt hơn fixed-size. |
| `rmit-study-faq` | FixedSizeChunker (`fixed_size`, 400) | 61 | 395.72 | Thấp — cắt theo ký tự nên dễ tách câu hỏi khỏi phần trả lời tương ứng. |
| `rmit-study-faq` | SentenceChunker (`by_sentences`, 3 câu) | 90 | 265.11 | Trung bình — câu được giữ nguyên nhưng heading có thể bị tách khỏi câu trả lời. |
| `rmit-study-faq` | RecursiveChunker (`recursive`, 400) | 73 | 328.70 | Khá — giữ cấu trúc đoạn tốt hơn, nhưng chunk con vẫn có thể mất heading của mục FAQ. |
| `rmit-study-room-booking` | FixedSizeChunker (`fixed_size`, 400) | 4 | 338.50 | Trung bình — số chunk ít nhưng có nguy cơ cắt giữa các bước đặt phòng hoặc booking policy. |
| `rmit-study-room-booking` | SentenceChunker (`by_sentences`, 3 câu) | 2 | 675.00 | Thấp — chunk quá lớn vì nội dung dạng bullet không được nhận diện tốt như câu hoàn chỉnh. |
| `rmit-study-room-booking` | RecursiveChunker (`recursive`, 400) | 4 | 337.00 | Khá — giữ các đoạn và dòng chính sách gần nhau, phù hợp hơn hai baseline còn lại. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

> **Bộ query đã chốt:** mọi thành viên phải giữ nguyên câu chữ, gold answer, corpus và embedder khi chạy benchmark. Query số 4 bắt buộc dùng `metadata_filter={"audience": "student"}`.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 — Số liệu | How many items can undergraduate and postgraduate students borrow, for how long, and how many renewals are allowed? | Undergraduate and postgraduate students can borrow **25 items** for **30 days**, with **1 renewal**. | `rmit-borrowing-returning` → `Borrowing for students, staff and alumni` → `Student` → `Undergraduate and postgraduate students` |
| 2 — Điều kiện | Under what conditions can a borrowed item be renewed, and how long does the renewal last? | An item can be renewed only when it is **not overdue** and **has not been reserved by another user**. A renewal lasts **15 days**, with a maximum loan period of **45 days**. | `rmit-borrowing-returning` → `Borrowing for students, staff and alumni` → phần điều kiện gia hạn |
| 3 — Quy trình | What steps are required to book a Library study room? | Log in with an **RMIT account**, choose the **campus**, select a **room and time**, then **confirm the booking**. | `rmit-study-room-booking` → `How to book a room` |
| 4 — Liệt kê + lọc metadata | What support does the Library provide to make resources accessible? **Filter:** `{"audience": "student"}` | The Library provides **text digitisation**, **help obtaining digital resources**, and **conversion of PDF documents to text**. | `rmit-accessibility-resources` → `Resources for students with a disability` |
| 5 — Ngoại lệ | Which reasons will the Library not accept when a user disputes a fine? | The Library does not accept: lack of knowledge of library policies; unwillingness to take responsibility for material loaned to a third party; forgetting the due date; not receiving reminders; a full email inbox; inability to visit often or distance from the library; disagreement with the fine policy; not being on campus; semester breaks or summer vacation; or changed opening hours. | `rmit-borrowing-returning` → `Disputes` → `We will not accept the following reasons` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
