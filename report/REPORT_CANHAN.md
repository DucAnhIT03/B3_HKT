# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Huy Tỏa
**Nhóm:** HKT
**Ngày:** 3/8

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau, cho thấy hai đoạn văn có nội dung hoặc ý nghĩa tương đồng, dù chúng có thể sử dụng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên được mượn sách trong 30 ngày.
- Câu B: Thời hạn vay tài liệu dành cho người học là một tháng.
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng cùng nói về thời hạn sinh viên được mượn tài liệu thư viện.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên được mượn sách trong 30 ngày.
- Câu B: Thư viện đóng cửa vào các ngày lễ.
- Tại sao khác: Câu thứ nhất nói về thời hạn mượn tài liệu, còn câu thứ hai nói về lịch hoạt động của thư viện.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity so sánh hướng của hai vector nên tập trung tốt hơn vào mức độ tương đồng ngữ nghĩa và ít bị ảnh hưởng bởi độ lớn vector. Khoảng cách Euclid phụ thuộc trực tiếp vào cả hướng lẫn độ lớn, vì vậy hai vector biểu diễn nội dung gần nhau vẫn có thể bị xem là xa nếu độ lớn của chúng khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Bước dịch giữa hai chunk liên tiếp là `500 - 50 = 450` ký tự. Số chunk được tính bằng `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.111...) = 23`.
>
> **Đáp án: 23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước dịch giảm còn `500 - 100 = 400` ký tự và số chunk tăng thành `ceil((10,000 - 100) / 400) = ceil(24.75) = 25`. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới giữa các chunk, nhưng làm tăng nội dung trùng lặp, dung lượng lưu trữ và chi phí embedding/tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng đứng sau dấu kết thúc câu, nhờ đó dấu câu vẫn được giữ ở cuối phần trước. Sau khi `strip()` và loại phần rỗng, tôi duyệt danh sách theo từng nhóm `max_sentences_per_chunk` câu rồi ghép mỗi nhóm bằng một khoảng trắng; text rỗng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Hàm `chunk()` xử lý text rỗng, gọi `_split()` với danh sách separator theo thứ tự ưu tiên rồi loại các chunk rỗng. `_split()` trả ngay khi đoạn đã không vượt `chunk_size`; nếu hết separator hoặc gặp separator rỗng thì cắt cố định, còn nếu separator hiện tại không xuất hiện thì chuyển sang separator tiếp theo. Các phần vừa kích thước được gộp lại, trong khi phần quá dài được xử lý đệ quy với separator ưu tiên thấp hơn để bảo đảm thuật toán luôn tiến gần điều kiện dừng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi dùng store in-memory và chuẩn hóa mỗi `Document` thành record gồm ID duy nhất, nội dung, bản sao metadata và embedding. `add_documents()` nhúng mỗi tài liệu đúng một lần rồi thêm record vào `_store`; `search()` chỉ tạo query embedding một lần, tính tích vô hướng với embedding của từng record, sắp xếp score giảm dần và lấy `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter()` lọc record trước bằng cách yêu cầu mọi cặp key/value trong `metadata_filter` đều khớp, sau đó mới gọi chung `_search_records()` để xếp hạng; cách này tránh mất tài liệu hợp lệ nếu lọc sau top-k. `delete_document()` tạo lại danh sách record sau khi loại tất cả chunk có `metadata['doc_id']` trùng ID cần xóa và trả `True` khi kích thước store thực sự giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer()` gọi store để lấy top-k chunk, đánh số từng nguồn `[1]`, `[2]` và đưa cả `doc_id`, URL/path nguồn cùng nội dung vào phần `Context`. Prompt yêu cầu LLM chỉ dùng context, trích dẫn bằng số chunk và nói rõ khi thông tin không đủ; nếu store không trả kết quả, agent trả thông báo trực tiếp thay vì gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- .venv\Scripts\python.exe
rootdir: C:\Users\huyto\Downloads\AITHUCCHIEN\lab\B3_HKT
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.06s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các điểm thực tế được đo bằng local embedding `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` và hàm `compute_similarity()`. Để đối chiếu cột dự đoán theo hai mức, tôi quy ước cosine score **từ 0.50 trở lên là cao**, dưới 0.50 là thấp; đây chỉ là ngưỡng thực hành cho 5 cặp này, không phải ngưỡng phổ quát cho mọi hệ thống embedding.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Students may borrow 25 items for 30 days. | Undergraduate and postgraduate students have a loan quota of 25 items and a loan period of 30 days. | Cao — hai câu cùng số lượng và thời hạn mượn. | **0.8111** (cao) | Đúng |
| 2 | Log in with your RMIT account to book a library study room. | Use your RMIT credentials, choose a campus, room and time, then confirm the reservation. | Cao — hai câu cùng mô tả quy trình đặt phòng bằng tài khoản RMIT. | **0.4760** (thấp) | Sai |
| 3 | The library is closed on public holidays. | Overdue library items incur a fine of VND 5,000 per item per day. | Thấp — một câu nói về giờ hoạt động, câu còn lại nói về tiền phạt. | **0.2648** (thấp) | Đúng |
| 4 | The library converts PDF documents to text for students with disabilities. | Lecturers can embed library resources in Canvas course content. | Thấp — cùng nhắc tài nguyên thư viện nhưng khác đối tượng và mục đích hỗ trợ. | **0.4761** (thấp) | Đúng |
| 5 | Food is allowed inside the library. | Users can bring beverages but not food into the library. | Thấp — hai phát biểu trái ngược nhau về việc mang đồ ăn. | **0.5524** (cao) | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 5 bất ngờ nhất vì hai câu mâu thuẫn về việc cho phép đồ ăn nhưng vẫn đạt cosine 0.5524 và bị xếp mức cao. Kết quả này cho thấy embedding nhận ra rất mạnh chủ đề và từ vựng chung như “food”, “allowed” và “library”, nhưng không phải lúc nào cũng biểu diễn tốt phủ định hoặc tính đúng-sai của mệnh đề. Cặp 2 cũng cho thấy các câu mô tả cùng quy trình có thể chưa đạt điểm cao khi cách diễn đạt và lượng chi tiết khác nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Cấu hình đo:** `HeadingAwareChunker(max_chunk_size=400)`, local embedding `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, corpus `data/rmit-library` gồm 188 chunks, `top_k=3`. Query 4 dùng `metadata_filter={"audience": "student"}`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Cosine score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) | Điểm rubric (/2) |
|---|-------|--------------------------------|-------|-----------|------------------------|------------------|
| 1 | How many items can undergraduate and postgraduate students borrow, for how long, and how many renewals are allowed? | `rmit-borrowing-returning::chunk_4`: đúng mục undergraduate/postgraduate, chứa 25 items, 30 days và 1 renewal. | 0.7049 | Có — full evidence ở top-1. | Đúng: 25 tài liệu, 30 ngày và 1 lần gia hạn; câu trả lời có thêm điều kiện gia hạn. | **2** |
| 2 | Under what conditions can a borrowed item be renewed, and how long does the renewal last? | `rmit-borrowing-returning::chunk_8`: mục Alumni nhưng chứa đủ điều kiện không overdue/không reserved và thời gian gia hạn 15 ngày, tối đa 45 ngày. | 0.7241 | Có — full evidence ở top-1. | Đúng điều kiện và thời gian; có thêm quota của alumni nhưng không làm sai đáp án. | **2** |
| 3 | What steps are required to book a Library study room? | `rmit-study-room-booking::chunk_0`: chỉ giới thiệu công dụng của study room, không chứa các bước đặt phòng. | 0.7926 | Không ở top-1; full evidence chỉ đứng top-3. | Thiếu: agent chỉ trả phần giới thiệu, không nêu đăng nhập, chọn campus/phòng/thời gian và xác nhận. | **1** |
| 4 | What support does the Library provide to make resources accessible? | `rmit-accessibility-resources::chunk_0`: chứa đủ text digitisation, hỗ trợ lấy digital resources và chuyển PDF thành text. | 0.6203 | Có — full evidence ở top-1 sau khi lọc `audience=student`. | Đúng và được grounded đầy đủ trong chunk top-1. | **2** |
| 5 | Which reasons will the Library not accept when a user disputes a fine? | `rmit-borrowing-returning::chunk_17`: chỉ hướng dẫn trao đổi với service desk, không chứa danh sách lý do bị từ chối. | 0.7373 | Không ở top-1; top-2 chỉ có partial evidence và top-3 thiếu `Changed opening hours`. | Sai/thiếu: agent nói thư viện sẽ xem xét khiếu nại nhưng không liệt kê các lý do không được chấp nhận. | **1** |

