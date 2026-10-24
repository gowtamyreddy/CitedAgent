"""The agent loop: plan, retrieve, verify, compose, trace."""
import os
import time

from citedagent import composer, planner, verifier
from citedagent.qa import EvidenceRAGQA


class CitedAgent:
    def __init__(self, qa):
        self.qa = qa

    def run(self, question, run_id=None):
        t_start = time.perf_counter()
        trace = []

        def step(kind, detail, fn):
            t0 = time.perf_counter()
            try:
                out = fn()
                status = "ok"
            except Exception as exc:
                out, status = str(exc), "error"
            trace.append({"kind": kind, "detail": detail,
                          "latency_ms": round(
                              (time.perf_counter() - t0) * 1000, 1),
                          "status": status})
            if status == "error":
                raise RuntimeError(out)
            return out

        subs = step("plan", question, lambda: planner.plan(question))
        sub_results = []
        for sub in subs:
            result = step("retrieve", sub,
                          lambda s=sub: self.qa.retrieve(s))
            spans = step("verify", sub,
                         lambda r=result: verifier.verify(
                             r["spans"]))
            sub_results.append((sub, spans))
        out = step("compose", question,
                   lambda: composer.compose(question, sub_results))
        total = round((time.perf_counter() - t_start) * 1000, 1)
        return {"question": question, "plan": subs,
                "status": out["status"], "report": out["report"],
                "citations": out["citations"],
                "unsupported": out["unsupported"], "trace": trace,
                "latency_ms": total}


def make_agent():
    home = os.environ.get("EVIDENCERAG_HOME", "../evidencerag")
    return CitedAgent(EvidenceRAGQA(home))
