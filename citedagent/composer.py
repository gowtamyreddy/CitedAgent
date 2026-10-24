"""Compose the report: quotes, evidence table, refusals."""


def _sort_key(span):
    """Answerer score, highest first."""
    return span["citation"]["score"]


def _source_line(cit):
    return ("<small>Source: arXiv %s, page %s, chars %s-%s, "
            " score %.3f</small>"
            % (cit["doc_id"], cit["page"], cit["char_start"],
               cit["char_end"], cit["score"]))


def compose(question, sub_results):
    """sub_results: list of (sub_question, verified_spans)."""
    verified = [s for _, spans in sub_results for s in spans]
    # dedupe across sub-questions too: the same passage can win
    # for several sub-questions, at different scores. Keep the
    # highest-scored copy.
    best = {}
    for span in verified:
        cit = span["citation"]
        key = (cit["doc_id"], cit["page"], cit["char_start"],
               cit["char_end"])
        if key not in best or _sort_key(span) > _sort_key(best[key]):
            best[key] = span
    verified = sorted(best.values(), key=_sort_key, reverse=True)
    unsupported = [q for q, spans in sub_results if not spans]
    if not verified:
        return {
            "status": "refused",
            "report": ("I could not find supporting evidence in the "
                       "papers for this question, so I will not "
                       "answer it."),
            "citations": [],
            "unsupported": [q for q, _ in sub_results],
        }
    lines = ["# Research report", "", "## Answer", ""]
    for span in verified[:5]:
        cit = span["citation"]
        lines.append("> " + span["text"])
        lines.append("")
        lines.append(_source_line(cit))
        lines.append("")
    lines.append("## Evidence")
    lines.append("")
    for span in verified[:8]:
        cit = span["citation"]
        lines.append("- arXiv %s, page %s, score %.3f"
                     % (cit["doc_id"], cit["page"], cit["score"]))
    if unsupported:
        lines.append("")
        lines.append("## Could not verify")
        lines.append("")
        for q in unsupported:
            lines.append("- %s: no supporting passage found" % q)
    return {"status": "answered", "report": "\n".join(lines),
            "citations": [s["citation"] for s in verified],
            "unsupported": unsupported}
