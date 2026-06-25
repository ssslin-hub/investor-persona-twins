"""B2 + B4 evaluators ported from investorPersona_2/scripts/*.mjs.

Subcommands:
  b2      — per-analyst evaluator (0-4 + binary + 4 sub-dimensions) on auto-pipeline TEST
  b4      — set-level evaluator (coverage + precision) on auto-pipeline TEST
  report  — assemble reports/b2_b4_summary.md from whichever artifacts exist

Reads:
  data_auto/final_eval/summary.json    per-analyst predicted_questions (auto-pipeline)
  data_auto/test.json                  per-analyst actual questions on 2026-Q1

Writes:
  data_auto/final_eval/b2/<analyst>.json
  data_auto/final_eval/b2_summary.json
  data_auto/final_eval/b4.json
  reports/b2_b4_summary.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
FINAL_EVAL = os.path.join(DATA_AUTO, "final_eval")
REPORTS = os.path.join(ROOT, "reports")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]

B2_PROMPT_PATH = os.path.join(PROMPTS, "b2_eval.md")
B4_PROMPT_PATH = os.path.join(PROMPTS, "b4_eval.md")


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def load_text(p: str) -> str:
    with open(p) as f:
        return f.read()


# ---- B2 ----

def _b2_stub(analyst: str) -> dict:
    return {
        "analyst_name": analyst,
        "best_match_actual_tuple_id": None,
        "match_score_0_to_4": 0,
        "binary_match": False,
        "topic_match": "none",
        "trigger_alignment": "none",
        "question_form_alignment": "none",
        "granularity_alignment": "none",
        "reasoning": "DRY_RUN stub",
        "miss_or_gap": "DRY_RUN stub",
    }


def cmd_b2() -> None:
    print("=== B2 — per-analyst evaluator on auto TEST ===")
    out_dir = os.path.join(FINAL_EVAL, "b2")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    summary = json.load(open(os.path.join(FINAL_EVAL, "summary.json")))
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]
    tpl = load_text(B2_PROMPT_PATH)

    evaluations = []
    for name in TEST_RETURNING:
        pa = summary.get("per_analyst", {}).get(name)
        if not pa:
            print(f"  ! {name}: no auto-pipeline predictions; skipping")
            continue
        sim = pa.get("predictions") or {}
        sim_block = {
            "analyst_name": name,
            "predicted_questions": sim.get("predicted_questions", []),
        }
        # Actuals block, attaching tuple_id so the evaluator can reference one
        actuals = []
        for i, a in enumerate(actuals_by.get(name, [])):
            actuals.append({
                "tuple_id": f"{name}-actual-{i}",
                "analyst_name": name,
                "call": a.get("call"),
                "question": a.get("question"),
            })

        prompt = (tpl
                  .replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2))
                  .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
        log = os.path.join(log_dir, f"{_safe(name)}.txt")
        out = call_llm(prompt, expect_json=True, dry_run_stub=_b2_stub(name), log_to=log)
        try:
            ev = parse_json_strict(out)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {name}: parse failed ({e}); using stub")
            ev = _b2_stub(name)
        # Ensure analyst_name set
        ev["analyst_name"] = name
        path = os.path.join(out_dir, f"{_safe(name)}.json")
        with open(path, "w") as f:
            json.dump(ev, f, indent=2)
        evaluations.append(ev)
        print(f"  {name:25s} score={ev.get('match_score_0_to_4',0)} binary={ev.get('binary_match',False)} "
              f"topic={ev.get('topic_match','?')}")

    # Aggregate exactly per summarizeEvaluations
    scored = [e for e in evaluations if isinstance(e.get("match_score_0_to_4"), (int, float))]
    binary = sum(1 for e in scored if e.get("binary_match"))
    avg = (sum(e["match_score_0_to_4"] for e in scored) / max(1, len(scored))) if scored else 0.0
    agg = {
        "evaluated_count": len(scored),
        "binary_match_count": binary,
        "binary_match_rate": binary / max(1, len(scored)),
        "average_match_score_0_to_4": avg,
    }
    with open(os.path.join(FINAL_EVAL, "b2_summary.json"), "w") as f:
        json.dump(agg, f, indent=2)
    print(f"\n  B2 aggregate: evaluated={agg['evaluated_count']} binary={agg['binary_match_count']} "
          f"rate={agg['binary_match_rate']:.3f} avg_score={agg['average_match_score_0_to_4']:.3f}")


# ---- B4 ----

def _b4_stub(n_pred: int, n_act: int) -> dict:
    return {
        "actual_question_count": n_act,
        "predicted_question_count": n_pred,
        "actual_coverage": [],
        "predicted_precision": [],
        "set_metrics": {
            "coverage_count": 0,
            "coverage_rate": 0.0,
            "useful_prediction_count": 0,
            "precision_rate": 0.0,
            "average_actual_best_score": 0.0,
            "average_predicted_best_score": 0.0,
        },
        "missed_actual_themes": [],
        "overpredicted_themes": [],
        "summary": "DRY_RUN stub",
    }


def cmd_b4() -> None:
    print("=== B4 — set-level evaluator on auto TEST ===")
    log_dir = os.path.join(FINAL_EVAL, "b4_logs")
    os.makedirs(log_dir, exist_ok=True)

    summary = json.load(open(os.path.join(FINAL_EVAL, "summary.json")))
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]

    predicted: list[dict] = []
    actuals: list[dict] = []

    for name in TEST_RETURNING:
        pa = summary.get("per_analyst", {}).get(name) or {}
        for i, q in enumerate((pa.get("predictions") or {}).get("predicted_questions", [])):
            predicted.append({
                "candidate_id": f"{_safe(name)}-pred-{i}",
                "source_analyst": name,
                "question": q.get("question_text", ""),
                "topic_label": q.get("topic_label", ""),
            })
        for i, a in enumerate(actuals_by.get(name, [])):
            actuals.append({
                "actual_id": f"{_safe(name)}-actual-{i}",
                "source_analyst": name,
                "question": a.get("question", ""),
            })

    print(f"  predicted set size: {len(predicted)};  actual set size: {len(actuals)}")

    tpl = load_text(B4_PROMPT_PATH)
    prompt = (tpl
              .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(predicted, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
    log = os.path.join(log_dir, "b4_prompt.txt")
    out = call_llm(prompt, expect_json=True,
                   dry_run_stub=_b4_stub(len(predicted), len(actuals)), log_to=log)
    try:
        ev = parse_json_strict(out)
    except Exception as e:  # noqa: BLE001
        print(f"  ! parse failed ({e}); using stub")
        ev = _b4_stub(len(predicted), len(actuals))

    with open(os.path.join(FINAL_EVAL, "b4.json"), "w") as f:
        json.dump(ev, f, indent=2)
    m = ev.get("set_metrics", {})
    print(f"\n  B4 set_metrics: coverage={m.get('coverage_count','?')}/{ev.get('actual_question_count','?')} "
          f"(rate={m.get('coverage_rate','?')}) "
          f"precision={m.get('useful_prediction_count','?')}/{ev.get('predicted_question_count','?')} "
          f"(rate={m.get('precision_rate','?')}) "
          f"avg_act={m.get('average_actual_best_score','?')} avg_pred={m.get('average_predicted_best_score','?')}")


# ---- Report ----

def cmd_report() -> None:
    print("=== Report — assemble reports/b2_b4_summary.md ===")
    os.makedirs(REPORTS, exist_ok=True)

    # Auto-pipeline B2
    b2_summary_path = os.path.join(FINAL_EVAL, "b2_summary.json")
    b2_summary = json.load(open(b2_summary_path)) if os.path.exists(b2_summary_path) else None
    b2_per_analyst = []
    b2_dir = os.path.join(FINAL_EVAL, "b2")
    if os.path.isdir(b2_dir):
        for name in TEST_RETURNING:
            p = os.path.join(b2_dir, f"{_safe(name)}.json")
            if os.path.exists(p):
                b2_per_analyst.append((name, json.load(open(p))))

    # Auto-pipeline B4
    b4_path = os.path.join(FINAL_EVAL, "b4.json")
    b4 = json.load(open(b4_path)) if os.path.exists(b4_path) else None

    # Existing hit rate for context
    hit_summary = json.load(open(os.path.join(FINAL_EVAL, "summary.json")))

    # Published investorPersona_2 reference (for context only; different roster)
    ref_b2_path = os.path.join(os.path.dirname(ROOT), "investorPersona_2",
                                "data", "llm", "llm_run_summary.json")
    ref_b4_path = os.path.join(os.path.dirname(ROOT), "investorPersona_2",
                                "data", "llm_set", "set_evaluation.json")
    ref_b2 = json.load(open(ref_b2_path)) if os.path.exists(ref_b2_path) else None
    ref_b4 = json.load(open(ref_b4_path)) if os.path.exists(ref_b4_path) else None

    lines: list[str] = []
    lines.append("# B2 + B4 metrics on the auto-discovery pipeline (TEST = 2026-Q1)\n")

    lines.append("## Headline\n")
    lines.append(f"- Coarse hit rate (this pipeline): **{hit_summary['hit_rate_exact_or_partial']:.3f}** "
                 f"({hit_summary['n_exact']} exact + {hit_summary['n_partial']} partial / {hit_summary['n_actual']})  "
                 f"_(reference: V1 baseline 0.500)_")
    if b2_summary:
        lines.append(f"- **B2 binary_match_rate** (per-analyst, score ≥ 3): "
                     f"**{b2_summary['binary_match_rate']:.3f}** "
                     f"({b2_summary['binary_match_count']} / {b2_summary['evaluated_count']}); "
                     f"avg match_score_0_to_4 = **{b2_summary['average_match_score_0_to_4']:.3f}**")
    if b4 and b4.get("set_metrics"):
        sm = b4["set_metrics"]
        lines.append(f"- **B4 coverage_rate** (set-level, score ≥ 3): "
                     f"**{sm['coverage_rate']:.3f}** "
                     f"({sm['coverage_count']} / {b4['actual_question_count']}); "
                     f"**precision_rate** = **{sm['precision_rate']:.3f}** "
                     f"({sm['useful_prediction_count']} / {b4['predicted_question_count']}); "
                     f"avg_actual_best_score = **{sm['average_actual_best_score']:.3f}**, "
                     f"avg_predicted_best_score = **{sm['average_predicted_best_score']:.3f}**")
    lines.append("")

    if ref_b2 or ref_b4:
        lines.append("## Reference: investorPersona_2 (Node pipeline, different roster)\n")
        lines.append("These numbers are from the published Node-pipeline outputs and are **not apples-to-apples** "
                     "with the auto-pipeline here:\n"
                     "- Node B2 evaluator ran on 11 analysts (incl. 2 cold-start); auto here runs on 9 returning.\n"
                     "- Node B4 evaluator ran on 12 actual questions; auto here runs on 10 (cold-start excluded).\n")
        if ref_b2 and ref_b2.get("metrics"):
            m = ref_b2["metrics"]
            lines.append(f"- Node B2: binary_match_rate = {m.get('binary_match_rate',0):.3f} "
                         f"({m.get('binary_match_count',0)} / {m.get('evaluated_count',0)}); "
                         f"avg score = {m.get('average_match_score_0_to_4',0):.3f}")
        if ref_b4 and ref_b4.get("set_metrics"):
            sm = ref_b4["set_metrics"]
            lines.append(f"- Node B4: coverage_rate = {sm.get('coverage_rate',0):.3f} "
                         f"({sm.get('coverage_count',0)} / {ref_b4.get('actual_question_count',0)}); "
                         f"precision_rate = {sm.get('precision_rate',0):.3f} "
                         f"({sm.get('useful_prediction_count',0)} / {ref_b4.get('predicted_question_count',0)}); "
                         f"avg_actual_best = {sm.get('average_actual_best_score',0):.3f}; "
                         f"avg_pred_best = {sm.get('average_predicted_best_score',0):.3f}")
        lines.append("")

    if b2_per_analyst:
        lines.append("## B2 per-analyst breakdown (auto-pipeline)\n")
        lines.append("| analyst | score 0-4 | binary | topic | trigger | form | granularity |")
        lines.append("|---|---|---|---|---|---|---|")
        for name, ev in b2_per_analyst:
            lines.append(f"| {name} | {ev.get('match_score_0_to_4','?')} | "
                         f"{'✓' if ev.get('binary_match') else '·'} | "
                         f"{ev.get('topic_match','?')} | "
                         f"{ev.get('trigger_alignment','?')} | "
                         f"{ev.get('question_form_alignment','?')} | "
                         f"{ev.get('granularity_alignment','?')} |")
        lines.append("")

    if b4:
        lines.append("## B4 actual-coverage breakdown (auto-pipeline)\n")
        lines.append("| actual_id (analyst-idx) | covered | best predicted | score |")
        lines.append("|---|---|---|---|")
        for c in b4.get("actual_coverage", []):
            lines.append(f"| {c.get('actual_id','?')} | "
                         f"{'✓' if c.get('covered') else '·'} | "
                         f"{c.get('best_predicted_candidate_id','—')} | "
                         f"{c.get('match_score_0_to_4','?')} |")
        lines.append("")

        lines.append("## B4 predicted-precision breakdown\n")
        lines.append("| candidate_id | useful | best actual | score |")
        lines.append("|---|---|---|---|")
        for p in b4.get("predicted_precision", []):
            lines.append(f"| {p.get('candidate_id','?')} | "
                         f"{'✓' if p.get('useful') else '·'} | "
                         f"{p.get('best_actual_id','—')} | "
                         f"{p.get('match_score_0_to_4','?')} |")
        lines.append("")

        if b4.get("missed_actual_themes"):
            lines.append("### Missed actual themes\n")
            for t in b4["missed_actual_themes"]:
                lines.append(f"- {t}")
            lines.append("")
        if b4.get("overpredicted_themes"):
            lines.append("### Overpredicted themes\n")
            for t in b4["overpredicted_themes"]:
                lines.append(f"- {t}")
            lines.append("")
        if b4.get("summary"):
            lines.append("### Set-level summary (evaluator)\n")
            lines.append(b4["summary"])
            lines.append("")

    out = os.path.join(REPORTS, "b2_b4_summary.md")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"  wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("b2")
    sub.add_parser("b4")
    sub.add_parser("report")
    args = ap.parse_args()
    if args.cmd == "b2":
        cmd_b2()
    elif args.cmd == "b4":
        cmd_b4()
    elif args.cmd == "report":
        cmd_report()


if __name__ == "__main__":
    main()
