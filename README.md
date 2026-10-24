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

## Rescue rule (added after the RETRO miss)

When the answer scorer refuses (best sentence score below 0.5) but the
reranker is confident and consistent, the agent quotes the top
reranked passage, labelled "retriever-selected" in the report. Both
gates are required: top cross-encoder score above zero AND at least 3
of the top 5 passages from one document. The bread refusal scores 3/5
on share but a -10.69 top score, so share alone never rescues. Golden
eval after the fix: 9/9, refusal rate 1.0.