**Tổng điểm benchmark cá nhân:** **8/10**.

### Bằng chứng top-3 ở mức chunk

| Query | Hạng | Chunk | Score | Đánh giá evidence | Ghi chú |
|-------|------|-------|-------|-------------------|---------|
| 1 | 1 | `rmit-borrowing-returning::chunk_4` | 0.7049 | Full | Đúng đối tượng undergraduate/postgraduate và đủ 4/4 evidence. |
| 1 | 2 | `rmit-borrowing-returning::chunk_1` | 0.7048 | None | Chỉ có heading chung về borrowing. |
| 1 | 3 | `rmit-borrowing-returning::chunk_6` | 0.6806 | Partial | Cùng số liệu nhưng dành cho academic staff, nên không phải gold chunk. |
| 2 | 1 | `rmit-borrowing-returning::chunk_8` | 0.7241 | Full | Đủ điều kiện và thời gian gia hạn. |
| 2 | 2 | `rmit-borrowing-returning::chunk_4` | 0.6850 | Full | Đủ điều kiện và thời gian gia hạn. |
| 2 | 3 | `rmit-borrowing-returning::chunk_7` | 0.6561 | Full | Đủ điều kiện và thời gian gia hạn. |
| 3 | 1 | `rmit-study-room-booking::chunk_0` | 0.7926 | None | Đúng chủ đề nhưng chỉ là giới thiệu. |
| 3 | 2 | `rmit-study-room-booking::chunk_4` | 0.7039 | None | Booking policy, không chứa quy trình đặt phòng. |
| 3 | 3 | `rmit-study-room-booking::chunk_2` | 0.7023 | Full | Chứa đủ đăng nhập, chọn campus/phòng/thời gian và xác nhận. |
| 4 | 1 | `rmit-accessibility-resources::chunk_0` | 0.6203 | Full | Đủ 3/3 evidence sau filter. |
| 4 | 2 | `rmit-study-faq::chunk_15` | 0.5865 | None | Nói về academic resources, không phải accessibility support. |
| 4 | 3 | `rmit-accessibility-resources::chunk_2` | 0.5315 | None | Nói chung về ELA nhưng không liệt kê ba hỗ trợ cần trả lời. |
| 5 | 1 | `rmit-borrowing-returning::chunk_17` | 0.7373 | None | Cùng chủ đề dispute/fine nhưng không chứa danh sách bị từ chối. |
| 5 | 2 | `rmit-borrowing-returning::chunk_18` | 0.6345 | Partial | Có hai evidence đầu nhưng phần cuối danh sách nằm ngoài top-3. |
| 5 | 3 | `rmit-library-rules::chunk_3` | 0.5794 | None | Quy tắc thư viện chung, không phải fine dispute. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5/5** có ít nhất một chunk liên quan; trong đó **4/5** có chunk chứa full evidence, còn query 5 chỉ có partial evidence.

