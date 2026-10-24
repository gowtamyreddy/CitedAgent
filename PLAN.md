# CitedAgent: capstone plan

## One line
A research agent that does a real job: given a question, it
plans sub-questions, retrieves from real papers, verifies every
claim against a citation, writes a cited report, and refuses
what it cannot support.

## Why this is the capstone
EvidenceRAG answers. Forkwise traces. TrustLens gates.
VoiceLoop speaks. CitedAgent is the system those tools were
built for: it uses the EvidenceRAG pipeline as its retriever,
records a Forkwise-shaped step trace for every run, and is
scored by a TrustLens-style eval gate. The portfolio stops
being five demos and becomes one engineer who built a system.

## Pipeline (no LLM, free, local)
1. Plan: expand the question into up to 3 sub-questions
   (original, keyword form, method form).
2. Retrieve: each sub-question runs the live EvidenceRAG
   pipeline (hybrid FAISS + BM25 + RRF, cross-encoder rerank).
3. Verify: drop spans below the 0.5 evidence threshold,
   dedupe by document and character range.
4. Compose: report with quoted answer, evidence table, and a
   "could not verify" section per unsupported sub-question.
   Zero verified spans means a full refusal, not a guess.
5. Trace: every step logged with kind, input, output,
   latency, and status, one JSON file per run.
6. Gate: a golden set scores pass rate, citation precision,
   and refusal correctness across two configs.

## Not in V1
- No LLM planner or writer (rule-based planning, extractive
  quotes). An LLM layer is a documented future step, gated by
  the same eval set before it ships.
- No web search: the corpus is the EvidenceRAG paper set.

## Role split
- Boone: agent, eval, UI, tests.
- Meganaa: the golden questions, the report judgment calls,
  README story, interview explanation.

## Fix log: RETRO recall gap (2026-10-24)

Failure: "What is RETRO?" refused even though 2112.04426 is in the
corpus. Diagnosis: retrieval and reranking found the paper (top
reranked score 2.44, 5/5 passages RETRO), but the answer scorer's
sentence similarity peaked at 0.29, below the 0.5 bar. Fix: the
two-gate rescue rule above, verified by the full golden eval (9/9)
with both refusal cases still refusing.

## Update: rescue rule removed (2026-10-24)

The rescue rule above was a band-aid and has been deleted from the
code, the tests, and the report format. Root cause found the same day:
small-caps PDF extraction mangled RETRO's name in 149 chunks (see
EvidenceRAG src/ingest.py clean_text). After the corpus fix and a
curated rebuild, RETRO answers through the normal verify path. Do not
re-add a rescue-style fallback without a new, separately diagnosed
failure.
