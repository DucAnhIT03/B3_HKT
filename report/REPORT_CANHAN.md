# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Chưa cung cấp]
**Nhóm:** [Chưa cung cấp]
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

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

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
