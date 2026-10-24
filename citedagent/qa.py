"""Live EvidenceRAG retriever, same adapter shape as VoiceLoop."""
import sys

_cache = {}


def _load(home):
    if home in _cache:
        return _cache[home]
    if home not in sys.path:
        sys.path.insert(0, home)
    from src import embed, index as vector_index, ingest
    from src import rerank as rerank_module
    from src import answer as answer_module
    from src.retrieve import Retriever
    import pathlib
    artifacts = pathlib.Path(home) / "data" / "artifacts"
    chunks = ingest.load_chunks(artifacts / "chunks.jsonl")
    faiss_index = vector_index.load_index(artifacts / "index.faiss")
    embedder = embed.Embedder()
    retriever = Retriever(chunks, embedder, faiss_index)
    _cache[home] = (retriever, rerank_module, answer_module)
    return _cache[home]


class EvidenceRAGQA:
    def __init__(self, home, rerank=True, top_k=5):
        self.home = str(home)
        self.use_rerank = bool(rerank)
        self.top_k = int(top_k)
        self._reranker = None

    def retrieve(self, question):
        retriever, rerank_module, answer_module = _load(self.home)
        fused = retriever.hybrid_search(question, top_k=20)
        if self.use_rerank:
            if self._reranker is None:
                self._reranker = rerank_module.Reranker()
            ranked = rerank_module.rerank(question, fused,
                                          self._reranker, self.top_k)
        else:
            ranked = fused[: self.top_k]
        result = answer_module.extractive_answer(
            question, ranked, retriever.embedder)
        spans = result.get("spans") or []
        return {"status": result.get("status"), "spans": spans}
