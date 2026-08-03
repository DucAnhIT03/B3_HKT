from __future__ import annotations

import csv
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Callable

import pandas as pd
import streamlit as st

from ingest import build_knowledge_base, load_documents
from src.agent import KnowledgeBaseAgent
from src.chunking import (
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
    _dot,
)
from src.embeddings import LOCAL_EMBEDDING_MODEL, LocalEmbedder, _mock_embed


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "k3_university"
SOURCES_PATH = DATA_DIR / "sources.csv"
BENCHMARK_PATH = ROOT / "report" / "benchmark_results.json"

STRATEGY_LABELS = {
    "fixed_size": "Fixed-size",
    "by_sentences": "Theo câu",
    "recursive": "Recursive",
}
PROVIDER_LABELS = {
    "local": "Local multilingual",
    "mock": "Mock deterministic",
}
EXAMPLE_QUESTIONS = [
    "Sinh viên năm nhất nhận được những hỗ trợ nào từ First-Year Librarians?",
    "Tôi được mượn tối đa bao nhiêu sách trên Libby và trong bao lâu?",
    "Tài liệu mượn thông thường được tự động gia hạn tối đa bao nhiêu lần?",
    "Giảng viên đặt một buổi hướng dẫn thư viện cho lớp bằng cách nào?",
    "BorrowDirect cho mượn tài liệu gì và có được gia hạn không?",
]


st.set_page_config(
    page_title="K3 RAG Library",
    page_icon=":material/local_library:",
    layout="wide",
)


class RetrievedResultStore:
    """Store adapter that lets KnowledgeBaseAgent answer from an exact result set."""

    def __init__(self, results: list[dict]) -> None:
        self.results = results

    def search(self, _question: str, top_k: int = 3) -> list[dict]:
        return self.results[:top_k]


def _default_settings() -> dict:
    default_provider = os.getenv("RAG_UI_DEFAULT_PROVIDER", "local").strip().lower()
    if default_provider not in PROVIDER_LABELS:
        default_provider = "local"
    return {
        "provider": default_provider,
        "strategy": "recursive",
        "chunk_size": 500,
        "overlap": 50,
        "max_sentences": 3,
        "top_k": 3,
    }


def _init_state() -> None:
    st.session_state.setdefault("settings", _default_settings())
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("pending_question", None)


@st.cache_data
def load_corpus_documents():
    return load_documents(DATA_DIR)


@st.cache_data
def load_source_registry() -> list[dict[str, str]]:
    with SOURCES_PATH.open(encoding="utf-8", newline="") as source_file:
        return list(csv.DictReader(source_file))


@st.cache_data
def load_benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def _make_cached_embedder(provider: str) -> tuple[Callable[[str], list[float]], str, str | None]:
    warning = None
    if provider == "local":
        try:
            backend = LocalEmbedder(LOCAL_EMBEDDING_MODEL)
        except Exception as exc:
            backend = _mock_embed
            warning = f"Không tải được model local ({exc}). Hệ thống đã chuyển sang Mock."
    else:
        backend = _mock_embed

    @lru_cache(maxsize=4096)
    def cached(text: str) -> tuple[float, ...]:
        return tuple(float(value) for value in backend(text))

    def embed(text: str) -> list[float]:
        return list(cached(text))

    backend_name = getattr(backend, "_backend_name", backend.__class__.__name__)
    return embed, backend_name, warning


def _make_chunker(settings: dict):
    if settings["strategy"] == "by_sentences":
        return SentenceChunker(max_sentences_per_chunk=settings["max_sentences"])
    if settings["strategy"] == "recursive":
        return RecursiveChunker(chunk_size=settings["chunk_size"])
    safe_overlap = min(settings["overlap"], settings["chunk_size"] - 1)
    return FixedSizeChunker(chunk_size=settings["chunk_size"], overlap=safe_overlap)


