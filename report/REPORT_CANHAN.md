# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Tạ Long Khánh  
**Nhóm:** B3-HKT 
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine cao cho thấy hai vector embedding có hướng gần giống nhau, tức là hai đoạn văn bản có nội dung hoặc ý nghĩa tương đồng. Trong bài toán NLP, hai câu có thể dùng từ khác nhau nhưng vẫn có cosine similarity cao nếu cùng diễn đạt một ý.

**Ví dụ có độ tương tự CAO:**

- **Câu A:** Sinh viên có thể gia hạn thời gian mượn sách.
- **Câu B:** Người học được phép kéo dài thời hạn mượn tài liệu thư viện.
- **Tại sao tương đồng:** Hai câu diễn đạt cùng một quy định nhưng sử dụng từ ngữ khác nhau.

**Ví dụ có độ tương tự THẤP:**

- **Câu A:** Sinh viên có thể gia hạn thời gian mượn sách.
- **Câu B:** Hôm nay trời có mưa lớn ở Hà Nội.
- **Tại sao khác:** Hai câu thuộc hai chủ đề hoàn toàn khác nhau nên embedding sẽ có hướng khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity chỉ quan tâm đến hướng của vector thay vì độ lớn của vector. Điều này phù hợp với text embedding vì hai câu cùng ý nghĩa có thể tạo ra vector có độ lớn khác nhau nhưng vẫn cùng hướng.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> **Phép tính:**

```
ceil((10000 - 50) / (500 - 50))
= ceil(9950 / 450)
= ceil(22.11)
= 23
```

> **Đáp án:** 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Khi overlap tăng lên 100 thì số lượng chunk tăng lên do khoảng dịch giữa hai chunk giảm xuống. Overlap lớn giúp giữ được nhiều ngữ cảnh hơn giữa các chunk liên tiếp nhưng làm tăng số lượng embedding và chi phí lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

#### `SentenceChunker.chunk` — hướng tiếp cận

> Tôi sử dụng Regular Expression để tách văn bản tại các dấu kết thúc câu như `.`, `!`, `?`, sau đó loại bỏ khoảng trắng và các chuỗi rỗng bằng `strip()`. Các câu được gom lại theo số lượng tối đa `max_sentences_per_chunk`, giúp mỗi chunk giữ được ngữ nghĩa hoàn chỉnh thay vì cắt giữa câu.

#### `RecursiveChunker.chunk` / `_split` — hướng tiếp cận

> RecursiveChunker ưu tiên chia theo các ranh giới tự nhiên như đoạn văn, dòng, câu, từ và cuối cùng mới cắt theo ký tự. Base case của thuật toán là khi văn bản nhỏ hơn `chunk_size` hoặc không còn separator để chia thì trả về kết quả ngay, tránh đệ quy vô hạn.

### Lớp EmbeddingStore

#### `add_documents` + `search` — hướng tiếp cận

> Mỗi `Document` được chuyển thành một record gồm `id`, `content`, `metadata` và `embedding`. Khi tìm kiếm, embedding của câu truy vấn chỉ được tạo một lần, sau đó tính dot product với embedding của từng record, sắp xếp theo score giảm dần và trả về top-k kết quả.

#### `search_with_filter` + `delete_document` — hướng tiếp cận

> Tôi thực hiện lọc metadata trước rồi mới tính độ tương tự để chỉ xếp hạng các tài liệu đúng điều kiện. Hàm `delete_document` sẽ xóa tất cả record có cùng `doc_id`, đồng thời trả về `True` nếu có dữ liệu được xóa và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

#### `answer` — hướng tiếp cận

> Agent sử dụng `EmbeddingStore.search()` để lấy top-k chunk liên quan nhất, ghép chúng thành phần Context rồi đưa vào prompt cùng với câu hỏi. Prompt yêu cầu mô hình chỉ trả lời dựa trên Context đã truy xuất nhằm giảm hiện tượng hallucination và tăng khả năng truy vết nguồn.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
E:\VinUni\lab7\B3_HKT [2A202601197-TaLongKhanh +0 ~3 -0 !]> pytest tests/ -v
======================================================== test session starts =========================================================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- E:\VinUni\lab7\B3_HKT\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\VinUni\lab7\B3_HKT
collected 42 items                                                                                                                    

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                           [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                    [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                             [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                              [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                   [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                   [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                         [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                          [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                        [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                          [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                          [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                     [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                 [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                           [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                  [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                      [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                      [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                          [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                            [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                              [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                    [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                         [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                           [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                               [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                            [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                     [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                    [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                               [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                           [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                      [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                          [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                          [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                       [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                     [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                    [ 88%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                            [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                  [ 97%]

========================================================= 42 passed in 0.15s =========================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên được gia hạn sách. | Người học được kéo dài thời gian mượn tài liệu. | Cao | | |
| 2 | Thư viện mở cửa từ 8 giờ sáng. | Phòng đọc bắt đầu phục vụ lúc 8 giờ. | Cao | | |
| 3 | Sinh viên phải đóng học phí đúng hạn. | Người học cần thanh toán học phí trước thời hạn. | Cao | | |
| 4 | Sinh viên được đăng ký tối đa 24 tín chỉ. | Hôm nay trời nhiều mây. | Thấp | | |
| 5 | Giảng viên được mượn tài liệu trong 30 ngày. | Đội tuyển bóng đá Việt Nam thi đấu tối nay. | Thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Embedding không chỉ dựa trên các từ giống nhau mà còn học được ngữ nghĩa của câu. Vì vậy hai câu có cách diễn đạt khác nhau vẫn có thể có độ tương đồng cao nếu cùng truyền tải một ý.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-----------------|---------------------------------------|------------|---------------------|----------------------------------|
| 1 | How many items can undergraduate and postgraduate students borrow, for how long, and how many renewals are allowed? | Chunk chứa quy định Undergraduate & Postgraduate students: 25 items, 30 days, 1 renewal. | 0.6522 | Có | Agent trả lời sinh viên được mượn 25 tài liệu trong 30 ngày và được gia hạn 1 lần. |
| 2 | Under what conditions can a borrowed item be renewed, and how long does the renewal last? | Chunk chứa điều kiện gia hạn: tài liệu không quá hạn, không bị người khác đặt trước và thời gian gia hạn. | 0.7358 | Có | Agent trả lời đúng điều kiện gia hạn và thời hạn gia hạn dựa trên context. |
| 3 | What steps are required to book a Library study room? | Chunk mô tả quy trình đặt phòng học: đăng nhập, chọn campus, chọn phòng và xác nhận. | 0.6691 | Có | Agent mô tả đầy đủ các bước đặt phòng học của thư viện. |
| 4 | What support does the Library provide to make resources accessible? | Chunk về Accessibility Resources: số hóa tài liệu, hỗ trợ tài nguyên số, chuyển PDF sang văn bản. | 0.5467 | Có | Agent trả lời các dịch vụ hỗ trợ tiếp cận tài nguyên dành cho sinh viên. |
| 5 | Which reasons will the Library not accept when a user disputes a fine? | Chunk liệt kê các lý do thư viện không chấp nhận khi khiếu nại tiền phạt. | 0.7507 | Có | Agent trả lời các trường hợp thư viện từ chối khiếu nại theo đúng quy định. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Qua quá trình so sánh, tôi nhận thấy không có một chiến lược chunking phù hợp cho mọi loại dữ liệu. Việc lựa chọn kích thước chunk, overlap và metadata phù hợp với từng domain có ảnh hưởng rất lớn đến chất lượng retrieval của hệ thống RAG.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) |  / 10 |
| **Tổng phần cá nhân** | ** 60 / 60** |