### Phân tích A/B metadata filter — Query 4

Hai lượt dùng cùng query, corpus, embedder, strategy và `top_k=3`; biến duy nhất được thay đổi là có hoặc không có `metadata_filter={"audience": "student"}`.

| Lượt đo | Top-3 | Evidence coverage | Nhận xét |
|---------|-------|-------------------|----------|
| A — Không filter | `rmit-library-resources::chunk_4` (0.7168, `audience=all`); `rmit-library-resources::chunk_0` (0.7092, `audience=all`); `rmit-library-resources::chunk_10` (0.6826, `audience=all`) | **0/3** | Cả ba chunk giống chủ đề “library resources/support” nhưng không chứa ba hỗ trợ accessibility trong gold answer. |
| B — Có filter `audience=student` | `rmit-accessibility-resources::chunk_0` (0.6203); `rmit-study-faq::chunk_15` (0.5865); `rmit-accessibility-resources::chunk_2` (0.5315) | **3/3** | Gold chunk lên top-1 và agent trả lời đủ ba hỗ trợ. |

Filter đã thay đổi toàn bộ top-3 và cải thiện precision rõ rệt: từ không có evidence lên full evidence ở top-1. Điểm 0.6203 của gold chunk thấp hơn 0.7168 của chunk nhiễu khi không filter, cho thấy cosine score chỉ là tín hiệu xếp hạng trong tập ứng viên chứ không phải bằng chứng nội dung đúng. Filter loại các tài liệu `audience=all` và `faculty`, làm giảm recall theo thiết kế, nhưng trong query này không loại nhầm đáp án vì gold answer dành riêng cho `student`.

### Failure analysis — Query 5

