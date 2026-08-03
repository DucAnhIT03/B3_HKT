# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [VŨ ĐĂNG HUY]
**Nhóm:** [B3-HKT]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> _Viết 1-2 câu:_
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau trong không gian vector, biểu thị rằng hai câu có ý nghĩa ngữ nghĩa tương đồng mặc dù có thể khác nhau về cách diễn đạt.

**Ví dụ có độ tương tự CAO:**

- Câu A: Xe điện cần được kiểm tra tình trạng pin thường xuyên.
- Câu B:Cần theo dõi sức khỏe của pin xe điện để đảm bảo hiệu suất hoạt động.
- Tại sao tương đồng:Hai câu sử dụng các từ khác nhau nhưng đều đề cập đến việc kiểm tra, theo dõi tình trạng pin xe điện. Embedding model có thể hiểu được ý nghĩa chung của hai câu nên vector biểu diễn sẽ gần nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A:Xe điện cần được bảo dưỡng định kỳ.
- Câu B:Hôm nay thời tiết Hà Nội rất nóng.
- Tại sao khác:Hai câu thuộc hai chủ đề khác nhau. Một câu nói về bảo dưỡng phương tiện, câu còn lại nói về thời tiết nên vector embedding có hướng khác nhau và cosine similarity thấp.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> _Viết 1-2 câu:_
> Cosine similarity đo góc giữa hai vector thay vì khoảng cách tuyệt đối, vì vậy nó tập trung vào hướng biểu diễn ngữ nghĩa của văn bản. Với text embeddings, độ dài vector thường không quan trọng bằng sự tương đồng về ý nghĩa nên cosine similarity phù hợp hơn Euclidean distance.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> _Trình bày phép tính:_
> _Đáp án:_
> Số ký tự mỗi bước = chunk_size - overlap

= 500 - 50
= 450 ký tự

chunks = (document_size - chunk_size) / (chunk_size - overlap) + 1

= (10000 - 500) / 450 + 1

= 9500 / 450 + 1

≈ 21.11 + 1

≈ 22 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> _Viết 1-2 câu:_

Khi overlap tăng lên 100:

Bước dịch = 500 - 100 = 400

chunks = (10000 - 500) / 400 + 1

= 9500 / 400 + 1

≈ 23.75 + 1

≈ 25 chunks

Đáp án: Số lượng chunk tăng lên khoảng 25 chunks.

Overlap lớn hơn giúp giữ lại thông tin ở phần giao nhau giữa các chunk, tránh việc câu hoặc ý nghĩa quan trọng bị cắt giữa hai đoạn. Tuy nhiên overlap quá lớn sẽ làm tăng số lượng chunk, tăng chi phí lưu trữ và tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> _Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?_

Hàm SentenceChunker.chunk thực hiện chia tài liệu dựa trên ranh giới câu thay vì cắt theo số lượng ký tự cố định. Tôi sử dụng biểu thức chính quy (regex) để nhận diện các dấu kết thúc câu như dấu chấm (.), dấu hỏi (?) và dấu chấm than (!).

Sau khi tách câu, các câu được ghép lại thành từng chunk cho đến khi đạt giới hạn kích thước chunk_size. Với các trường hợp đặc biệt như câu quá dài, không có dấu kết thúc câu hoặc văn bản rỗng, chương trình xử lý bằng cách giữ nguyên nội dung hoặc bỏ qua phần không hợp lệ để tránh lỗi.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> _Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?_

RecursiveChunker sử dụng chiến lược chia nhỏ đệ quy (recursive splitting). Thuật toán ưu tiên chia văn bản theo các cấp độ từ lớn đến nhỏ như:

Paragraph (\n\n)
Sentence (.)
Word ( )
Character

Nếu đoạn văn hiện tại nhỏ hơn giới hạn chunk_size, thuật toán dừng lại (base case). Nếu vẫn quá dài, nó tiếp tục chia nhỏ bằng separator tiếp theo.

