"""CitedAgent dashboard: ask, read the report, inspect the trace."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr

from citedagent.agent import make_agent
from citedagent.eval import load_cases, run_eval

AGENT = make_agent()


def ask(question):
    out = AGENT.run(question)
    rows = [[s["kind"], s["detail"][:60], "%.0f ms" % s["latency_ms"],
             s["status"]] for s in out["trace"]]
    return (out["report"], rows,
            "Status: %s | total %.0f ms | %d citations"
            % (out["status"], out["latency_ms"],
               len(out["citations"])))


def run_gate():
    cases = load_cases()
    report = run_eval(AGENT, cases)
    lines = ["Pass rate: %.3f over %d cases"
             % (report["pass_rate"], report["n_cases"]),
             "Refusal rate: %s" % report["refusal_rate"]]
    for case in report["cases"]:
        mark = "PASS" if case["passed"] else "FAIL"
        lines.append("%s %s (%s)" % (mark, case["case_id"],
                                     case["reason"]))
    return "\n".join(lines)


with gr.Blocks(title="CitedAgent",
               theme=gr.themes.Soft(primary_hue="indigo",
                                    neutral_hue="slate"),
               css=".footer {display: none !important}") as demo:
    gr.Markdown("# CitedAgent: a research agent that proves its "
                "work\n\nAsk a question. CitedAgent plans "
                "sub-questions, retrieves from real papers, "
                "verifies every claim against a citation, and "
                "writes a cited report. What it cannot support, "
                "it refuses.")
    question = gr.Textbox(
        label="Research question",
        placeholder="How does RAPTOR organize retrieved text?")
    gr.Examples(
        examples=[["How does RAPTOR organize retrieved text?"],
                  ["How many Wikipedia passages does Dense "
                   "Passage Retrieval index?"],
                  ["What is the best way to bake bread?"]],
        inputs=question)
    ask_btn = gr.Button("Research", variant="primary")
    report = gr.Markdown("_Your report will appear here._")
    trace = gr.Dataframe(
        headers=["Step", "Detail", "Time", "Status"],
        datatype=["str", "str", "str", "str"],
        label="Run trace", interactive=False)
    summary = gr.Markdown()
    ask_btn.click(ask, inputs=question,
                  outputs=[report, trace, summary], api_name="ask")
    gate_btn = gr.Button("Run the eval gate")
    gate_out = gr.Markdown()
    gate_btn.click(run_gate, outputs=gate_out, api_name="gate")

if __name__ == "__main__":
    demo.queue()
    demo.launch()
