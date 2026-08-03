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

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy ngữ cảnh phù hợp trong cơ sở tri thức để trả lời câu hỏi."

        context_parts = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            doc_id = metadata.get("doc_id", result.get("id", "unknown"))
            source = metadata.get("source_url") or metadata.get("source") or doc_id
            context_parts.append(
                f"[{index}] doc_id={doc_id}; source={source}\n{result['content']}"
            )

        context = "\n\n".join(context_parts)
        prompt = (
            "Instruction: Answer the question using only the supplied context. "
            "Cite supporting chunks with their bracketed numbers, such as [1]. "
            "If the context is insufficient, state that clearly.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
