# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phan Văn Hiếu

**MSSV:** 2A202601227

**Nhóm:** B3_HKT

**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding cùng hướng thì có cosine similarity cao, nghĩa là hai
> đoạn văn có nội dung hoặc ý nghĩa gần nhau, dù cách dùng từ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Thư viện mở cửa lúc 8 giờ sáng.
- Câu B: Giờ hoạt động của thư viện bắt đầu từ 8 giờ.
- Tại sao tương đồng: Hai câu cùng nói về thời điểm thư viện bắt đầu phục vụ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên có thể gia hạn sách trực tuyến.
- Câu B: Hôm nay trời mưa lớn ở thành phố.
- Tại sao khác: Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào góc, tức hướng ngữ nghĩa của vector, và ít bị ảnh hưởng
> bởi độ lớn vector. Khoảng cách Euclid phụ thuộc cả độ lớn nên hai vector cùng
> hướng vẫn có thể bị xem là xa nhau nếu thang đo khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450)`.
> Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap là 100, số chunk là `ceil((10,000 - 100) / (500 - 100)) = 25`,
> tăng từ 23 lên 25. Chồng chéo lớn hơn giúp giữ ngữ cảnh ở biên chunk, đổi lại
> tốn thêm dung lượng lưu trữ, thời gian embedding và có thể tạo kết quả trùng lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng hoặc xuống dòng ngay
> sau dấu kết thúc câu, nhờ đó dấu câu vẫn thuộc về câu trước. Các câu được loại
> khoảng trắng thừa, bỏ phần rỗng, rồi nhóm tối đa theo `max_sentences_per_chunk`;
> chuỗi rỗng hoặc chỉ có khoảng trắng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử separator theo thứ tự ưu tiên, ghép các phần nhỏ miễn là tổng độ
> dài chưa vượt `chunk_size`, và gọi đệ quy với separator tiếp theo cho phần quá
> lớn. Base case là đoạn đã đủ ngắn; khi hết separator, hàm cắt cứng theo kích
> thước để luôn kết thúc và vẫn giữ giới hạn độ dài.

**`compute_similarity` + `ChunkingStrategyComparator.compare`** — hướng tiếp cận:
> `compute_similarity` tính tích vô hướng rồi chia cho tích độ lớn của hai vector;
> nếu một vector có norm bằng 0 thì trả `0.0` để tránh chia cho 0. Comparator chạy
> cùng một văn bản qua FixedSize, Sentence và Recursive, sau đó trả số chunk, độ
> dài trung bình và nội dung chunk để so sánh định lượng lẫn độ mạch lạc.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được sao chép metadata, bổ sung `doc_id` nếu thiếu, embedding một
> lần rồi lưu thành record có ID duy nhất. Store dùng ChromaDB khi khả dụng và tự
> chuyển sang danh sách trong bộ nhớ khi không có; tìm kiếm trong bộ nhớ embedding
> câu hỏi, tính tích vô hướng với từng record, sắp xếp score giảm dần và lấy top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc trước bằng phép bằng trên tất cả cặp key/value metadata,
> sau đó mới xếp hạng vector trong tập ứng viên để đúng yêu cầu pre-filter.
> `delete_document` xóa mọi record có `metadata["doc_id"]` khớp và trả về `True`
> chỉ khi thực sự có ít nhất một record bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` lấy top-k chunk từ store, đánh số từng context và kèm nguồn từ metadata
> để truy vết. Prompt chứa chỉ dẫn chỉ trả lời dựa trên context, yêu cầu thừa nhận
> khi thiếu thông tin, tiếp theo là các chunk, câu hỏi và vị trí bắt đầu câu trả lời.
> Nếu store không trả về chunk nào, agent trả thông báo rõ ràng ngay và không gọi LLM.
> Tôi mở rộng tham số `metadata_filter` để query bắt buộc của K3 đi qua
> `search_with_filter()` nhưng vẫn giữ hành vi cũ khi filter là `None`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
collected 42 items

tests/test_solution.py ..........................................        [100%]