**Query:** “Which reasons will the Library not accept when a user disputes a fine?”

**Bằng chứng từ top-3:**

- Top-1 `rmit-borrowing-returning::chunk_17`, score 0.7373: đúng chủ đề fine dispute nhưng chỉ hướng dẫn nói chuyện với service desk; không chứa lý do nào trong gold answer.
- Top-2 `rmit-borrowing-returning::chunk_18`, score 0.6345: chứa partial evidence gồm “Lack of knowledge of library polices” và “Forgetting the due date”, nhưng chưa có phần cuối danh sách.
- Top-3 `rmit-library-rules::chunk_3`, score 0.5794: quy tắc thư viện chung, không chứa evidence về tranh chấp tiền phạt.
- `rmit-borrowing-returning::chunk_19`, nằm ngoài top-3, mới chứa các lý do còn lại gồm “Not being on campus”, “Semester breaks, summer vacation” và “Changed opening hours”.

**Kết quả:** context top-3 chỉ đạt evidence coverage 2/3 theo các chuỗi đặc trưng. Agent extractive dùng top-1 nên trả lời rằng thư viện sẽ xem xét khiếu nại, thay vì liệt kê các lý do không được chấp nhận; vì vậy query này chỉ đạt **1/2 điểm**.

**Nguyên nhân:** `HeadingAwareChunker` giữ đúng heading nhưng section danh sách dài hơn 400 ký tự bị recursive fallback chia thành `chunk_18` và `chunk_19` mà không có overlap. Đồng thời, chunk giới thiệu `chunk_17` chứa trực tiếp các từ “disagree”, “library fine” nên có cosine score cao hơn chunk chứa câu trả lời. Đây là trường hợp đúng `doc_id` và đúng chủ đề nhưng sai section; score cao không đồng nghĩa với mật độ thông tin trả lời cao.

**Cải thiện đề xuất:** giữ một overlap nhỏ giữa các chunk con của cùng section hoặc cho phép giữ trọn section dạng danh sách; thử reranker ưu tiên chunk chứa cấu trúc liệt kê/chuỗi evidence; và để agent tổng hợp nhiều chunk liên quan thay vì chỉ trích top-1. Nếu tăng `top_k`, cần kiểm tra precision thay vì mặc định rằng nhiều context luôn tốt hơn.

### Nhận xét theo tiêu chí CP6

| Tiêu chí | Nhận xét từ kết quả cá nhân |
|----------|-----------------------------|
| Precision | Query 1, 2 và 4 có full evidence ở top-1; query 3 đúng ở top-3; query 5 chỉ có partial evidence ở top-2. |
| Chunk coherence | Heading giúp giữ tên section, nhưng recursive fallback không overlap làm danh sách ngoại lệ của query 5 bị tách đôi. |
| Metadata utility | Filter `audience=student` đổi evidence coverage query 4 từ 0/3 thành 3/3 và đưa gold chunk lên top-1. |
| Grounding | Agent đúng khi top-1 chứa full evidence (query 1, 2, 4), nhưng sai/thiếu khi top-1 chỉ cùng chủ đề (query 3, 5). |
| Failure case | Query 5 cho thấy cùng `doc_id` không đủ để kết luận retrieval đúng; phải kiểm nội dung chunk và evidence thực tế. |

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua phần demo và so sánh trong nhóm, tôi nhận ra không có chiến lược chunking nào tốt nhất cho mọi loại câu hỏi; cùng một corpus và embedder nhưng cách chia chunk khác nhau có thể làm gold chunk thay đổi thứ hạng. Tôi cũng học được rằng score cao chỉ phản ánh mức độ tương đồng chủ đề, không bảo đảm chunk chứa đáp án, nên cần kiểm tra evidence ở mức nội dung. Ngoài ra, metadata filter có thể cải thiện precision mạnh hơn việc chỉ tinh chỉnh kích thước chunk đối với các câu hỏi phụ thuộc đối tượng.

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | **5 / 5** |
| Hướng tiếp cận của tôi (My Approach) | **10 / 10** |
| Hoàn thiện code (Core Implementation — tests) | **30 / 30** — 42/42 tests passed |
| Dự đoán độ tương tự (Similarity Predictions) | **5 / 5** — đủ 5 cặp, điểm thực tế và phần phản ánh |
| Kết quả truy xuất của tôi (Competition Results) | **8 / 10** — theo rubric 5 benchmark queries |
| **Tổng phần cá nhân** | **58 / 60** |
