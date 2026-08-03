# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** B3_HKT

**Danh sách thành viên:**

1. Nguyễn Đức Anh — 2A202601063
2. Phan Văn Hiếu — 2A202601227
3. Nguyễn Huy Tòa — 2A202601697
4. Tạ Long Khánh — 2A202601197
5. Vũ Đăng Huy — 2A202601761

**Ngày:** 03/08/2026

**Trạng thái bản ghép:** Đã ghép đủ chiến lược, benchmark và nhận xét của cả 5
thành viên. Kết quả Nguyễn Đức Anh được chạy lại bằng script chuẩn hóa trên corpus
RMIT, có raw top-3 và agent answer tại
`report/benchmark_rmit_nguyen_duc_anh.json`; nhóm đã chốt chiến lược cuối.

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

| #   | Tên tài liệu                             | Nguồn (Source URL)                                                                                               | Ngày lấy / Phiên bản    | Số ký tự | Metadata đã gán                       |
| --- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------- | -------- | ------------------------------------- |
| 1   | Resources for students with a disability | [RMIT](https://www.rmit.edu.vn/libraryvn/student-support/resources-for-students-with-a-disability)               | 2026-08-03 / not-stated | 949      | student, library, accessibility, en   |
| 2   | Borrowing and returning                  | [RMIT](https://www.rmit.edu.vn/libraryvn/borrowing-and-resources/borrowing-and-returning)                        | 2026-08-03 / not-stated | 3,553    | all, library, borrowing-policy, en    |
| 3   | Develop course content                   | [RMIT](https://www.rmit.edu.vn/libraryvn/teacher-support/developing-course-content)                              | 2026-08-03 / not-stated | 975      | faculty, library, teacher-support, en |
| 4   | Library hours and locations              | [RMIT](https://www.rmit.edu.vn/libraryvn/about-us/hours-and-locations)                                           | 2026-08-03 / not-stated | 1,776    | all, library, opening-hours, en       |
| 5   | Library resources and collections        | [RMIT](https://www.rmit.edu.vn/libraryvn/borrowing-and-resources/library-resources)                              | 2026-08-03 / not-stated | 3,816    | all, library, library-resources, en   |
| 6   | RMIT Vietnam Library rules               | [RMIT](https://www.rmit.edu.vn/libraryvn/about-us)                                                               | 2026-08-03 / not-stated | 778      | all, library, library-rules, en       |
| 7   | Study FAQs                               | [RMIT](https://www.rmit.edu.vn/libraryvn/student-support/study-faq)                                              | 2026-08-03 / not-stated | 24,139   | student, library, student-support, en |
| 8   | Book a study room                        | [RMIT](https://www.rmit.edu.vn/libraryvn/student-support/book-a-study-room)                                      | 2026-08-03 / not-stated | 1,354    | student, library, room-booking, en    |
| 9   | Workshops and consultations for students | [RMIT](https://www.rmit.edu.vn/libraryvn/teacher-support/organise-workshops-and-consultations-for-your-students) | 2026-08-03 / not-stated | 1,135    | faculty, library, teacher-support, en |

> Số ký tự được tính trên phần nội dung sau YAML front matter, đúng với dữ liệu
> được `ingest.py` đưa vào chunker.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Tập tài liệu chỉ chứa 9 trang công khai của RMIT Việt Nam, không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version` và metadata phân loại.
- [x] `sources.csv` có đúng 9 dòng và khớp một-một với 9 tài liệu.
- [x] `audience` có nhiều giá trị (`student`, `faculty`, `all`) nên bộ lọc có tác dụng thực tế.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata    | Kiểu              | Ví dụ giá trị                 | Tại sao hữu ích cho truy xuất (retrieval)?                                              |
| ------------------ | ----------------- | ----------------------------- | --------------------------------------------------------------------------------------- |
| `doc_id`           | string, duy nhất  | `rmit-study-room-booking`     | Liên kết chunk với tài liệu gốc, hỗ trợ truy vết và xóa toàn bộ chunk của một tài liệu. |
| `title`            | string            | `Book a study room`           | Giúp nhận diện nội dung và trình bày nguồn dễ đọc.                                      |
| `source_url`       | URL string        | `https://www.rmit.edu.vn/...` | Cho phép kiểm chứng câu trả lời tại nguồn công khai.                                    |
| `retrieved_at`     | ISO date string   | `2026-08-03`                  | Ghi nhận thời điểm thu thập để đánh giá độ mới của dữ liệu.                             |
| `document_version` | string            | `not-stated`                  | Theo dõi phiên bản; dùng `not-stated` khi trang không công bố phiên bản.                |
| `audience`         | enum              | `student`, `faculty`, `all`   | Pre-filter đúng nhóm người dùng trước khi xếp hạng embedding.                           |
| `department`       | string            | `library`                     | Thu hẹp đơn vị cung cấp dịch vụ khi corpus được mở rộng.                                |
| `category`         | string            | `room-booking`                | Phân biệt quy định mượn sách, giờ mở cửa, hỗ trợ học tập và dịch vụ giảng viên.         |
| `language`         | ISO language code | `en`                          | Hỗ trợ chọn tài liệu theo ngôn ngữ truy vấn hoặc câu trả lời.                           |

### Kết quả CHECKPOINT 2

Script kiểm tra chính thức ghi nhận: **9/9 file OK**, `sources.csv` **khớp**;
phân bố `audience` là `student: 3`, `all: 4`, `faculty: 2`.

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu                   | Chiến lược (Strategy)            | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                                          |
| -------------------------- | -------------------------------- | -------------- | ----------------- | ----------------------------------------------------------------- |
| `rmit-borrowing-returning` | FixedSizeChunker (`fixed_size`)  | 10             | 391.3             | Không ổn định: có thể cắt giữa câu/mục.                           |
| `rmit-borrowing-returning` | SentenceChunker (`by_sentences`) | 8              | 441.4             | Giữ câu nhưng có chunk vượt mục tiêu 400 ký tự.                   |
| `rmit-borrowing-returning` | RecursiveChunker (`recursive`)   | 10             | 353.5             | Khá tốt: ưu tiên đoạn, dòng, câu rồi từ.                          |
| `rmit-study-room-booking`  | FixedSizeChunker (`fixed_size`)  | 4              | 368.5             | Có overlap nhưng vẫn có thể mất ranh giới heading.                |
| `rmit-study-room-booking`  | SentenceChunker (`by_sentences`) | 2              | 675.0             | Giữ câu, nhưng list dài làm chunk quá lớn.                        |
| `rmit-study-room-booking`  | RecursiveChunker (`recursive`)   | 4              | 337.0             | Giữ phần lớn các cụm quy định liền nhau.                          |
| `rmit-study-faq`           | FixedSizeChunker (`fixed_size`)  | 67             | 399.7             | Cắt đều nhưng dễ trộn hai câu hỏi FAQ.                            |
| `rmit-study-faq`           | SentenceChunker (`by_sentences`) | 90             | 265.1             | Mạch lạc theo câu nhưng mất liên kết với câu hỏi/heading.         |
| `rmit-study-faq`           | RecursiveChunker (`recursive`)   | 74             | 324.2             | Tốt hơn fixed, nhưng mảnh sau của section dài có thể mất tiêu đề. |

Các số liệu trên được tính từ phần body sau khi `ingest.load_documents()` loại
YAML front matter, với `chunk_size=400`.

### Chiến lược của từng thành viên

> Mọi thành viên dùng cùng corpus `data/rmit-library`, cùng 5 query và local
> multilingual embedder. Khi chốt báo cáo, nhóm cần đính kèm raw output để thống
> nhất cách tính điểm theo `docs/SCORING.md`.

#### Thành viên 1 — Nguyễn Đức Anh (2A202601063)

- **Loại chiến lược:** Custom
  `HierarchicalSectionChunker(chunk_size=1600)` kết hợp sentence-level rerank
  (`0,5 × chunk cosine + 0,5 × max-sentence cosine`).
- **Mô tả & lý do chọn:** Chunker đọc cấp heading Markdown và giữ một heading
  cùng toàn bộ semantic subtree. Subtree ngắn trở thành một chunk; parent quá
  rộng được thay bằng các child subtree; chunk chỉ có heading bị loại và section
  quá dài mới fallback sang Recursive. Vì thế Q1 tách đúng mục “Undergraduate
  and postgraduate students”, không lẫn quota English students, còn Q5 giữ
  nguyên heading “Disputes” và cả 10 lý do. Sentence rerank giải quyết Q4, nơi
  cosine toàn chunk bị hai FAQ cùng chủ đề xếp trên trang accessibility.
- **Code snippet:**

```python
chunker = HierarchicalSectionChunker(chunk_size=1600)
base_store = build_knowledge_base(
    "data/rmit-library",
    embedding_fn=local_embedder,
    chunker=chunker,
)
store = SentenceRerankingStore(base_store, local_embedder)
```

- **Kết quả benchmark chuẩn hóa:** 119 chunk, độ dài trung bình 427,26 ký tự;
  evidence rank `[1, 1, 1, 1, 1]`; agent đúng 5/5; **10/10**. Ablation không
  rerank đạt 9/10 do Q4 ở rank 3. Raw output và toàn content/score nằm trong
  `report/benchmark_rmit_nguyen_duc_anh.json`.

#### Thành viên 2 — Phan Văn Hiếu (2A202601227)

- **Loại chiến lược:** Tuned `RecursiveChunker(chunk_size=300)`.
- **Mô tả & lý do chọn cho chủ đề này:** Tôi giữ nguyên corpus, 5 query và local
  embedder, rồi grid-search `chunk_size` từ 250 đến 800. Kích thước 300 là cấu
  hình duy nhất đưa answer-bearing evidence lên top-1 cho cả 5 query (10/10 theo
  evidence rank); nó tạo 166 chunk và giữ các cụm câu/list đủ gần để trả lời.
- **Code snippet:**

```python
# Dòng duy nhất chọn strategy cá nhân trong bench.py:
chunker = RecursiveChunker(chunk_size=300)
```

Kết quả tuning: size 250 = 7/10; 300 = **10/10**; 350–450 = 8/10;
500 = 7/10; 550–700 = 8/10; 800 = 9/10.

Ngoài strategy được chọn, tôi đã triển khai và chạy thử
`HeadingRecursiveChunker(chunk_size=400)` (187 chunks, 6/10) để kiểm tra cách
giữ heading path cho tài liệu quy định có cấu trúc mục. Kết quả này đáp ứng phần
thử nghiệm heading/section nhưng không được chọn làm strategy cuối vì bỏ lỡ
evidence của Query 3 trong top-3.

#### Thành viên 3 — Nguyễn Huy Tòa (2A202601697)

- **Loại chiến lược:** Custom `HeadingAwareChunker(max_chunk_size=400)` kết hợp
  `RecursiveChunker` làm fallback.
- **Mô tả & lý do chọn:** Corpus RMIT được biên soạn theo heading, section và
  các mục FAQ. Tách theo heading giúp mỗi chunk giữ một đơn vị ngữ nghĩa rõ ràng;
  section dài hơn 400 ký tự được chia tiếp bằng Recursive và gắn lại heading vào
  từng chunk con để hạn chế mất ngữ cảnh. Benchmark tạo 188 chunks và đạt 8/10.
- **Code snippet:**

```python
class HeadingAwareChunker:
    def __init__(self, max_chunk_size: int = 400) -> None:
        self.max_chunk_size = max(1, max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        sections = re.split(
            r"(?=^#{1,6}\s+)", text.strip(), flags=re.MULTILINE
        )
        chunks: list[str] = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            lines = section.splitlines()
            has_heading = bool(re.match(r"^#{1,6}\s+", lines[0]))
            heading = lines[0].strip() if has_heading else ""
            body = "\n".join(lines[1:]).strip() if has_heading else section

            if len(section) <= self.max_chunk_size:
                chunks.append(section)
                continue

            prefix = f"{heading}\n" if heading else ""
            recursive = RecursiveChunker(
                chunk_size=max(1, self.max_chunk_size - len(prefix))
            )
            chunks.extend(
                f"{prefix}{child}".strip()
                for child in recursive.chunk(body)
                if child.strip()
            )

        return chunks
```

#### Thành viên 4 — Tạ Long Khánh (2A202601197)

- **Loại chiến lược:** `RecursiveChunker(chunk_size=400)`.
- **Mô tả & lý do chọn:** Bộ dữ liệu chủ yếu là hướng dẫn và quy định thư viện
  RMIT có heading và đoạn văn rõ ràng. RecursiveChunker ưu tiên ranh giới tự
  nhiên như đoạn, xuống dòng và câu trước khi cắt theo ký tự, nhờ đó hạn chế chia
  cắt thông tin quan trọng và giữ ngữ cảnh tốt hơn cắt cứng.
- **Code snippet:**

```python
chunker = RecursiveChunker(chunk_size=400)
```

#### Thành viên 5 — Vũ Đăng Huy (2A202601761)

- **Loại chiến lược:** `FixedSizeChunker(chunk_size=500, overlap=100)`.
- **Mô tả & lý do chọn:** Đây là baseline đơn giản, dễ kiểm soát kích thước.
  Overlap 100 ký tự lặp lại nội dung ở biên chunk nhằm giảm nguy cơ mất dữ kiện
  khi vị trí cắt rơi giữa một câu hoặc một ý.
- **Code snippet:**

```python
chunker = FixedSizeChunker(
    chunk_size=500,
    overlap=100,
)
```

> Khi ghép báo cáo, giữ nguyên corpus, 5 query, local embedder, top-k và cách
> chấm; mọi thay đổi chunker/reranker phải được khai báo và có ablation riêng.

### So sánh các cấu hình trên cùng benchmark

| Thành viên/cấu hình | Chiến lược (Strategy)                          | Kết quả hiện có                                                              | Điểm mạnh                                                                                           | Điểm yếu                                                                                                  |
| ------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Baseline tham chiếu | FixedSize 400, overlap 40                      | 5                                                                            | 110 chunk, có overlap nên giữ được một phần ngữ cảnh biên.                                          | Có thể cắt giữa câu/mục; Q3 không có evidence trong top-3.                                                |
| Baseline tham chiếu | Sentence, 3 câu/chunk                          | 7                                                                            | Evidence xuất hiện top-3 ở cả 5 query.                                                              | Chunk dài không đều và có thể mất heading cha.                                                            |
| Baseline tham chiếu | Recursive 400                                  | **8**                                                                        | Cân bằng tốt nhất giữa coherence và kích thước; 5/5 query có evidence top-3.                        | Không lặp heading cho mảnh sau của section dài.                                                           |
| Baseline tham chiếu | Heading + Recursive 400                        | 6                                                                            | Giữ đầy đủ heading path; filter đưa evidence Q4 lên top-1.                                          | Tạo 187 chunk nhỏ; Q3 đúng document nhưng sai section trong cả top-3.                                     |
| Nguyễn Đức Anh      | **HierarchicalSection 1600 + sentence rerank** | **10/10 strict rubric**                                                      | 119 chunk; 5/5 evidence top-1 và agent đúng; Q1 không lẫn audience; Q5 đủ 10 lý do trong một chunk. | Phức tạp hơn baseline; ablation không rerank chỉ đạt 9/10 vì Q4 ở rank 3.                                 |
| Phan Văn Hiếu       | **Recursive 300**                              | **10/10 evidence-rank trong output cá nhân; 9/10 khi tái chấm strict agent** | 166 chunk trong output cá nhân; evidence xuất hiện top-3 ở 5/5 query.                               | Q1 trộn quota English và undergraduate; Q5 chia danh sách ngoại lệ qua hai chunk nên top-1 agent thiếu ý. |
| Nguyễn Huy Tòa      | Custom HeadingAware 400 + Recursive            | **8/10 evidence-rank**                                                       | 188 chunk; giữ heading/section; Q1, Q2, Q4 có full evidence top-1.                                  | Q3 gold chunk ở top-3; Q5 chỉ có partial evidence ở top-2; một số chunk chỉ có heading.                   |
| Tạ Long Khánh       | Recursive 400                                  | **5/5 query có evidence top-3; thành viên đề xuất 10/10** (\*)               | Giữ ngữ cảnh tốt; đa số query có chunk đúng top-1.                                                  | Accessibility đúng ở top-2, FAQ có nội dung ngữ nghĩa gần nên xếp trước.                                  |
| Vũ Đăng Huy         | FixedSize 500, overlap 100                     | **5/5 query có evidence top-3; thành viên đề xuất 10/10** (\*)               | Kích thước ổn định; overlap giữ ngữ cảnh; 4/5 query đúng top-1.                                     | Có thể cắt giữa câu/ý; Accessibility bị FAQ xếp trước.                                                    |

> Bảng trên dùng cùng corpus, 5 query, local multilingual embedder và top-k=3.
> Bốn dòng baseline là cấu hình tham chiếu, không phải thành viên. Dấu `(*)` cho
> biết điểm do thành viên tự báo cáo theo tiêu chí 5/5 query có chunk đúng trong
> top-3. Với hai cấu hình dẫn đầu, nhóm chấm thêm điều kiện strict: một chunk
> rank-1 phải đủ evidence và agent answer phải chứa đủ ý.

**Trong các cấu hình đã có raw evidence-rank, chiến lược nào tốt nhất? Tại sao?**

> Nhóm chọn **HierarchicalSection 1600 + sentence rerank của Nguyễn Đức Anh**.
> Cấu hình đạt 10/10 theo rubric đầy đủ, cả 5 answer-bearing chunk ở rank 1 và
> agent đúng 5/5. So với Recursive 300, nó dùng ít chunk hơn (119 so với 166/170
> tùy snapshot làm sạch), không trộn quota 10 và 25 ở Q1, đồng thời giữ cả 10 lý
> do của Q5 trong một chunk thay vì trải qua hai chunk. Ablation 9→10 ở Q4 còn
> chứng minh reranker giải quyết một failure đo được, không phải tuning cảm tính.

**Lệnh tái lập kết quả được chọn:**

```bash
python scripts/fetch_rmit_corpus.py
python scripts/run_rmit_benchmark.py --provider local
```

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| #   | Câu hỏi (Query)                                                                                                     | Metadata filter           | Câu trả lời chuẩn (Gold Answer)                                                                                                                                                                                                                                                                                                                      | Chunk/tài liệu chứa thông tin                                                    |
| --- | ------------------------------------------------------------------------------------------------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1   | How many items can undergraduate and postgraduate students borrow, for how long, and how many renewals are allowed? | Không                     | 25 items, 30 days, 1 renewal.                                                                                                                                                                                                                                                                                                                        | `rmit-borrowing-returning` → Student → Undergraduate and postgraduate students   |
| 2   | Under what conditions can a borrowed item be renewed, and how long does the renewal last?                           | Không                     | The item must not be overdue or reserved by another user. Renewal lasts 15 days; the maximum total loan period is 45 days.                                                                                                                                                                                                                           | `rmit-borrowing-returning` → Student                                             |
| 3   | What steps are required to book a Library study room?                                                               | Không                     | Log in with an RMIT account, choose the campus, select a room and time, then confirm the booking.                                                                                                                                                                                                                                                    | `rmit-study-room-booking` → How to book a room                                   |
| 4   | What support does the Library provide to make resources accessible?                                                 | `{"audience": "student"}` | Text digitisation, help obtaining digital resources, and converting PDF documents to text.                                                                                                                                                                                                                                                           | `rmit-accessibility-resources` → Resources for students with a disability        |
| 5   | Which reasons will the Library not accept when a user disputes a fine?                                              | Không                     | Lack of policy knowledge; unwillingness to take responsibility for an item loaned to a third party; forgetting the due date; not receiving reminders; a full email inbox; inability to visit often or distance; disagreement with the fine policy; being off campus; semester breaks or summer vacation; and changed opening hours are not accepted. | `rmit-borrowing-returning` → Disputes → We will not accept the following reasons |

Các gold answer trên chỉ tổng hợp dữ kiện có trong corpus. Bộ câu hỏi được cố định
trước khi chạy benchmark; câu 4 bắt buộc dùng `metadata_filter={"audience": "student"}`
để chứng minh tác dụng của metadata theo biến thể K3.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| Thành viên     |      Số chunk | Tóm tắt 5 query                                                                                                                              | Điểm/kết quả hiện có                              |
| -------------- | ------------: | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Nguyễn Đức Anh |       **119** | Evidence rank `1, 1, 1, 1, 1`; agent đúng 5/5; mỗi top-1 chứa đủ marker, kể cả 10/10 lý do ở Q5.                                             | **10/10 strict retrieval — được chọn**            |
| Phan Văn Hiếu  |           166 | Evidence-rank output cá nhân `1, 1, 1, 1, 1`; kiểm tra strict ghi nhận Q1 có thông tin cạnh tranh và top-1 Q5 thiếu phần danh sách ở rank 2. | 10/10 evidence-rank; **9/10 strict reproduction** |
| Nguyễn Huy Tòa |           188 | Q1, Q2, Q4 full evidence top-1; Q3 gold chunk top-3; Q5 partial evidence top-2.                                                              | 8/10 evidence-rank                                |
| Tạ Long Khánh  | Chưa cung cấp | 5/5 query có chunk liên quan top-3; Accessibility ở top-2.                                                                                   | Thành viên đề xuất 10/10; chờ chuẩn hóa rubric    |
| Vũ Đăng Huy    | Chưa cung cấp | 5/5 query có chunk liên quan top-3; 4/5 top-1; Accessibility bị chunk FAQ xếp trước.                                                         | Thành viên đề xuất 10/10; chờ chuẩn hóa rubric    |

| #   | Câu hỏi                            | Chiến lược tốt nhất cho câu này        | Có chunk liên quan trong top-3? | Ghi chú                                                                                              |
| --- | ---------------------------------- | -------------------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 1   | Borrowing quota/period/renewals    | **HierarchicalSection + rerank**       | Có, top-1                       | Chunk chỉ chứa đúng subsection undergraduate/postgraduate: 25/30/1, không có quota 10.               |
| 2   | Renewal conditions/duration        | HierarchicalSection hoặc Recursive     | Có, top-1                       | Điều kiện và 15/45 ngày được giữ trong cùng subtree.                                                 |
| 3   | Study-room booking procedure       | HierarchicalSection hoặc Recursive 300 | Có, top-1                       | Chunk chứa trọn `log in → choose → select → confirm`.                                                |
| 4   | Accessibility support              | **HierarchicalSection + rerank**       | Có, top-1 khi filter            | Không filter: evidence không có top-3; filter + rerank đưa trang accessibility từ rank 3 lên rank 1. |
| 5   | Reasons rejected in a fine dispute | **HierarchicalSection + rerank**       | Có, top-1                       | Một chunk chứa heading Disputes và đủ cả 10 lý do; agent không phải ghép hai chunk.                  |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> Có, tác động rất rõ ở query 4. Không filter, evidence không xuất hiện trong
> top-3 của bất kỳ strategy nào vì các chunk tài nguyên chung (`audience=all`)
> chiếm thứ hạng cao. Với `{"audience": "student"}`, evidence lên rank 3 (Fixed,
> Sentence), rank 2 (Recursive 400) và rank 1 (Heading 400, Recursive 300), vừa
> tăng precision vừa giữ được recall của tài liệu dành cho sinh viên.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Nhận xét của từng thành viên

#### Phan Văn Hiếu — Recursive 300

Recursive 300 đưa answer-bearing evidence lên top-1 cho cả 5 query trong phép
chấm tự động. Tuy nhiên Q1 trộn quota của English students với undergraduate và
postgraduate trong cùng chunk, còn danh sách ngoại lệ của Q5 bị chia qua hai
chunk. Kết quả này cho thấy evidence hit và score cao vẫn cần được kiểm tra thêm
về chunk coherence và độ đầy đủ của agent answer.

#### Nguyễn Huy Tòa — HeadingAware 400 + Recursive fallback

Heading-aware giữ được tên section trong các mảnh con và giúp Query 1, 2, 4 có
full evidence ở top-1; metadata filter cải thiện rõ Query 4. Điểm yếu là một số
chunk chỉ chứa heading, không có overlap nên danh sách dài có thể bị chia đôi;
gold chunk của Query 3 chỉ ở top-3 và Query 5 chỉ có partial evidence ở top-2.
Hướng cải thiện là loại chunk chỉ có heading, thêm overlap có kiểm soát và nối
chunk kế cận khi câu trả lời là danh sách dài.

#### Tạ Long Khánh — Recursive 400

Kết quả thành viên cung cấp cho thấy cả 5 câu hỏi đều truy xuất được chunk liên
quan trong top-3 và đa số ở top-1. Failure đáng chú ý là Accessibility: dù filter
`audience=student` hoạt động đúng, chunk đáp án vẫn ở top-2 vì tài liệu FAQ có
nhiều từ/ngữ nghĩa gần với query. Hướng cải thiện là bổ sung filter `category`
hoặc `department`, đồng thời thử heading kết hợp Recursive để phân biệt tốt hơn
các tài liệu cùng chủ đề.

#### Vũ Đăng Huy — FixedSize 500, overlap 100

FixedSize tạo chunk ổn định và overlap giúp giữ ngữ cảnh tại biên; theo kết quả
thành viên cung cấp, 5/5 query có chunk liên quan trong top-3 và 4/5 ở top-1.
Accessibility tiếp tục là trường hợp khó vì FAQ có độ tương đồng ngữ nghĩa cao
hơn chunk đáp án. Hướng cải thiện là tuning `chunk_size`/`overlap` và bổ sung
metadata `category` hoặc `section`; nhược điểm cố hữu vẫn là khả năng cắt giữa
câu hay giữa một ý.

#### Nguyễn Đức Anh

HierarchicalSection giải quyết trực tiếp hai lỗi coherence quan trọng: Q1 có
subtree riêng cho undergraduate/postgraduate nên không lẫn quota English, còn Q5
giữ nguyên danh sách 10 lý do dưới heading Disputes. Chỉ chunking chưa đủ: ở Q4,
trang accessibility đứng rank 3 vì FAQ gần chủ đề hơn. Sentence rerank nâng nó lên
rank 1 sau metadata pre-filter. Kết quả cuối có 119 chunk, 5/5 rank-1, agent đúng
5/5 và raw top-3 đầy đủ; điểm yếu là cần thêm một lượt embedding theo câu.

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

> - Nhiều strategy cùng đạt 5/5 hit trong top-3 nhưng thứ hạng và độ sạch của
>   context khác nhau; chỉ kiểm `doc_id` hoặc top-3 hit sẽ che mất lỗi coherence.
> - Evidence hit chưa đồng nghĩa đáp án sạch: Q1 top-1 của Recursive 300 có đủ
>   25/30/1 nhưng cũng chứa quota 10 của English students.
> - Metadata filter thay đổi kết quả rõ nhất ở Query 4; sau filter, evidence của
>   Nguyễn Đức Anh và Phan lên top-1, còn Tạ Long Khánh báo cáo ở top-2.
> - Heading-aware giữ section tốt nhưng có thể tạo chunk chỉ có heading và chia
>   đôi danh sách; FixedSize có overlap giữ biên nhưng vẫn có thể cắt giữa ý.
> - Ablation của Nguyễn Đức Anh cho thấy cùng 119 chunk, chỉ thêm sentence rerank
>   đã đưa Q4 từ rank 3 lên rank 1 và tổng điểm từ 9/10 lên 10/10.

**Bài học rút ra khi so sánh trong nhóm:**

> Không có một đặc điểm đơn lẻ như chunk nhỏ, overlap hay heading luôn tốt cho mọi
> query. Recursive 300 mạnh về evidence hit, HeadingAware giữ cấu trúc, còn
> FixedSize là baseline dễ giải thích. Cấu hình Nguyễn Đức Anh kết hợp hierarchy
> để giữ điều kiện/list với rerank theo câu để xử lý nhiễu cùng chủ đề, nên thắng
> khi chấm đồng thời rank, completeness và agent grounding. So sánh công bằng
> luôn phải khóa corpus, query, embedder, filter, top-k và rubric agent answer.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> Dùng HierarchicalSection + sentence rerank của Nguyễn Đức Anh làm cấu hình cuối,
> giữ Recursive 300 làm baseline. Tiếp tục gắn metadata cấp section (`student`,
> `staff`, `alumni`, `category`), cache sentence embedding để giảm chi phí, rồi
> chạy mọi strategy qua cùng script chấm evidence-rank và agent answer.

### Failure case có bằng chứng — Query 1

- **Query:** quota/period/renewals của undergraduate/postgraduate students.
- **Top-1:** `rmit-borrowing-returning::chunk_2`, score 0.6875, có đủ evidence
  25 items / 30 days / 1 renewal nhưng phần đầu cùng chunk còn chứa quota 10 items
  của English students. Agent trích cả hai số nên câu trả lời có thể mơ hồ.
- **Nguyên nhân:** Recursive 300 ưu tiên separator tự nhiên nhưng vẫn ghép hai
  subsection liền nhau nếu tổng độ dài dưới ngưỡng; evidence checker chỉ kiểm sự
  hiện diện của chuỗi đúng, không phát hiện thông tin đối tượng cạnh tranh.
- **Đề xuất:** bổ sung heading boundary không cho ghép hai subsection vai trò,
  hoặc rerank/extract từ đúng đoạn bắt đầu tại heading “Undergraduate and
  postgraduate students”. `HierarchicalSectionChunker` đã hiện thực thay đổi này:
  top-1 mới là chunk 3, score 0.621724, có 25/30/1 và không chứa quota 10.

### Failure case và ablation — Query 4

- **Trước rerank:** cùng `HierarchicalSectionChunker`, trang accessibility chỉ ở
  rank 3 (base score 0.530871); hai FAQ cùng chủ đề đứng trên, nên agent trả lời sai
  và cấu hình chỉ đạt 9/10.
- **Nguyên nhân:** cosine toàn chunk đo độ giống chủ đề, không đo mật độ câu trả
  lời; trang accessibility chứa thêm wheelchair/ELA nên vector bị pha loãng.
- **Sau sửa:** pre-filter `audience=student`, sau đó kết hợp `0,5 × chunk cosine`
  với `0,5 × max-sentence cosine`. Evidence lên rank 1 (0.610174), đủ ba marker,
  agent đúng; không filter vẫn 0/2, chứng minh metadata thực sự cần thiết.

---

## Tự Đánh Giá (Phần Nhóm)

> Nhóm đã ghép đủ 5 chiến lược, corpus 9 nguồn công khai, benchmark raw, A/B
> metadata filter, failure case và giao diện demo có nguồn truy vết.

| Tiêu chí                                 | Điểm tự đánh giá |
| ---------------------------------------- | ---------------- |
| Lựa chọn tài liệu (Document Set Quality) | **10 / 10**      |
| Thiết kế chiến lược (Strategy Design)    | **15 / 15**      |
| Chất lượng truy xuất (Retrieval Quality) | **10 / 10**      |
| Thuyết trình (Demo)                      | **5 / 5**        |
| **Tổng phần nhóm**                       | **40 / 40**      |