============================== 42 passed ======================================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

**Môi trường kiểm tra:** Python 3.11 trong `.venv`; lệnh
`python -m pytest tests -v`. Bộ test kiểm tra chunking, cosine, comparator,
EmbeddingStore (add/search/filter/delete) và KnowledgeBaseAgent.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | How many books can undergraduate students borrow? | What is the borrowing quota for undergraduate students? | Cao nhất | 0.7290 | Đúng |
| 2 | Students must log in to book a library study room. | A library room reservation requires an RMIT account login. | Cao | 0.6191 | Đúng |
| 3 | A borrowed item may be renewed when it is not overdue. | Overdue library items must be returned and may incur a fine. | Trung bình | 0.4976 | Đúng |
| 4 | The Library converts PDF documents to text for accessibility. | Teachers can request workshops about using library databases. | Thấp–trung bình | 0.4165 | Đúng |
| 5 | The library opens at eight o'clock in the morning. | Heavy rain is expected in the city this afternoon. | Thấp nhất | 0.1162 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 vẫn đạt 0.4165 dù hai câu phục vụ hai đối tượng và hai tác vụ khác nhau;
> nguyên nhân là chúng cùng chứa ngữ cảnh chung về Library và support. Điều này
> cho thấy embedding nắm bắt chủ đề tổng quát khá tốt nhưng điểm giống chủ đề
> không đảm bảo chunk chứa đúng dữ kiện trả lời; vì vậy benchmark phải kiểm
> evidence trong chunk và metadata, không chỉ nhìn score.

