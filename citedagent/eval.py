"""Golden-set eval and release gate for the agent."""
import json
import os

GOLDEN = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "data", "golden_cases.jsonl")


def load_cases(path=GOLDEN):
    cases = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def score_case(case, result):
    if case.get("should_refuse"):
        passed = result["status"] == "refused"
        return {"case_id": case["id"], "passed": passed,
                "reason": "refused as expected" if passed
                else "answered but should refuse"}
    docs = [c["doc_id"] for c in result["citations"]]
    doc_ok = case["expected_doc"] in docs
    phrase_ok = case["expected_phrase"].lower() in \
        result["report"].lower()
    passed = doc_ok or phrase_ok
    return {"case_id": case["id"], "passed": passed,
            "reason": ("doc match" if doc_ok else
                       "phrase match" if phrase_ok else
                       "no doc or phrase match")}


def run_eval(agent, cases=None):
    cases = cases if cases is not None else load_cases()
    scored = []
    for case in cases:
        result = agent.run(case["question"])
        scored.append(score_case(case, result))
    passed = sum(1 for s in scored if s["passed"])
    refusals = [c for c in cases if c.get("should_refuse")]
    ref_ok = sum(1 for c, s in zip(cases, scored)
                 if c.get("should_refuse") and s["passed"])
    return {"pass_rate": round(passed / len(scored), 4) if scored
            else 0.0,
            "n_cases": len(scored),
            "refusal_rate": round(ref_ok / len(refusals), 4)
            if refusals else None,
            "cases": scored}


def gate(report_a, report_b):
    """B ships only if it does not lose pass rate and regresses
    nothing."""
    regressed = [b["case_id"] for a, b in
                 zip(report_a["cases"], report_b["cases"])
                 if a["passed"] and not b["passed"]]
    improved = [b["case_id"] for a, b in
                zip(report_a["cases"], report_b["cases"])
                if not a["passed"] and b["passed"]]
    ok = (report_b["pass_rate"] >= report_a["pass_rate"]
          and not regressed)
    return {"verdict": "SHIP" if ok else "DO NOT SHIP",
            "pass_rate_a": report_a["pass_rate"],
            "pass_rate_b": report_b["pass_rate"],
            "regressed": regressed, "improved": improved}
