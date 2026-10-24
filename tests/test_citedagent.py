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


def _ranked(doc_scores):
    return [{"doc_id": d, "page": 1, "char_start": 0, "char_end": 10,
             "text": "passage", "rerank_score": s}
            for d, s in doc_scores]


class RescueTests(unittest.TestCase):
    def test_rescue_positive_retro_like(self):
        ranked = _ranked([("2112.04426", 2.44), ("2112.04426", 1.79),
                          ("2112.04426", 0.67), ("2112.04426", 0.52),
                          ("2112.04426", 0.30)])
        span = verifier.rescue(ranked)
        self.assertIsNotNone(span)
        self.assertEqual(span["citation"]["doc_id"], "2112.04426")
        self.assertTrue(span["citation"]["rescued"])

    def test_rescue_rejects_negative_top_despite_share(self):
        # bread: 3/5 from one doc, but top score -10.69
        ranked = _ranked([("2505.19134", -10.69), ("2112.04426", -11.04),
                          ("2112.04426", -11.06),
                          ("cancer-ensemble-segmentation", -11.06),
                          ("2112.04426", -11.07)])
        self.assertIsNone(verifier.rescue(ranked))

    def test_rescue_rejects_scattered_positive(self):
        ranked = _ranked([("2112.04426", 0.5), ("2112.04426", 0.4),
                          ("gsad-sdee-2022", 0.3), ("2505.19134", 0.2),
                          ("2505.19134", 0.1)])
        self.assertIsNone(verifier.rescue(ranked))


class FakeRescueQA:
    def retrieve(self, question):
        return {"status": "insufficient_evidence", "spans": [],
                "ranked": _ranked([("2112.04426", 2.44),
                                   ("2112.04426", 1.79),
                                   ("2112.04426", 0.67),
                                   ("2112.04426", 0.52),
                                   ("2112.04426", 0.30)])}


class AgentRescueTests(unittest.TestCase):
    def test_agent_answers_via_rescue(self):
        agent = CitedAgent(FakeRescueQA())
        out = agent.run("What is RETRO?")
        self.assertEqual(out["status"], "answered")
        self.assertIn("2112.04426", out["report"])
        self.assertIn("retriever-selected", out["report"])
        self.assertTrue(any(t["kind"] == "rescue"
                            for t in out["trace"]))


if __name__ == "__main__":
    unittest.main()