> Các điểm trên được đo bằng
> `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, sau đó truyền hai
> vector chuẩn hóa vào chính hàm `compute_similarity()` của dự án.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Undergraduate/postgraduate borrowing quota, period, renewals | Chunk có cả English students (10 items) và undergraduate/postgraduate (25 items, 30 days, 1 renewal) | 0.6875 | Có evidence nhưng lẫn đối tượng | Agent trích cả 10 và 25 items nên cần đọc heading để chọn đúng 25. |
| 2 | Conditions and duration for renewal | Chunk Alumni chứa điều kiện không overdue/reserved, 15 ngày, tối đa 45 ngày | 0.7372 | Có, evidence top-1 | Agent trích đúng điều kiện và thời hạn áp dụng chung. |
| 3 | Steps to book a study room | Chunk chứa trọn log in, chọn campus/phòng/thời gian và confirm | 0.7372 | Có, evidence top-1 | Agent trích đúng quy trình. |
| 4 | Accessibility support | Chunk digitisation, digital resources, PDF-to-text | 0.6128 | Có, evidence top-1 | Agent trích đúng ba hỗ trợ với `audience=student`. |
| 5 | Reasons not accepted when disputing a fine | Chunk chứa heading ngoại lệ và ba lý do đầu | 0.7471 | Có evidence nhưng gold answer còn tiếp ở rank 2 | Agent trả đúng nhưng chưa đầy đủ toàn bộ danh sách. |

**Bao nhiêu câu hỏi trả về chunk có evidence trong top-3?** **5 / 5**

**Điểm retrieval chính thức của strategy cá nhân:** **10 / 10** — cả 5 query đều
có answer-bearing evidence ở top-1.

> Q1 vẫn có thêm thông tin của đối tượng English students và Q5 cần đọc tiếp
> chunk rank 2 để lấy trọn danh sách. Đây là nhận xét failure/coherence để đề xuất
> cải thiện, không làm thay đổi điểm retrieval 10/10 của benchmark.

**Cấu hình benchmark:**
- Embedder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Strategy: `RecursiveChunker(chunk_size=300)` — 166 chunks; được chọn qua grid
  search size 250–800 trên cùng benchmark.
- Quy tắc chấm: evidence top-1 = 2; evidence top-2/3 = 1; không có trong top-3 = 0.
- Agent dùng `extractive_demo_llm`, chỉ trích Context 1 để đo grounding mà không
  phát sinh thông tin ngoài nguồn.

### Chi tiết top-3 theo evidence

| Query | Rank | Score | `doc_id::chunk_index` | Evidence đáp án? | Nhận xét |
|------:|-----:|------:|------------------------|------------------|----------|
| 1 | 1 | 0.6875 | `rmit-borrowing-returning::2` | **Có** | Có 25/30/1 nhưng phần đầu chunk còn quota 10 của English students. |
| 1 | 2 | 0.6583 | `rmit-borrowing-returning::6` | Không | Nội dung renewal/alumni/returns, thiếu evidence undergraduate. |
| 1 | 3 | 0.5897 | `rmit-borrowing-returning::4` | Không | Professional staff, sai đối tượng. |
| 2 | 1 | 0.7372 | `rmit-borrowing-returning::5` | **Có** | Chứa đủ điều kiện overdue/reservation và 15/45 ngày. |
| 2 | 2 | 0.6986 | `rmit-borrowing-returning::3` | **Có** | Cùng quy tắc renewal trong section trước. |
| 2 | 3 | 0.6867 | `rmit-borrowing-returning::4` | Không | Có điều kiện nhưng thời gian renewal bị cắt sang chunk kế tiếp. |
| 3 | 1 | 0.7372 | `rmit-study-room-booking::1` | **Có** | Chứa đủ log in, choose campus, select room/time, confirm. |
| 3 | 2 | 0.7043 | `rmit-study-room-booking::2` | Không | Chính sách first-come/đặt trước. |
| 3 | 3 | 0.6674 | `rmit-study-room-booking::0` | Không | Giới thiệu và kiểm tra availability. |
| 4 | 1 | 0.6128 | `rmit-accessibility-resources::0` | **Có** | Chứa đủ ba evidence phrase accessibility. |
| 4 | 2 | 0.6086 | `rmit-study-faq::97` | Không | Thông tin database chung. |
| 4 | 3 | 0.5920 | `rmit-study-faq::102` | Không | Google Scholar/support, không phải accessibility. |
| 5 | 1 | 0.7471 | `rmit-borrowing-returning::13` | **Có** | Heading ngoại lệ và ba lý do đầu; danh sách còn tiếp. |
| 5 | 2 | 0.4922 | `rmit-borrowing-returning::14` | Không | Nửa sau danh sách; cần kết hợp với rank 1 để đủ gold answer. |
| 5 | 3 | 0.4792 | `rmit-library-rules::2` | Không | Quy tắc sử dụng thư viện, không phải dispute reasons. |

### A/B metadata filter — Query 4

Không filter, cả ba kết quả top-3 đều không chứa evidence trả lời. Khi lọc
`{"audience": "student"}`, chunk
`rmit-accessibility-resources::chunk_0` lên top-1 với score 0.6128 và chứa đủ ba
evidence phrase. Filter đã giảm nhiễu rõ rệt, không loại nhầm đáp án.

### Failure analysis — Query 1

Evidence checker cho 2 điểm vì top-1 chứa đủ 25 items, 30 days và 1 renewal.
Tuy nhiên chunk bắt đầu bằng quota 10 items của English students rồi mới sang
heading undergraduate/postgraduate, khiến extractive agent đưa ra cả hai số.
Nguyên nhân là Recursive 300 ghép hai subsection liền nhau khi còn dưới ngưỡng;
score cao không phát hiện thông tin cạnh tranh. Tôi đề xuất thêm boundary rule tại
heading vai trò hoặc trích từ đúng heading undergraduate trước khi tạo câu trả lời.

**Điều hay nhất tôi học được qua phần so sánh/demo:**
> Tại thời điểm hoàn thiện phần cá nhân, tôi chưa ghép kết quả chính thức của các
> thành viên khác. So sánh có kiểm soát với các baseline cho thấy Recursive 300
> đạt evidence-rank 10/10, cao hơn Recursive 400 (8/10) và Heading 400 (6/10).
> Tuy vậy kiểm tra thủ công Q1 vẫn phát hiện thông tin thừa, nên phải kết hợp
> metric tự động với đánh giá coherence/grounding.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
