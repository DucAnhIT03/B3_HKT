# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đức Anh
**Nhóm:** B3_HKT
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có hướng gần nhau, nghĩa là hai đoạn văn được mô hình biểu diễn có nội dung hoặc ngữ nghĩa tương tự, dù chúng không nhất thiết dùng cùng từ ngữ.

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

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi dùng store in-memory; mỗi `Document` được chuẩn hóa thành record gồm ID lưu trữ duy nhất, content, bản sao metadata và embedding. `search` tạo query embedding đúng một lần, tính dot product với embedding của từng record, sắp xếp score giảm dần rồi trả tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc record trước theo điều kiện mọi cặp key/value metadata phải khớp, sau đó mới xếp hạng tập còn lại bằng helper dùng chung với `search`; khi filter là `None`, hàm gọi thẳng `search`. `delete_document` loại tất cả record có `metadata['doc_id']` bằng ID tài liệu gốc và trả `True` chỉ khi kích thước store thực sự giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent lấy top-k chunk từ store, đánh số `[1]`, `[2]`, ... và gắn `doc_id` cùng `source_url`/đường dẫn nguồn trước nội dung từng chunk. Prompt yêu cầu chỉ dùng context, nói rõ khi thiếu thông tin và trích dẫn theo số; nếu store không trả kết quả, Agent trả thông báo trực tiếp mà không gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# python -m pytest tests -v
# ============================= 42 passed in 0.10s =============================
```

**Kết quả Checkpoint 3 (chunking, similarity, comparator):** 23 / 23 tests vượt qua.

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Cấu hình:** `LocalEmbedder(sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)`, vector 384 chiều đã normalize; `RecursiveChunker(chunk_size=500)`; `top_k=3`. Agent benchmark dùng `KnowledgeBaseAgent` với `llm_fn` extractive: xếp hạng câu trong context bằng cùng embedding rồi trả bốn câu tốt nhất kèm citation. Chấm evidence bằng marker cố định trong nội dung chunk, không chấm chỉ theo `doc_id`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Hỗ trợ của First-Year Librarians | `librarians-first-year-students#0`: giới thiệu đầu mối và các hỗ trợ | 0,764 | Có, marker ở rank 1 | Chỉ nêu đầu mối/Library Liaison, bỏ câu “guidance, consultations and referrals”; chưa đủ. |
| 2 | Giới hạn Libby | `libby-harvard#1`: 3 sách, 14 ngày, 5 holds | 0,710 | Có | Trả đúng cả ba giới hạn, dẫn `[1]`. |
| 3 | Tự động gia hạn | `borrow-renew-return#2`: tối đa 5 lần nếu không ai yêu cầu | 0,601 | Có | Trả đúng điều kiện và số lần, dẫn `[1]`. |
| 4 | Đặt buổi hướng dẫn | `teach-with-library#3`: yêu cầu gửi sớm | 0,683 | Có nhưng chỉ chứa một nửa; cách đặt ở rank 2 | Agent ghép rank 1+2 và trả đúng: liên hệ liaison/gửi request, gửi sớm. |
| 5 | BorrowDirect: loại tài liệu + thời hạn | `borrowdirect#1`: 16 tuần, không gia hạn | 0,745 | Liên quan một phần, thiếu loại tài liệu | Trả đúng thời hạn nhưng thiếu “printed books and music scores”, đồng thời lấy nhiễu từ Libby và policy mượn chung. |

**Bao nhiêu câu hỏi trả về chunk có đầy đủ evidence trong top-3?** 4 / 5

**Điểm retrieval theo rubric:** 6 / 10 (`1 + 2 + 2 + 1 + 0`).

### Bằng chứng top-3 ở mức chunk