Cách tiếp cận này giúp giữ được cấu trúc ngữ nghĩa của văn bản tốt hơn so với việc cắt cứng theo số ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> _Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?_

Trong hàm add_documents, mỗi document được chia thành các chunk nhỏ trước khi đưa qua embedding model để chuyển đổi thành vector số. Các vector embedding cùng metadata như document ID, nội dung chunk, vị trí chunk được lưu trong vector store.

Khi thực hiện search, câu hỏi của người dùng cũng được chuyển thành embedding vector. Hệ thống tính cosine similarity giữa vector truy vấn và các vector đã lưu, sau đó sắp xếp kết quả theo độ tương đồng giảm dần và trả về top-k chunk phù hợp nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> _Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?_

Đối với search_with_filter, hệ thống thực hiện lọc metadata trước khi tính toán similarity. Ví dụ có thể lọc theo loại tài liệu, nguồn dữ liệu hoặc document ID để giảm số lượng vector cần tìm kiếm.

Sau khi lọc, hệ thống mới thực hiện cosine similarity để tìm các chunk phù hợp nhất.

Đối với delete_document, hệ thống tìm tất cả chunk thuộc document cần xóa dựa trên document ID, sau đó loại bỏ cả nội dung, metadata và vector embedding tương ứng khỏi vector store.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> _Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?_

Hàm answer triển khai mô hình Retrieval-Augmented Generation (RAG). Đầu tiên, câu hỏi người dùng được gửi tới EmbeddingStore để truy xuất các đoạn văn bản có liên quan nhất.

Các đoạn context này được đưa vào prompt cùng với câu hỏi ban đầu.

Cấu trúc prompt:

System:
Bạn là trợ lý AI.
Hãy trả lời dựa trên context được cung cấp.

Context:
{retrieved_documents}

Question:
{user_question}

Answer:

Agent không tự suy đoán kiến thức bên ngoài mà ưu tiên sử dụng thông tin được lấy từ knowledge base. Điều này giúp giảm hiện tượng hallucination và tăng độ chính xác của câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

