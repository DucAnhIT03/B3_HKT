# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đức Anh

**Mã sinh viên:** 2A202601063_

**Nhóm:** B3_HKT

**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có hướng gần nhau, nghĩa là hai đoạn văn được mô hình biểu diễn có nội dung hoặc ngữ nghĩa tương tự, dù chúng không nhất thiết dùng cùng từ ngữ.

Với hai vector `a` và `b`, tôi dùng công thức `cos(a,b) = (a·b) / (||a|| × ||b||)`. Giá trị gần `1` nghĩa là cùng hướng, gần `0` là gần trực giao và gần `-1` là ngược hướng. Nếu một vector có độ dài bằng `0`, implementation trả `0.0` để tránh chia cho 0.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên có thể gia hạn sách trực tuyến.
- Câu B: Người học được phép kéo dài thời hạn mượn tài liệu qua mạng.
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng cùng nói về việc sinh viên gia hạn tài liệu bằng hình thức trực tuyến.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên có thể gia hạn sách trực tuyến.
- Câu B: Dự báo ngày mai trời có mưa lớn.
- Tại sao khác: Một câu nói về dịch vụ thư viện, câu còn lại nói về thời tiết nên gần như không chia sẻ chủ đề hay ý định.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào hướng của vector, tức mẫu đặc trưng ngữ nghĩa, và ít bị ảnh hưởng bởi độ lớn vector. Khoảng cách Euclid còn thay đổi theo độ lớn nên hai vector cùng hướng nhưng khác độ dài có thể bị đánh giá là xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Bước dịch là `500 - 50 = 450`. Số chunk là `ceil((10.000 - 50) / (500 - 50)) = ceil(9.950 / 450) = ceil(22,11...)`.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Bước dịch giảm còn `500 - 100 = 400`, nên số chunk tăng thành `ceil((10.000 - 100) / 400) = ceil(24,75) = 25`. Overlap lớn giữ được nhiều ngữ cảnh hơn ở biên chunk nhưng làm tăng dữ liệu trùng lặp, số embedding, bộ nhớ và chi phí tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng đứng sau dấu `.`, `!` hoặc `?`, nhờ đó dấu kết câu được giữ ở câu phía trước. Text rỗng trả `[]`; mỗi câu được `strip()`, phần rỗng bị loại và các câu được ghép theo nhóm không vượt quá `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử separator theo thứ tự đoạn → dòng → câu → từ → ký tự, giữ lại separator khi chia rồi gộp các phần liền nhau cho đến giới hạn `chunk_size`. Base case là text đã đủ ngắn thì trả ngay; nếu hết separator hoặc gặp separator rỗng thì cắt fixed-size. Khi separator không xuất hiện hoặc một phần vẫn quá dài, lời gọi đệ quy luôn dùng phần danh sách separator còn lại để bảo đảm tiến tới điều kiện dừng.

**`HierarchicalSectionChunker` — chiến lược cá nhân cho K3:**
> Tôi parse toàn bộ cấp heading Markdown, không chỉ H2. Với mỗi heading, chunker
> giữ heading và semantic subtree đến sibling cùng/cao cấp tiếp theo. Subtree ngắn
> được giữ nguyên; parent quá rộng nhường cho các child subtree; chunk chỉ có
> heading bị loại; section quá dài mới fallback Recursive. Tôi chọn
> `chunk_size=1600`, rồi rerank bằng `0,5 × chunk cosine + 0,5 × max-sentence
> cosine`. Thiết kế này tách Q1 theo đúng audience, giữ trọn list Q5 và dùng
> sentence signal để đưa evidence accessibility của Q4 từ rank 3 lên rank 1.

### Độ tương tự và bộ so sánh chiến lược

**`compute_similarity`** — hướng tiếp cận:
> Tôi tách helper `_dot` để dùng chung. Hàm tính tích vô hướng và chuẩn Euclid của hai vector rồi áp dụng cosine similarity; nếu một trong hai chuẩn bằng `0`, hàm trả `0.0`. Cách này xử lý đúng vector giống nhau (`1`), đối nhau (`-1`), trực giao (`0`) và zero vector theo test.

**`ChunkingStrategyComparator.compare`** — hướng tiếp cận:
> Comparator chạy cùng một text qua `FixedSizeChunker`, `SentenceChunker` và `RecursiveChunker`, sau đó trả đúng ba key `fixed_size`, `by_sentences`, `recursive`. Với từng strategy, tôi lưu `count`, `avg_length` và danh sách `chunks`; text rỗng cho độ dài trung bình `0.0`, tránh phép chia cho 0. Tham số `chunk_size` được chuẩn hóa tối thiểu là 1 và overlap của fixed-size luôn nhỏ hơn chunk size.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi dùng store in-memory và đặt `self._use_chroma = False`. Helper `_make_record` chuẩn hóa mỗi `Document` thành record gồm ID duy nhất ghép từ `doc.id` và `_next_index`, content, **bản sao** metadata và embedding; `doc_id` luôn chỉ về file gốc thay vì chunk ID. `add_documents([])` không lỗi, còn mỗi document hợp lệ được append rồi mới tăng index. `search` gọi helper `_search_records`, tạo query embedding đúng một lần, tính dot product với từng record, copy metadata vào kết quả, sắp xếp score giảm dần rồi cắt `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc record trước theo điều kiện mọi cặp key/value metadata phải khớp, sau đó mới xếp hạng tập còn lại bằng helper dùng chung với `search`; khi filter là `None`, hàm gọi thẳng `search`. `delete_document` loại tất cả record có `metadata['doc_id']` bằng ID tài liệu gốc và trả `True` chỉ khi kích thước store thực sự giảm.