| Query | Rank | Chunk | Score | Đánh giá evidence |
|-------|------|-------|-------|-------------------|
| Q1 | 1 | `librarians-first-year-students#0` | 0,764 | Có marker hỗ trợ; agent không chọn câu marker. |
| Q1 | 2 | `librarians-first-year-students#1` | 0,578 | Cùng tài liệu, hỗ trợ liaison/consultation nhưng không có marker chính. |
| Q1 | 3 | — | — | Filter `student` chỉ còn hai chunk. |
| Q2 | 1 | `libby-harvard#1` | 0,710 | Có đủ marker 3 sách và 5 holds; cùng chunk có 14 ngày. |
| Q2 | 2 | `libby-harvard#0` | 0,507 | Đúng chủ đề Libby nhưng không có giới hạn. |
| Q2 | 3 | `borrow-renew-return#0` | 0,467 | Nhiễu từ chính sách mượn vật lý. |
| Q3 | 1 | `borrow-renew-return#2` | 0,601 | Có đầy đủ marker tự động gia hạn 5 lần và điều kiện. |
| Q3 | 2 | `borrowdirect#1` | 0,581 | Nhiễu gần chủ đề: 16 tuần, không gia hạn. |
| Q3 | 3 | `libby-harvard#1` | 0,514 | Nhiễu từ thời hạn mượn số. |
| Q4 | 1 | `teach-with-library#3` | 0,683 | Có marker “gửi sớm”. |
| Q4 | 2 | `teach-with-library#0` | 0,663 | Có marker liên hệ liaison/gửi request. |
| Q4 | 3 | `teach-with-library#2` | 0,619 | Cùng dịch vụ giảng dạy, không có hai điều kiện gold. |
| Q5 | 1 | `borrowdirect#1` | 0,745 | Chỉ có thời hạn 16 tuần/không gia hạn. |
| Q5 | 2 | `libby-harvard#1` | 0,671 | Nhiễu vì cũng chứa thời hạn và giới hạn mượn. |
| Q5 | 3 | `borrow-renew-return#2` | 0,641 | Nhiễu vì cũng nói về thời hạn/gia hạn. |

### A/B metadata filter

- **Q1 (`student`):** filtered trả hai chunk First-Year; unfiltered giữ nguyên hai rank đầu và thêm `teach-with-library#2` ở rank 3. Điểm vẫn 1/2 và agent vẫn bỏ marker, nên filter chỉ giảm nhiễu chứ không sửa failure của bước chọn câu.
- **Q4 (`faculty`):** filtered trả `teach#3`, `teach#0`, `teach#2` và agent có đủ hai marker. Unfiltered thay rank 3 bằng `librarians-first-year-students#0`; evidence vẫn có ở rank 1+2 nhưng agent extractive chọn nhiễu và bỏ marker “gửi sớm”. Filter cải thiện grounding dù điểm rank-based vẫn là 1/2.

### Failure case

**Q5 là failure rõ nhất.** `borrowdirect#1` đứng top-1 (0,745) nên nếu chỉ kiểm `doc_id` sẽ bị chấm đậu, nhưng chunk này chỉ trả lời thời hạn/gia hạn. Chunk `borrowdirect#2` chứa loại tài liệu “printed books and music scores” đứng tận rank 10 (0,307), ngoài context; agent vì thế không thể trả lời đủ.

Nguyên nhân là hai phần của câu hỏi nằm ở hai section và cosine ưu tiên từ vựng về thời hạn/gia hạn, đồng thời bị nhiễu bởi hai policy mượn khác có số liệu tương tự. Tôi đề xuất prepend tiêu đề section vào chunk, lấy thêm chunk lân cận cùng `doc_id`, hoặc rerank theo coverage của cả ba ý “loại tài liệu + thời hạn + gia hạn”; chỉ tăng `top_k` sẽ tăng recall nhưng cũng tăng nhiễu.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> So sánh ba strategy cho thấy score cao và đúng `doc_id` chưa đủ: Q5 có đúng tài liệu ở top-1 nhưng thiếu section trả lời loại tài liệu. Marker ở mức chunk và A/B filter giúp tách failure do retrieval, chunking và bước tạo câu trả lời thay vì quy chung là “model sai”.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
