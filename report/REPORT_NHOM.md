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
> Dịch vụ thư viện công khai của Harvard Library: mượn và gia hạn, hỗ trợ sinh viên năm nhất, sách số Libby, BorrowDirect và hỗ trợ giảng dạy.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Borrow renew and return library materials | [Nguồn](https://library.harvard.edu/how-to/borrow-renew-and-return-library-materials) | 2026-08-03 / not-stated | 1.609 | `audience=all`, `category=borrowing-policy` |
| 2 | Librarians for First-Year Students | [Nguồn](https://library.harvard.edu/services-tools/librarians-first-year-students) | 2026-08-03 / not-stated | 876 | `audience=student`, `category=research-support` |
| 3 | Libby for Harvard | [Nguồn](https://library.harvard.edu/services-tools/libby-harvard) | 2026-08-03 / not-stated | 1.071 | `audience=all`, `category=digital-borrowing` |
| 4 | Teach with the Library | [Nguồn](https://library.harvard.edu/services-tools/teach-library) | 2026-08-03 / not-stated | 1.503 | `audience=faculty`, `category=teaching-support` |
| 5 | BorrowDirect | [Nguồn](https://library.harvard.edu/services-tools/borrowdirect) | 2026-08-03 / not-stated | 1.327 | `audience=all`, `category=resource-sharing` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) được crawler lấy từ 5 trang công khai của Harvard Library sau khi kiểm tra `robots.txt`, chờ 1 giây giữa request; menu/footer đã được loại bỏ và corpus không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated`) trong metadata; `sources.csv` khớp một-một với 5 file.

**Quy trình và quyền sử dụng:**

- Danh sách đầu vào được cố định trong `data/urls.csv`; crawler chạy bằng lệnh `python scripts/fetch_public_pages.py data/urls.csv --output-dir data/k3_harvard_raw --delay 1 --timeout 30` và trả về `5 saved, 0 skipped`.
- Crawler đã đọc `https://library.harvard.edu/robots.txt`; cả 5 URL đều được phép cho user-agent của lab. Không đăng nhập, không dùng CAPTCHA, không gọi API riêng và không crawl liên kết ngoài danh sách.
- Nhóm đã đọc [Privacy, Terms of Use & Copyright Information](https://library.harvard.edu/about/policies/privacy-terms-use-copyright-information) và [Harvard Library CC BY Copyright Policy](https://library.harvard.edu/about/policies/harvard-library-cc-copyright-policy). Corpus chỉ giữ bản tóm lược phục vụ giáo dục, ghi nguồn trực tiếp, không sao chép ảnh, logo, dữ liệu được cấp phép hay bộ sưu tập số.
- Đầu ra thô được rà soát và loại menu, footer, lời mời đăng ký, thông tin liên hệ và các mục không cần cho benchmark trước khi đưa vào `data/k3_university/`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `librarians-first-year-students` | Định danh duy nhất tài liệu và truy vết chunk về nguồn. |
| `title` | string | `Renewing library items` | Hiển thị nguồn phù hợp và hỗ trợ đối chiếu kết quả. |
| `source_url` | URL string | `https://library.unimelb.edu.au/...` | Kiểm chứng câu trả lời trên trang chính thức. |
| `retrieved_at` | date (`YYYY-MM-DD`) | `2026-08-03` | Cho biết thời điểm chụp nội dung nguồn. |
| `document_version` | string | `not-stated` | Ghi phiên bản công bố; dùng `not-stated` khi trang không nêu. |
| `audience` | enum string | `student`, `faculty`, `all` | Lọc tài liệu theo đúng nhóm người dùng; corpus có ba giá trị và tài liệu dùng chung được gán `all`, không gán sai thành một vai riêng. |
| `department` | string | `library` | Giới hạn truy xuất theo đơn vị cung cấp dịch vụ. |
| `category` | enum string | `borrowing-policy`, `teaching-support` | Phân biệt các nghiệp vụ thư viện có từ vựng gần nhau. |
| `language` | ISO language code | `en` | Cho phép chọn ngôn ngữ corpus khi mở rộng dữ liệu. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

Thông số chung: `chunk_size=500`; comparator dùng FixedSize overlap 50, Sentence tối đa 3 câu/chunk và Recursive với thứ tự separator mặc định.

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `borrow-renew-return` | FixedSizeChunker (`fixed_size`) | 3 | 468,33 | Có overlap nhưng có thể cắt giữa câu/mục. |
| `borrow-renew-return` | SentenceChunker (`by_sentences`) | 5 | 259,60 | Giữ nguyên ranh giới câu; có thể ghép câu từ hai mục. |
| `borrow-renew-return` | RecursiveChunker (`recursive`) | 4 | 324,75 | Ưu tiên ranh giới mục, đoạn và câu. |
| `librarians-first-year-students` | FixedSizeChunker (`fixed_size`) | 2 | 308,50 | Có overlap nhưng điểm cắt không theo ngữ nghĩa. |
| `librarians-first-year-students` | SentenceChunker (`by_sentences`) | 2 | 282,00 | Các câu hỗ trợ được giữ trọn vẹn. |
| `librarians-first-year-students` | RecursiveChunker (`recursive`) | 2 | 282,50 | Giữ phần giới thiệu và mục hỗ trợ theo ranh giới tự nhiên. |
| `teach-with-library` | FixedSizeChunker (`fixed_size`) | 3 | 445,00 | Có overlap nhưng có thể cắt danh sách/chủ đề. |
| `teach-with-library` | SentenceChunker (`by_sentences`) | 4 | 307,00 | Không cắt giữa câu, nhóm tối đa ba câu. |
| `teach-with-library` | RecursiveChunker (`recursive`) | 4 | 307,25 | Giữ tốt cấu trúc các mục hướng dẫn và đoạn văn. |

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

| # | Câu hỏi (Query) | Metadata filter | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-----------------|-------------------------------|--------------------------|
| 1 | Sinh viên năm nhất nhận được những hình thức hỗ trợ nào từ First-Year Librarians? | `{"audience": "student"}` | First-Year Librarians là đầu mối thư viện cá nhân, cung cấp hướng dẫn, tư vấn và giới thiệu đến dịch vụ phù hợp khi sinh viên tìm hướng nghiên cứu hoặc viết bài nghiên cứu cho môn học. | `librarians-first-year-students` — mục “Support available”. |
| 2 | Người dùng được mượn tối đa bao nhiêu sách trên Libby cùng lúc, giữ trong bao lâu và đặt trước bao nhiêu sách? | Không | Tối đa 3 sách cùng lúc; mỗi lượt mượn kéo dài 14 ngày; được đặt trước tối đa 5 sách. | `libby-harvard` — mục “Borrowing limits”. |
| 3 | Tài liệu mượn thông thường được tự động gia hạn tối đa bao nhiêu lần, với điều kiện gì? | Không | Tự động gia hạn tối đa 5 lần nếu không có người dùng khác yêu cầu tài liệu đó. | `borrow-renew-return` — mục “Loan periods, renewals and returns”. |
| 4 | Giảng viên phải làm gì để đặt một buổi hướng dẫn thư viện cho lớp và nên gửi yêu cầu khi nào? | `{"audience": "faculty"}` | Liên hệ library liaison hoặc gửi request; nên gửi càng sớm càng tốt để bảo đảm có nhân sự và không gian. | `teach-with-library` — các mục “General library instruction” và “Special collections and archives”. |
| 5 | BorrowDirect cho mượn loại tài liệu nào, trong bao lâu và có được gia hạn không? | Không | Cho mượn sách in và bản nhạc mà thư viện sở hữu đồng ý cho mượn; thời hạn 16 tuần và không được gia hạn. | `borrowdirect` — các mục “Delivery and loan rules” và “Eligible material”. |

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