**Vì sao phải filter trước rồi mới rank?**
> Nếu lấy top-k toàn kho trước rồi mới bỏ record không khớp, cả k slot có thể thuộc sai audience và kết quả cuối bằng rỗng dù store vẫn có tài liệu hợp lệ. Pre-filter giữ toàn bộ candidate đúng metadata, sau đó embedding mới xếp hạng trong tập đó; đây là phép lọc metadata chính xác, không phải tìm keyword.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent lấy top-k chunk từ store, đánh số `[1]`, `[2]`, ... và gắn `doc_id` cùng `source_url`/đường dẫn nguồn trước nội dung từng chunk. Prompt yêu cầu chỉ dùng context, nói rõ khi thiếu thông tin và trích dẫn theo số; nếu store không trả kết quả, Agent trả thông báo trực tiếp mà không gọi LLM.

**Luồng dữ liệu hoàn chỉnh:** `file .md/.txt → parse front matter → Document → chunk Document có doc_id/chunk_index → embedding → EmbeddingStore → top-k/filter → context đánh số → llm_fn → câu trả lời có citation`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ python -m pytest tests -v
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1
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

============================= 42 passed in 0.15s ==============================
```

**Kết quả Checkpoint 3 (chunking, similarity, comparator):** 23 / 23 tests vượt qua.

**Số lượng bài test vượt qua (pass):** 42 / 42

**Kết luận:** toàn bộ interface bắt buộc của `src/chunking.py`, `src/store.py` và `src/agent.py` đều vượt qua test; không còn test đỏ hay test bị skip.

**Kiểm tra end-to-end:** `python main.py "What steps are required to book a
Library study room?"` nạp 119 chunk bằng local multilingual embedder, trả đúng
`rmit-study-room-booking` ở top-1 (score `0,816`) và agent trả đủ bốn bước với
citation `[1]`.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi ghi dự đoán trước khi đo theo nội dung ngữ nghĩa. Để chuyển điểm liên tục thành nhãn, tôi quy ước **cao khi score ≥ 0,50**, **thấp khi score < 0,50**. Điểm thực tế được tính bằng `LocalEmbedder(sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)` và chính hàm `compute_similarity()` trong bài; không dùng MockEmbedder.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Undergraduate and postgraduate students can borrow 25 items for 30 days. | Sinh viên đại học và sau đại học được mượn 25 tài liệu trong 30 ngày. | Cao | **0,883579** — cao | Có |
| 2 | Undergraduate and postgraduate students can borrow 25 items for 30 days. | Dự báo ngày mai trời có mưa lớn. | Thấp; dự đoán thấp nhất | **0,080691** — thấp nhất | Có |
| 3 | The Library provides text digitisation and converts PDF documents to text. | Thư viện số hóa văn bản và chuyển tài liệu PDF sang dạng văn bản. | Cao; dự đoán cao nhất | **0,857334** — cao | Có về nhãn; không phải cao nhất |
| 4 | Items can be renewed if they are not overdue. | Overdue items can be renewed. | Thấp vì điều kiện logic trái nhau | **0,896519** — cao nhất | **Không** |
| 5 | Undergraduate students may borrow 25 items. | Alumni may borrow 5 items. | Thấp vì khác audience và quota | **0,742701** — cao | **Không** |