@st.cache_resource(max_entries=12, show_spinner=False)
def build_resources(
    provider: str,
    strategy: str,
    chunk_size: int,
    overlap: int,
    max_sentences: int,
):
    settings = {
        "provider": provider,
        "strategy": strategy,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "max_sentences": max_sentences,
    }
    embedder, backend_name, warning = _make_cached_embedder(provider)
    store = build_knowledge_base(
        DATA_DIR,
        embedding_fn=embedder,
        chunker=_make_chunker(settings),
        collection_name=f"ui_{strategy}_{chunk_size}_{overlap}_{max_sentences}",
    )
    return store, embedder, backend_name, warning


def make_extractive_llm(embedding_fn: Callable[[str], list[float]]) -> Callable[[str], str]:
    """Create a deterministic grounded answerer for the no-API-key demo."""

    def answer(prompt: str) -> str:
        context_match = re.search(r"Context:\n(.*?)\n\nQuestion:", prompt, re.S)
        question_match = re.search(r"Question:\s*(.*?)\nAnswer:", prompt, re.S)
        if not context_match or not question_match:
            return "Không đủ thông tin trong ngữ cảnh được truy xuất."

        question = question_match.group(1).strip()
        candidates: list[tuple[str, str]] = []
        blocks = re.split(r"(?m)(?=^\[\d+\])", context_match.group(1))
        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) < 2 or not lines[0].startswith("["):
                continue
            citation = lines[0].split("]", 1)[0] + "]"
            sentences = re.split(r"(?<=[.!?])\s+|\n+", "\n".join(lines[1:]))
            candidates.extend(
                (citation, sentence.strip())
                for sentence in sentences
                if len(sentence.strip()) >= 20
            )

        if not candidates:
            return "Không đủ thông tin trong ngữ cảnh được truy xuất."

        query_vector = embedding_fn(question)
        ranked = sorted(
            candidates,
            key=lambda item: _dot(query_vector, embedding_fn(item[1])),
            reverse=True,
        )
        selected: list[str] = []
        seen: set[str] = set()
        for citation, sentence in ranked:
            normalized = sentence.casefold()
            if normalized in seen:
                continue
            selected.append(f"{citation} {sentence}")
            seen.add(normalized)
            if len(selected) == 4:
                break
        return " ".join(selected)

    return answer


def _metadata_options(documents, key: str) -> list[str]:
    return sorted(
        {
            str(document.metadata[key])
            for document in documents
            if document.metadata.get(key) not in (None, "")
        }
    )


def render_sidebar(documents) -> tuple[dict, dict]:
    settings = st.session_state.settings
    with st.sidebar:
        st.subheader(":material/tune: Cấu hình pipeline")
        with st.form("pipeline_settings"):
            provider = st.selectbox(
                "Embedding",
                options=list(PROVIDER_LABELS),
                index=list(PROVIDER_LABELS).index(settings["provider"]),
                format_func=PROVIDER_LABELS.get,
            )
            strategy = st.selectbox(
                "Chiến lược chunking",
                options=list(STRATEGY_LABELS),
                index=list(STRATEGY_LABELS).index(settings["strategy"]),
                format_func=STRATEGY_LABELS.get,
            )
            chunk_size = st.slider(
                "Kích thước chunk",
                min_value=150,
                max_value=900,
                value=settings["chunk_size"],
                step=50,
            )
            overlap = st.slider(
                "Overlap (fixed-size)",
                min_value=0,
                max_value=200,
                value=settings["overlap"],
                step=10,
            )
            max_sentences = st.slider(
                "Số câu mỗi chunk",
                min_value=1,
                max_value=8,
                value=settings["max_sentences"],
            )
            top_k = st.slider("Số kết quả top-k", 1, 5, settings["top_k"])
            apply_settings = st.form_submit_button(
                "Áp dụng cấu hình",
                icon=":material/check:",
                type="primary",
                width="stretch",
            )

        if apply_settings:
            new_settings = {
                "provider": provider,
                "strategy": strategy,
                "chunk_size": chunk_size,
                "overlap": overlap,
                "max_sentences": max_sentences,
                "top_k": top_k,
            }
            if new_settings != settings:
                st.session_state.settings = new_settings
                st.session_state.messages = []
                settings = new_settings
                st.toast("Đã áp dụng cấu hình và làm mới hội thoại.")

        st.subheader(":material/filter_list: Lọc metadata")
        audiences = ["Không lọc", *_metadata_options(documents, "audience")]
        categories = ["Không lọc", *_metadata_options(documents, "category")]
        audience = st.selectbox("Đối tượng", audiences)
        category = st.selectbox("Danh mục", categories)
        st.caption("Filter dùng so khớp chính xác và được áp dụng trước khi xếp hạng.")

        metadata_filter = {}
        if audience != "Không lọc":
            metadata_filter["audience"] = audience
        if category != "Không lọc":
            metadata_filter["category"] = category

        st.caption("K3 RAG Library · dữ liệu Harvard Library công khai")
    return settings, metadata_filter


