# CitedAgent

A research agent that proves its work.

Ask CitedAgent a question. It plans sub-questions, retrieves
from real research papers through EvidenceRAG, verifies every
claim against a citation, and writes a report made of quotes
with document, page, and character offsets. Claims it cannot
support go in a "could not verify" section. Questions with no
supporting evidence get a refusal, not an answer.

## Run it

    EVIDENCERAG_HOME=../evidencerag python -m citedagent.cli ask \
        "How does RAPTOR organize retrieved text?"

    EVIDENCERAG_HOME=../evidencerag python -m citedagent.cli eval
    EVIDENCERAG_HOME=../evidencerag python -m citedagent.cli gate
    python app.py   # Gradio UI

## Status
V1: planner, retriever, verifier, composer, trace, eval gate,
dashboard, tests.

## The RETRO miss, and the real fix (2026-10-24)

The agent once refused "What is RETRO?" even though the paper was in
the corpus. The first fix was a rescue rule (quote the top reranked
passage when the reranker was confident and consistent). That was a
band-aid and it was removed the same day.

The real cause was upstream: the RETRO paper sets its name in small
caps, and the PDF extractor mangled it into "R/e.sc/t.sc/r.sc/o.sc"
in 149 chunks, so the paper's own name was unsearchable in its own
text. The fix went into EvidenceRAG's text cleaner (small-caps repair
before chunking, so citations stay exact) plus a curated rebuild of
exactly the 20-paper index. After that, RETRO answers through the
normal path with scored citations, and the golden eval is 9/9 with
refusal rate 1.0 and no rescue rule in the code.