**Dự đoán thứ hạng trước khi chạy:** cặp 3 cao nhất vì là paraphrase xuyên ngôn
ngữ gần như đầy đủ; cặp 2 thấp nhất vì khác hoàn toàn chủ đề. **Kết quả:** cặp 4
cao nhất, cặp 2 thấp nhất. Tôi dự đoán đúng cực tiểu nhưng sai cực đại.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 bất ngờ nhất: “not overdue” và “overdue” đảo ngược điều kiện được gia
> hạn nhưng score vẫn cao nhất (`0,896519`) vì hai câu chia sẻ gần như toàn bộ từ
> khóa và cấu trúc. Cặp 5 cũng cao (`0,742701`) dù audience/quota khác nhau. Điều
> này cho thấy embedding cosine chủ yếu đo gần nhau về **chủ đề/biểu diễn phân
> bố**, không tự bảo đảm phủ định, ràng buộc đối tượng hay tính đúng của đáp án;
> retrieval phải kiểm tra content, heading và grounding, không xem score cao là
> bằng chứng đủ.

**Lệnh tái lập:**

```bash
python scripts/measure_similarity.py
```

Output: `0.883579, 0.080691, 0.857334, 0.896519, 0.742701` theo thứ tự cặp 1→5.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Cấu hình:** corpus 9 trang RMIT tại `data/rmit-library`;
`LocalEmbedder(sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)`,
vector 384 chiều normalized; `HierarchicalSectionChunker(chunk_size=1600)`;
`top_k=3`. Reranker dùng `0,5 × chunk cosine + 0,5 × max-sentence cosine`.
Agent extractive trả nguyên top-1 với citation `[1]`, nên chỉ được 2 điểm khi một
chunk rank-1 thực sự đủ evidence; không thể che lỗi bằng cách ghép gold answer.
Tổng cộng **119 chunk**, độ dài trung bình **427,26** ký tự.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Quota/thời hạn/gia hạn của undergraduate và postgraduate | `rmit-borrowing-returning#3` | **0,621724** | Có, đủ 4 marker rank 1; không chứa quota English = 10 | `[1]` nêu đúng 25 items, 30 days, 1 renewal. |
| 2 | Điều kiện và thời gian renewal | `rmit-borrowing-returning#7` | **0,710490** | Có, đủ 4 marker rank 1 | `[1]` nêu not overdue/not reserved, 15 days, maximum 45 days. |
| 3 | Các bước đặt study room | `rmit-study-room-booking#3` | **0,816358** | Có, đủ 4 marker rank 1 | `[1]` nêu log in, choose campus, select room/time, confirm. |
| 4 | Hỗ trợ accessibility (`audience=student`) | `rmit-accessibility-resources#0` | **0,610174** | Có, đủ 3 marker rank 1 | `[1]` nêu text digitisation, digital resources và PDF-to-text. |
| 5 | Các lý do không chấp nhận khi dispute fine | `rmit-borrowing-returning#15` | **0,774576** | Có, đủ 10/10 marker rank 1 | `[1]` giữ nguyên heading và toàn bộ 10 lý do. |

