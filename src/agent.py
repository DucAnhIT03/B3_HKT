from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        if metadata_filter is None:
            results = self.store.search(question, top_k=top_k)
        else:
            results = self.store.search_with_filter(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        if not results:
            return "Không tìm thấy ngữ cảnh phù hợp để trả lời câu hỏi."

        context_blocks = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or result.get("id")
            context_blocks.append(
                f"[Context {index} | source: {source}]\n{result['content']}"
            )

        context = "\n\n".join(context_blocks)
        prompt = (
            "Answer the question using only the retrieved context below. "
            "If the context is insufficient, say that you do not have enough information.\n\n"
            f"Retrieved context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