def render_kpis(store, documents, settings: dict, backend_name: str) -> None:
    with st.container(horizontal=True):
        st.metric("Tài liệu", len(documents), border=True)
        st.metric("Chunks", store.get_collection_size(), border=True)
        st.metric("Chunking", STRATEGY_LABELS[settings["strategy"]], border=True)
        st.metric("Embedding", "Local" if settings["provider"] == "local" else "Mock", border=True)
    st.caption(f"Backend đang chạy: `{backend_name}`")


def render_sources(results: list[dict]) -> None:
    if not results:
        st.warning("Không có chunk nào khớp bộ lọc hiện tại.", icon=":material/warning:")
        return

    st.markdown("**Các đoạn làm bằng chứng**")
    for rank, result in enumerate(results, start=1):
        metadata = result.get("metadata", {})
        title = metadata.get("title") or metadata.get("doc_id") or result.get("id")
        with st.container(border=True):
            with st.container(horizontal=True, vertical_alignment="center"):
                st.badge(f"[{rank}] Nguồn", color="blue")
                st.badge(f"score {result['score']:.3f}", color="gray")
                if metadata.get("audience"):
                    st.badge(str(metadata["audience"]), color="green")
            st.markdown(
                f"**{title}** · chunk `{metadata.get('chunk_index', '—')}` · "
                f"doc_id `{metadata.get('doc_id', '—')}`"
            )
            st.markdown(result["content"])
            if metadata.get("source_url"):
                st.link_button(
                    "Mở nguồn gốc",
                    metadata["source_url"],
                    icon=":material/open_in_new:",
                    width="content",
                )


def render_ab_comparison(filtered: list[dict], unfiltered: list[dict]) -> None:
    rows = []
    for rank in range(max(len(filtered), len(unfiltered))):
        filtered_item = filtered[rank] if rank < len(filtered) else None
        unfiltered_item = unfiltered[rank] if rank < len(unfiltered) else None
        rows.append(
            {
                "Hạng": rank + 1,
                "Có filter": filtered_item["metadata"].get("doc_id") if filtered_item else "—",
                "Score có filter": filtered_item["score"] if filtered_item else None,
                "Không filter": unfiltered_item["metadata"].get("doc_id") if unfiltered_item else "—",
                "Score không filter": unfiltered_item["score"] if unfiltered_item else None,
            }
        )
    st.dataframe(
        rows,
        hide_index=True,
        column_config={
            "Score có filter": st.column_config.NumberColumn(format="%.3f"),
            "Score không filter": st.column_config.NumberColumn(format="%.3f"),
        },
    )


def render_assistant_message(message: dict) -> None:
    with st.chat_message("assistant", avatar=":material/local_library:"):
        st.markdown(message["answer"])
        render_sources(message["results"])
        if message.get("metadata_filter"):
            with st.expander("So sánh A/B filter", icon=":material/compare_arrows:"):
                st.caption(f"Filter đã dùng: `{message['metadata_filter']}`")
                render_ab_comparison(message["results"], message["unfiltered_results"])


def run_query(store, embedder, question: str, top_k: int, metadata_filter: dict) -> dict:
    results = store.search_with_filter(
        question,
        top_k=top_k,
        metadata_filter=metadata_filter or None,
    )
    unfiltered_results = (
        store.search(question, top_k=top_k) if metadata_filter else results
    )
    agent = KnowledgeBaseAgent(
        store=RetrievedResultStore(results),
        llm_fn=make_extractive_llm(embedder),
    )
    return {
        "role": "assistant",
        "answer": agent.answer(question, top_k=top_k),
        "results": results,
        "unfiltered_results": unfiltered_results,
        "metadata_filter": dict(metadata_filter),
    }


