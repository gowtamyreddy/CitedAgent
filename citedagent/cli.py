"""CLI: ask, eval, gate."""
import argparse
import json
import os
import sys

from citedagent.agent import CitedAgent
from citedagent.eval import gate, load_cases, run_eval
from citedagent.qa import EvidenceRAGQA


def _agent(top_k, rerank):
    home = os.environ.get("EVIDENCERAG_HOME", "../evidencerag")
    return CitedAgent(EvidenceRAGQA(home, rerank=rerank, top_k=top_k))


def cmd_ask(args):
    agent = _agent(args.top_k, not args.no_rerank)
    out = agent.run(args.question)
    runs_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "runs")
    os.makedirs(runs_dir, exist_ok=True)
    import time as _time
    path = os.path.join(runs_dir, "run_%d.json" % int(_time.time()))
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(out["report"])
    print("")
    print("status: %s | latency: %.0f ms | steps: %d"
          % (out["status"], out["latency_ms"], len(out["trace"])))


def cmd_eval(args):
    agent = _agent(args.top_k, not args.no_rerank)
    report = run_eval(agent)
    print(json.dumps(report, indent=2))


def cmd_gate(args):
    agent_a = _agent(5, True)
    agent_b = _agent(3, True)
    report_a = run_eval(agent_a)
    report_b = run_eval(agent_b)
    verdict = gate(report_a, report_b)
    print(json.dumps({"config_a": "top_k 5, rerank on",
                      "config_b": "top_k 3, rerank on",
                      **verdict}, indent=2))


def main():
    parser = argparse.ArgumentParser(prog="citedagent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ask")
    p.add_argument("question")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--no-rerank", action="store_true")
    p.set_defaults(fn=cmd_ask)

    p = sub.add_parser("eval")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--no-rerank", action="store_true")
    p.set_defaults(fn=cmd_eval)

    p = sub.add_parser("gate")
    p.set_defaults(fn=cmd_gate)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
