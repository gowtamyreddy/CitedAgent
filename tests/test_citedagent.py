import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from citedagent import composer, planner, verifier
from citedagent.agent import CitedAgent
from citedagent.eval import gate, score_case


class FakeQA:
    def retrieve(self, question):
        if "bread" in question.lower():
            return {"status": "insufficient_evidence", "spans": []}
        return {"status": "answered", "spans": [
            {"text": "RAPTOR clusters chunks of text.",
             "citation": {"doc_id": "2401.18059", "page": 1,
                          "char_start": 0, "char_end": 30,
                          "score": 0.9}},
            {"text": "A weak claim.",
             "citation": {"doc_id": "9999.99999", "page": 2,
                          "char_start": 0, "char_end": 12,
                          "score": 0.2}},
            {"text": "RAPTOR clusters chunks of text.",
             "citation": {"doc_id": "2401.18059", "page": 1,
                          "char_start": 0, "char_end": 30,
                          "score": 0.9}},
        ]}


class AgentTests(unittest.TestCase):
    def test_planner_expands(self):
        subs = planner.plan("How does RAPTOR organize retrieved text?")
        self.assertEqual(subs[0],
                         "How does RAPTOR organize retrieved text?")
        self.assertGreaterEqual(len(subs), 2)

    def test_verifier_threshold_and_dedupe(self):
        spans = FakeQA().retrieve("x")["spans"]
        kept = verifier.verify(spans)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["citation"]["doc_id"], "2401.18059")

    def test_agent_answers_with_citation(self):
        agent = CitedAgent(FakeQA())
        out = agent.run("How does RAPTOR organize retrieved text?")
        self.assertEqual(out["status"], "answered")
        self.assertIn("2401.18059", out["report"])
        self.assertEqual(len(out["trace"]), 8)  # 1 plan + 3x2 + 1 compose

    def test_agent_refuses_off_corpus(self):
        agent = CitedAgent(FakeQA())
        out = agent.run("What is the best way to bake bread?")
        self.assertEqual(out["status"], "refused")

    def test_composer_partial_refusal(self):
        out = composer.compose("q", [("a", [{"text": "t",
            "citation": {"doc_id": "d", "page": 1, "char_start": 0,
                         "char_end": 1, "score": 0.9}}]),
            ("b", [])])
        self.assertEqual(out["status"], "answered")
        self.assertEqual(out["unsupported"], ["b"])

    def test_eval_gate(self):
        a = {"pass_rate": 0.8, "cases": [
            {"case_id": "x", "passed": True},
            {"case_id": "y", "passed": True}]}
        b = {"pass_rate": 0.8, "cases": [
            {"case_id": "x", "passed": True},
            {"case_id": "y", "passed": False}]}
        verdict = gate(a, b)
        self.assertEqual(verdict["verdict"], "DO NOT SHIP")
        self.assertEqual(verdict["regressed"], ["y"])

    def test_score_case_refusal(self):
        case = {"id": "r", "question": "bread?",
                "should_refuse": True}
        self.assertTrue(score_case(case, {"status": "refused",
                                          "report": "", "citations": []}
                                   )["passed"])


if __name__ == "__main__":
    unittest.main()
