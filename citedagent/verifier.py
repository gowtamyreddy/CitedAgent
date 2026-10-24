"""Verify retrieved spans: threshold, dedupe, keep the evidence."""
import collections
import time

THRESHOLD = 0.5


def verify(spans):
    """Drop below-threshold spans, dedupe by doc and char range."""
    seen, kept = set(), []
    for span in spans:
        cit = span["citation"]
        if cit["score"] < THRESHOLD:
            continue
        key = (cit["doc_id"], cit["page"], cit["char_start"],
               cit["char_end"])
        if key in seen:
            continue
        seen.add(key)
        kept.append(span)
    return kept


def rescue(ranked):
    """Fallback when the answer scorer refuses but the reranker is
    confident AND consistent. Both gates are required:
      - top cross-encoder score above zero, and
      - at least 3 of the top 5 passages from one document.
    The bread refusal scores 3/5 on share but a -10.69 top score,
    so share alone would rescue wrongly; the score gate blocks it.
    Returns one span (the top passage, marked rescued) or None.
    The passage is quoted whole and labelled retriever-selected
    in the report, never dressed up as an answerer-selected quote.
    """
    if not ranked or len(ranked) < 3:
        return None
    top = ranked[0]
    if top["rerank_score"] <= 0:
        return None
    docs = collections.Counter(r["doc_id"] for r in ranked[:5])
    if docs.most_common(1)[0][1] < 3:
        return None
    return {"text": top["text"],
            "citation": {"doc_id": top["doc_id"], "page": top["page"],
                         "char_start": top["char_start"],
                         "char_end": top["char_end"], "score": None,
                         "rerank_score": round(top["rerank_score"], 3),
                         "rescued": True}}