def render_qa_view(documents, settings: dict, metadata_filter: dict) -> None:
    metrics_slot = st.container()
    try:
        with st.spinner("Đang nạp model và lập chỉ mục dữ liệu…", show_time=True):
            store, embedder, backend_name, warning = build_resources(
                settings["provider"],
                settings["strategy"],
                settings["chunk_size"],
                settings["overlap"],
                settings["max_sentences"],
            )
    except Exception as exc:
        st.error(f"Không thể dựng knowledge base: {exc}", icon=":material/error:")
        return

    with metrics_slot:
        render_kpis(store, documents, settings, backend_name)
    if warning:
        st.warning(warning, icon=":material/warning:")
    if settings["provider"] == "mock":
        st.info(
            "Mock chỉ kiểm tra luồng kỹ thuật, không phản ánh độ tương đồng ngữ nghĩa. "
            "Chọn Local multilingual để đánh giá retrieval.",
            icon=":material/info:",
        )

    if not st.session_state.messages:
        st.subheader(":material/chat: Hỏi kho tri thức")
        st.caption("Chọn một câu hỏi mẫu hoặc nhập câu hỏi của bạn ở ô phía dưới.")
        suggestion = st.pills(
            "Câu hỏi mẫu",
            EXAMPLE_QUESTIONS,
            label_visibility="collapsed",
        )
        if suggestion:
            st.session_state.pending_question = suggestion
            st.rerun()

    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            render_assistant_message(message)

    submitted_question = st.chat_input(
        "Hỏi về dịch vụ và chính sách thư viện…",
        submit_mode="disable",
    )
    question = st.session_state.pending_question or submitted_question
    st.session_state.pending_question = None
    if not question:
        return

    user_message = {"role": "user", "content": question}
    st.session_state.messages.append(user_message)
    with st.chat_message("user"):
        st.markdown(question)

    with st.spinner("Đang truy xuất và tổng hợp câu trả lời…", show_time=True):
        assistant_message = run_query(
            store,
            embedder,
            question,
            settings["top_k"],
            metadata_filter,
        )
    st.session_state.messages.append(assistant_message)
    render_assistant_message(assistant_message)


def _benchmark_rows(benchmark: dict, strategy_name: str) -> list[dict]:
    rows = []
    for entry in benchmark["strategies"][strategy_name]["results"]:
        primary = entry["primary"]
        top1 = primary["top3"][0]["doc_id"] if primary["top3"] else "—"
        rows.append(
            {
                "Query": f"Q{entry['id']}",
                "Điểm": primary["points"],
                "Hạng bằng chứng": str(primary["evidence_rank"] or "Không có"),
                "Agent đúng": primary["agent_correct"],
                "Top-1 doc_id": top1,
            }
        )
    return rows