**Bao nhiêu câu hỏi trả về chunk có đầy đủ evidence trong top-3?** 5 / 5

**Điểm retrieval theo rubric:** **10 / 10** (`2 + 2 + 2 + 2 + 2`).

### Bằng chứng top-3 ở mức chunk

| Query | Rank | Chunk | Score | Đánh giá evidence |
|-------|------|-------|-------|-------------------|
| Q1 | 1 | `rmit-borrowing-returning#3` | 0,621724 | Đủ heading + 25/30/1; đúng audience, không có quota 10. |
| Q1 | 2 | `rmit-borrowing-returning#5` | 0,609576 | Nhiễu Academic staff; có 25/30/1 nhưng sai đối tượng. |
| Q1 | 3 | `rmit-borrowing-returning#1` | 0,587938 | Đúng document nhưng trộn English và undergraduate; không dùng làm answer. |
| Q2 | 1 | `rmit-borrowing-returning#7` | 0,710490 | Đủ điều kiện và 15/45 ngày. |
| Q2 | 2 | `rmit-borrowing-returning#3` | 0,693873 | Đủ evidence; section undergraduate/postgraduate. |
| Q2 | 3 | `rmit-borrowing-returning#6` | 0,679440 | Đủ evidence nhưng thuộc professional staff; query không giới hạn audience. |
| Q3 | 1 | `rmit-study-room-booking#3` | 0,816358 | Đủ bốn bước trong một câu. |
| Q3 | 2 | `rmit-study-room-booking#2` | 0,802272 | Đủ evidence, thêm heading cha. |
| Q3 | 3 | `rmit-study-room-booking#0` | 0,786828 | Đủ evidence nhưng chunk rộng hơn. |
| Q4 | 1 | `rmit-accessibility-resources#0` | 0,610174 | Đủ cả ba dịch vụ sau filter. |
| Q4 | 2 | `rmit-study-faq#7` | 0,602153 | Nhiễu FAQ về academic resources, không có marker. |
| Q4 | 3 | `rmit-study-faq#31` | 0,593163 | Nhiễu FAQ Euromonitor, không có marker. |
| Q5 | 1 | `rmit-borrowing-returning#15` | 0,774576 | Đủ 10/10 lý do trong một subtree. |
| Q5 | 2 | `rmit-borrowing-returning#14` | 0,773022 | Đủ 10/10, gồm heading Disputes. |
| Q5 | 3 | `rmit-borrowing-returning#16` | 0,697623 | Đủ 10/10, section con “We will not accept…”. |

### A/B metadata filter — Query 4

- **Có filter `{"audience": "student"}`:** evidence accessibility ở rank 1,
  score 0,610174; agent đúng; **2/2**.
- **Không filter:** top-3 lần lượt là `rmit-library-resources#4` (0,737371),
  `rmit-library-resources#0` (0,717897) và `rmit-develop-course-content#2`
  (0,689225); không chunk nào có marker; agent sai; **0/2**.
- **Kết luận:** hai kết quả khác hoàn toàn. Filter loại đúng tài liệu `all/faculty`
  đang chiếm top-k rồi mới rank trong tập student, nên tăng precision mà không
  làm mất gold document.

### Failure case

**Failure trước khi tinh chỉnh — Q4, Hierarchical không rerank.** Gold chunk
`rmit-accessibility-resources#0` chỉ đứng rank 3 với base score 0,530871; hai FAQ
cùng chủ đề đứng trên. Agent extractive trả top-1 không chứa “Text digitisation”,
“Helping to obtain digital resources”, “Converting documents from PDF to text”,
nên Q4 chỉ được 1/2 và tổng là 9/10.

