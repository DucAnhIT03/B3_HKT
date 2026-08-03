# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** B3_HKT
**Thành viên thực hiện phần này:** Phan Văn Hiếu — 2A202601227
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**
> Dịch vụ và quy định của Thư viện RMIT Việt Nam dành cho sinh viên, giảng viên
> và toàn bộ cộng đồng RMIT. Corpus chính thức nằm tại `data/rmit-library`.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Resources for students with a disability | [RMIT](https://www.rmit.edu.vn/libraryvn/student-support/resources-for-students-with-a-disability) | 2026-08-03 / not-stated | 949 | student, library, accessibility, en |
| 2 | Borrowing and returning | [RMIT](https://www.rmit.edu.vn/libraryvn/borrowing-and-resources/borrowing-and-returning) | 2026-08-03 / not-stated | 3,553 | all, library, borrowing-policy, en |
| 3 | Develop course content | [RMIT](https://www.rmit.edu.vn/libraryvn/teacher-support/developing-course-content) | 2026-08-03 / not-stated | 975 | faculty, library, teacher-support, en |
| 4 | Library hours and locations | [RMIT](https://www.rmit.edu.vn/libraryvn/about-us/hours-and-locations) | 2026-08-03 / not-stated | 1,776 | all, library, opening-hours, en |
| 5 | Library resources and collections | [RMIT](https://www.rmit.edu.vn/libraryvn/borrowing-and-resources/library-resources) | 2026-08-03 / not-stated | 3,816 | all, library, library-resources, en |
| 6 | RMIT Vietnam Library rules | [RMIT](https://www.rmit.edu.vn/libraryvn/about-us) | 2026-08-03 / not-stated | 778 | all, library, library-rules, en |
| 7 | Study FAQs | [RMIT](https://www.rmit.edu.vn/libraryvn/student-support/study-faq) | 2026-08-03 / not-stated | 24,139 | student, library, student-support, en |
| 8 | Book a study room | [RMIT](https://www.rmit.edu.vn/libraryvn/student-support/book-a-study-room) | 2026-08-03 / not-stated | 1,354 | student, library, room-booking, en |
| 9 | Workshops and consultations for students | [RMIT](https://www.rmit.edu.vn/libraryvn/teacher-support/organise-workshops-and-consultations-for-your-students) | 2026-08-03 / not-stated | 1,135 | faculty, library, teacher-support, en |

> Số ký tự được tính trên phần nội dung sau YAML front matter, đúng với dữ liệu
> được `ingest.py` đưa vào chunker.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa 9 trang công khai của RMIT Việt Nam, không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version` và metadata phân loại.
- [x] `sources.csv` có đúng 9 dòng và khớp một-một với 9 tài liệu.
- [x] `audience` có nhiều giá trị (`student`, `faculty`, `all`) nên bộ lọc có tác dụng thực tế.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string, duy nhất | `rmit-study-room-booking` | Liên kết chunk với tài liệu gốc, hỗ trợ truy vết và xóa toàn bộ chunk của một tài liệu. |
| `title` | string | `Book a study room` | Giúp nhận diện nội dung và trình bày nguồn dễ đọc. |
| `source_url` | URL string | `https://www.rmit.edu.vn/...` | Cho phép kiểm chứng câu trả lời tại nguồn công khai. |
| `retrieved_at` | ISO date string | `2026-08-03` | Ghi nhận thời điểm thu thập để đánh giá độ mới của dữ liệu. |
| `document_version` | string | `not-stated` | Theo dõi phiên bản; dùng `not-stated` khi trang không công bố phiên bản. |
| `audience` | enum | `student`, `faculty`, `all` | Pre-filter đúng nhóm người dùng trước khi xếp hạng embedding. |
| `department` | string | `library` | Thu hẹp đơn vị cung cấp dịch vụ khi corpus được mở rộng. |
| `category` | string | `room-booking` | Phân biệt quy định mượn sách, giờ mở cửa, hỗ trợ học tập và dịch vụ giảng viên. |
| `language` | ISO language code | `en` | Hỗ trợ chọn tài liệu theo ngôn ngữ truy vấn hoặc câu trả lời. |

### Kết quả CHECKPOINT 2

Script kiểm tra chính thức ghi nhận: **9/9 file OK**, `sources.csv` **khớp**;
phân bố `audience` là `student: 3`, `all: 4`, `faculty: 2`.

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

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

| # | Câu hỏi (Query) | Metadata filter | Câu trả lời chuẩn (Gold Answer) | Chunk/tài liệu chứa thông tin |
|---|-------|-----------------|-------------------------------|--------------------------|
| 1 | Trong học kỳ, thư viện RMIT tại Sài Gòn và Hà Nội mở cửa vào thời gian nào? | Không | Cả hai cơ sở mở 8:00–21:00 từ thứ Hai đến thứ Sáu và 8:00–17:00 thứ Bảy, Chủ nhật. Riêng Sài Gòn trong tuần thi 10–12 mở 8:00–21:00 từ thứ Hai đến Chủ nhật. | `rmit-library-hours`, mục “During semester” |
| 2 | Sinh viên đại học và sau đại học được mượn bao nhiêu tài liệu, trong bao lâu và gia hạn thế nào? | Không | Được mượn 25 tài liệu trong 30 ngày và gia hạn một lần nếu tài liệu chưa quá hạn hoặc chưa bị người khác đặt trước. Thời gian gia hạn là 15 ngày, tổng thời gian tối đa 45 ngày. | `rmit-borrowing-returning`, mục “Undergraduate and postgraduate students” |
| 3 | Sinh viên có thể đặt phòng học trước bao lâu và bị giới hạn thời lượng, số lượt thế nào? | `{"audience": "student"}` | Có thể đặt trước tối đa 2 tuần; mỗi lượt tối đa 1 giờ và mỗi người tối đa 2 lượt đặt. Một đại diện nhóm phải check-in với thủ thư bằng thẻ RMIT; nếu không check-in trong vòng 15 phút trước lịch, lượt đặt bị hủy. | `rmit-study-room-booking`, mục “Booking policy” |
| 4 | Thư viện hỗ trợ sinh viên khuyết tật bằng những tài nguyên và khả năng tiếp cận nào? | `{"audience": "student"}` | Thư viện hỗ trợ số hóa văn bản, tìm tài nguyên số, chuyển PDF thành text và phối hợp với ELA để cung cấp tài nguyên ở định dạng phù hợp. Lối đi xe lăn có tại các địa điểm Sài Gòn, Hà Nội và Đà Nẵng. | `rmit-accessibility-resources`, phần mở đầu, “Wheelchair access” và “Equitable Learning and Accessibility” |
| 5 | Thư viện hỗ trợ giảng viên phát triển nội dung môn học như thế nào? | `{"audience": "faculty"}` | Thư viện cung cấp eReserve qua Liaison Librarian, hỗ trợ tích hợp reading list và theo dõi hoạt động sinh viên, hướng dẫn liên kết/nhúng tài nguyên vào Canvas bảo đảm bản quyền, đồng thời nhận đề xuất mua sách in hoặc e-book. | `rmit-course-content-support`, các mục “eReserve”, “Reading list assistance”, “Add library resources to Canvas”, “Purchasing books” |

Các gold answer trên chỉ tổng hợp dữ kiện có trong corpus. Bộ câu hỏi được cố định
trước khi chạy benchmark; câu 3 bắt buộc dùng `metadata_filter={"audience": "student"}`
để chứng minh tác dụng của metadata theo biến thể K3.

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