def render_benchmark_view() -> None:
    if not BENCHMARK_PATH.exists():
        st.warning("Chưa có kết quả benchmark. Chạy `python scripts/run_benchmark.py`.")
        return
    benchmark = load_benchmark()
    st.subheader(":material/analytics: Benchmark retrieval")
    st.caption(
        f"Embedding: `{benchmark['embedding_backend']}` · chấm ở mức chunk · top-{benchmark['top_k']}"
    )

    chart_rows = []
    with st.container(horizontal=True):
        for name, stats in benchmark["strategies"].items():
            label = STRATEGY_LABELS.get(name, name)
            st.metric(
                label,
                f"{stats['score']}/10",
                f"{stats['chunk_count']} chunks",
                border=True,
            )
            chart_rows.append({"Chiến lược": label, "Điểm / 10": stats["score"]})

    st.bar_chart(pd.DataFrame(chart_rows), x="Chiến lược", y="Điểm / 10", horizontal=True)

    strategy_name = st.segmented_control(
        "Xem chi tiết chiến lược",
        options=list(benchmark["strategies"]),
        default="recursive",
        format_func=lambda value: STRATEGY_LABELS.get(value, value),
    )
    st.dataframe(
        _benchmark_rows(benchmark, strategy_name),
        hide_index=True,
        column_config={
            "Điểm": st.column_config.ProgressColumn(min_value=0, max_value=2),
            "Agent đúng": st.column_config.CheckboxColumn(),
        },
    )

    failures = [
        entry
        for entry in benchmark["strategies"][strategy_name]["results"]
        if entry["primary"]["points"] < 2
    ]
    if not failures:
        st.success("Chiến lược này không có query dưới 2 điểm.")
        return

    selected_failure = st.selectbox(
        "Phân tích failure case",
        options=failures,
        format_func=lambda entry: f"Q{entry['id']} · {entry['query']}",
    )
    query_spec = next(
        query for query in benchmark["queries"] if query["id"] == selected_failure["id"]
    )
    primary = selected_failure["primary"]
    with st.container(border=True):
        st.markdown(f"**Gold answer:** {query_spec['gold_answer']}")
        st.markdown(f"**Agent answer:** {primary['agent_answer']}")
        st.caption(
            f"Điểm {primary['points']}/2 · evidence rank: "
            f"{primary['evidence_rank'] or 'không có trong top-3'}"
        )

    benchmark_results = [
        {
            "id": item["id"],
            "content": item["content"],
            "score": item["score"],
            "metadata": {
                "doc_id": item["doc_id"],
                "chunk_index": item["chunk_index"],
            },
        }
        for item in primary["top3"]
    ]
    render_sources(benchmark_results)
    if "unfiltered_ab" in selected_failure:
        with st.expander("A/B metadata filter", icon=":material/compare_arrows:"):
            unfiltered = selected_failure["unfiltered_ab"]["top3"]
            unfiltered_results = [
                {
                    "score": item["score"],
                    "metadata": {"doc_id": item["doc_id"]},
                }
                for item in unfiltered
            ]
            render_ab_comparison(benchmark_results, unfiltered_results)


def render_corpus_view(documents) -> None:
    sources = load_source_registry()
    st.subheader(":material/database: Kho dữ liệu")
    with st.container(horizontal=True):
        st.metric("Tài liệu", len(documents), border=True)
        st.metric("Nguồn có URL", sum(bool(row.get("source_url")) for row in sources), border=True)
        st.metric("Chủ đề", "Harvard Library", border=True)

    st.dataframe(
        sources,
        hide_index=True,
        column_config={
            "source_url": st.column_config.LinkColumn("Nguồn gốc"),
            "file_path": st.column_config.TextColumn("File local"),
            "license_or_permission": st.column_config.TextColumn("Quyền sử dụng"),
        },
    )

    selected_document = st.selectbox(
        "Đọc tài liệu",
        options=documents,
        format_func=lambda document: document.metadata.get("title", document.id),
    )
    with st.container(border=True):
        with st.container(horizontal=True):
            st.badge(str(selected_document.metadata.get("audience", "all")), color="green")
            st.badge(str(selected_document.metadata.get("category", "uncategorized")), color="blue")
            st.badge(str(selected_document.metadata.get("language", "—")), color="gray")
        if selected_document.metadata.get("source_url"):
            st.link_button(
                "Xem trang nguồn",
                selected_document.metadata["source_url"],
                icon=":material/open_in_new:",
            )
        st.markdown(selected_document.content)


_init_state()
documents = load_corpus_documents()

st.title("K3 RAG Library", text_alignment="left")
st.caption(
    "Truy xuất dịch vụ và chính sách thư viện, kiểm tra top-k, metadata filter và nguồn của từng câu trả lời."
)

view = st.segmented_control(
    "Chế độ",
    ["qa", "benchmark", "corpus"],
    default="qa",
    format_func={
        "qa": "Hỏi đáp",
        "benchmark": "Benchmark",
        "corpus": "Kho dữ liệu",
    }.get,
    label_visibility="collapsed",
)

if view == "qa":
    current_settings, current_filter = render_sidebar(documents)
    render_qa_view(documents, current_settings, current_filter)
elif view == "benchmark":
    render_benchmark_view()
else:
    render_corpus_view(documents)