**Nguyên nhân:** cosine toàn chunk đo gần chủ đề, không đo mật độ bằng chứng. Gold
chunk còn chứa wheelchair và ELA, làm vector tổng hợp bị pha loãng; FAQ lại có
nhiều từ “resources/library”. Tôi giữ nguyên corpus/query/filter/top-k và thêm
sentence rerank. Sau sửa, max-sentence signal 0,689478 đưa gold lên rank 1, score
kết hợp 0,610174; agent đủ ba marker và tổng tăng **9/10 → 10/10**.

**Failure đối chứng — Q5 với Recursive 300:** raw reproduction tạo 170 chunk,
top-1 chỉ có 3/10 marker; phần danh sách còn lại xuất hiện ở rank 2. Evidence có
trong top-3 nhưng agent top-1 thiếu ý, nên strict rubric chỉ cho 1/2. Hierarchical
giữ cả list trong chunk rank-1 và lấy lại 2/2.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Recursive 300 của Phan Văn Hiếu cho evidence hit rất mạnh nhưng Q1/Q5 cho thấy
> đúng `doc_id` hoặc đủ marker đâu đó trong top-3 chưa bảo đảm top-1 sạch và agent
> đủ ý. HeadingAware của Nguyễn Huy Tòa gợi ý giữ structure, còn overlap của Vũ
> Đăng Huy nhắc về biên chunk. Tôi kết hợp hierarchy với rerank và chấm strict ở
> mức chunk + agent, thay vì quy mọi failure thành “model sai”.

### Khả năng tái lập kết quả cá nhân

```bash
pip install -r requirements.txt
pip install -r requirements-local.txt
python -m pytest tests -v
python scripts/measure_similarity.py
python scripts/fetch_rmit_corpus.py
python scripts/run_rmit_benchmark.py --provider local
```

Các bằng chứng máy đọc được nằm tại
`report/benchmark_rmit_nguyen_duc_anh.json`; bảng top-3 phía trên được lấy trực
tiếp từ file này. Giao diện kiểm chứng thủ công chạy bằng
`python -m streamlit run streamlit_app.py`, cho phép đổi strategy, top-k và
metadata filter rồi xem content/score/source của từng chunk.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Bằng chứng trong báo cáo | Điểm tự đánh giá |
|----------|--------------------------|-------------------|
| Khởi động (Warm-up) | Giải thích cosine, ví dụ cao/thấp, so sánh Euclid, tính đúng 23 và 25 chunks | **5 / 5** |
| Hướng tiếp cận của tôi (My Approach) | Giải thích toàn bộ chunker, similarity, comparator, 5 thao tác store, helper và agent | **10 / 10** |
| Hoàn thiện code (Core Implementation — tests) | Output `python -m pytest tests -v`: **42 passed, 0 failed, 0 skipped** | **30 / 30** |
| Dự đoán độ tương tự (Similarity Predictions) | Đủ 5 cặp, dự đoán trước đo, score thực tế, cực đại/cực tiểu và reflection | **5 / 5** |
| Kết quả truy xuất của tôi (Competition Results) | Đủ 5 query chung, top-3 chunk/score, agent answer, A/B filter, grounding và failure có bằng chứng | **10 / 10** |
| **Tổng phần cá nhân** | Hoàn thành đủ mọi trường bắt buộc trong form và có lệnh tái lập | **60 / 60** |

> Chiến lược cuối đạt `10/10` trên đúng 5 query RMIT đã đóng băng. Báo cáo giữ
> ablation 9/10 trước rerank, failure Q4 và đối chứng Recursive Q5; raw score
> trước/sau nằm trong `report/benchmark_rmit_nguyen_duc_anh.json`, không thay
> query, filter hay gold marker sau khi chạy.
