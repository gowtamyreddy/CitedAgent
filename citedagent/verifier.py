"""Verify retrieved spans: threshold, dedupe, keep the evidence."""
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