(.venv) PS D:\vinuni\lab6\B3_HKT> python -m pytest tests -v
=========================================================== test session starts ===========================================================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0 -- D:\vinuni\lab6\B3_HKT\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\vinuni\lab6\B3_HKT
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [ 2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [ 4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [ 7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [ 9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

=========================================================== 42 passed in 0.17s ====

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán    | Điểm thực tế | Đúng? |
| --- | ----- | ----- | ---------- | ------------ | ----- |
| 1   |       |       | cao / thấp |              |       |
| 2   |       |       | cao / thấp |              |       |
| 3   |       |       | cao / thấp |              |       |
| 4   |       |       | cao / thấp |              |       |
| 5   |       |       | cao / thấp |              |       |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> _Viết 2-3 câu:_

| Cặp | Câu A                                                                     | Câu B                                                                                      | Dự đoán | Điểm thực tế | Đúng? |
| --- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------- | ------------ | ----- |
| 1   | Sinh viên được mượn tối đa 25 tài liệu trong thư viện.                    | Sinh viên có thể mượn tối đa 25 cuốn sách từ thư viện.                                     | Cao     | 0.82         | Có    |
| 2   | Tài liệu quá hạn hoặc đã được người khác đặt trước sẽ không được gia hạn. | Một tài liệu chỉ có thể tiếp tục mượn nếu không bị quá hạn và không có người khác yêu cầu. | Cao     | 0.76         | Có    |
| 3   | Sinh viên cần đăng nhập tài khoản RMIT để đặt phòng học nhóm.             | Hôm nay thời tiết Hà Nội có nhiệt độ rất cao.                                              | Thấp    | 0.15         | Có    |
| 4   | Thư viện hỗ trợ chuyển đổi tài liệu PDF sang dạng văn bản.                | Sinh viên đăng ký môn học qua hệ thống trực tuyến.                                         | Thấp    | 0.21         | Có    |
| 5   | Quên ngày trả sách không phải là lý do hợp lệ để hủy tiền phạt.           | Không nhận được email nhắc nhở cũng không được chấp nhận khi khiếu nại tiền phạt.          | Cao     | 0.68         | Có    |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Kết quả bất ngờ nhất là các câu có cách diễn đạt khác nhau nhưng vẫn có độ tương đồng cao do cùng biểu diễn một ý nghĩa chung. Điều này cho thấy embedding không chỉ dựa vào việc so sánh từ khóa mà còn cố gắng học mối quan hệ ngữ nghĩa giữa các câu. Tuy nhiên, chất lượng kết quả phụ thuộc nhiều vào embedding model được sử dụng.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| #   | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| --- | --------------- | ------------------------------------ | ---------- | ------------------------------ | ------------------------------- |
| 1   |                 |                                      |            |                                |                                 |
| 2   |                 |                                      |            |                                |                                 |
| 3   |                 |                                      |            |                                |                                 |
| 4   |                 |                                      |            |                                |                                 |
| 5   |                 |                                      |            |                                |                                 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** \_\_ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> _Viết 2-3 câu:_

| #   | Câu hỏi (Query)                                                                                                     | Top-1 Chunk truy xuất được (tóm tắt)                                                                  | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt)                                                                               |
| --- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| 1   | How many items can undergraduate and postgraduate students borrow, for how long, and how many renewals are allowed? | Chunk về Borrowing and returning, chứa thông tin loan quota 25 items, loan period 30 days, renewals 1 | 0.6698     | Có                             | Agent lấy context về quy định mượn sách và trả lời dựa trên thông tin quota, thời hạn mượn và số lần gia hạn. |
| 2   | Under what conditions can a borrowed item be renewed, and how long does the renewal last?                           | Chunk rmit-borrowing-returning chứa điều kiện renewal và thời gian gia hạn 15 ngày                    | 0.7348     | Có                             | Agent trả lời đúng điều kiện không quá hạn, không có người đặt trước và thời gian renewal tối đa 45 ngày.     |
| 3   | What steps are required to book a Library study room?                                                               | Chunk rmit-study-room-booking chứa hướng dẫn đặt phòng học                                            | 0.6682     | Có                             | Agent truy xuất đúng tài liệu hướng dẫn đặt phòng và lấy được các bước booking.                               |
| 4   | What support does the Library provide to make resources accessible?                                                 | Top-3 chứa chunk rmit-accessibility-resources về hỗ trợ sinh viên khuyết tật                          | 0.5622     | Có                             | Agent có context liên quan nhưng thứ hạng chưa cao nhất do một số chunk FAQ có nội dung gần nghĩa.            |
| 5   | Which reasons will the Library not accept when a user disputes a fine?                                              | Chunk rmit-borrowing-returning phần Disputes chứa danh sách lý do không được chấp nhận                | 0.7361     | Có                             | Agent truy xuất đúng quy định về tranh chấp tiền phạt và các trường hợp không được chấp nhận.                 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?**

**5 / 5**

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

Qua quá trình so sánh kết quả giữa các chiến lược chunking, tôi nhận thấy cách chia nhỏ tài liệu ảnh hưởng lớn đến chất lượng truy xuất. Embedding model tốt kết hợp với chunk có cấu trúc giúp hệ thống RAG tìm đúng thông tin và giảm câu trả lời sai.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------- |
| Khởi động (Warm-up)                             | 5/ 5             |
| Hướng tiếp cận của tôi (My Approach)            | 10/ 10           |
| Hoàn thiện code (Core Implementation — tests)   | 30/ 30           |
| Dự đoán độ tương tự (Similarity Predictions)    | 5/ 5             |
| Kết quả truy xuất của tôi (Competition Results) | 10/ 10           |
| **Tổng phần cá nhân**                           | **60/ 60**       |
