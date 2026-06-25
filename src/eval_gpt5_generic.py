"""Generic gpt-5 B2 (per-actual, 12 cells with Robin split) + B4 (set-level)
evaluator over any summary.json that has per_analyst.predictions.predicted_questions.

Subcommands:
  b2       — per-actual B2 with Robin split, 12 cells, gpt-5
  b4       — set-level B4, 1 call, gpt-5
  pool     — dump raw candidate pool to raw_pool.json (no LLM)
  all      — pool + b2 + b4

Required args: --in-summary <path> --out-dir <path>

Outputs (under <out-dir>):
  raw_pool.json
  b2_per_actual.json + b2_summary.json + b2_logs/
  b4.json + b4_logs/
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
TEST_JSON = os.path.join(DATA_AUTO, "test.json")
B2_PROMPT_PATH = os.path.join(PROMPTS, "b2_eval.md")
B4_PROMPT_PATH = os.path.join(PROMPTS, "b4_eval.md")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]
COLD_START = ["xian siew", "kevin kopelman"]
ALL_11 = TEST_RETURNING + COLD_START
MODEL = os.environ.get("EVAL_MODEL", "gpt-5")


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def _b2_stub(name: str) -> dict:
    return {"analyst_name": name, "match_score_0_to_4": 0, "binary_match": False,
            "topic_match": "none", "trigger_alignment": "none",
            "question_form_alignment": "none", "granularity_alignment": "none",
            "reasoning": "DRY", "miss_or_gap": "DRY"}


def b2_for_one(analyst: str, predicted_questions: list, actual: dict,
               log_to: str, tpl: str) -> dict:
    sim_block = {"analyst_name": analyst, "predicted_questions": predicted_questions}
    actuals_b2 = [{
        "tuple_id": f"{analyst}-actual-single",
        "analyst_name": analyst,
        "call": actual.get("call"),
        "question": actual.get("question"),
    }]
    prompt = (tpl
              .replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b2, indent=2)))
    try:
        out = call_llm(prompt, model=MODEL, expect_json=True,
                       dry_run_stub=_b2_stub(analyst), log_to=log_to)
        ev = parse_json_strict(out)
    except Exception as e:
        print(f"  ! B2 failed for {analyst}: {type(e).__name__}: {str(e)[:150]}")
        ev = _b2_stub(analyst)
    ev["analyst_name"] = analyst
    return ev


def load_inputs(in_summary: str) -> tuple[dict, dict]:
    summary = json.load(open(in_summary))
    test = json.load(open(TEST_JSON))
    return summary, test


def cmd_pool(in_summary: str, out_dir: str) -> None:
    summary, test = load_inputs(in_summary)
    actuals_by = test["per_analyst_actual_questions"]
    pool = {"predicted": [], "actual": []}
    for name in ALL_11:
        pa = summary.get("per_analyst", {}).get(name) or {}
        for i, q in enumerate((pa.get("predictions") or {}).get("predicted_questions", [])):
            pool["predicted"].append({
                "candidate_id": f"{_safe(name)}-pred-{i}",
                "source_analyst": name,
                "question": q.get("question_text", ""),
                "topic_label": q.get("topic_label", ""),
            })
        for i, a in enumerate(actuals_by.get(name, [])):
            pool["actual"].append({
                "actual_id": f"{_safe(name)}-actual-{i}",
                "source_analyst": name,
                "question": a.get("question", ""),
            })
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "raw_pool.json"), "w") as f:
        json.dump(pool, f, indent=2)
    print(f"pool: predicted={len(pool['predicted'])} actuals={len(pool['actual'])}")


def cmd_b2(in_summary: str, out_dir: str) -> None:
    summary, test = load_inputs(in_summary)
    actuals_by = test["per_analyst_actual_questions"]
    tpl = open(B2_PROMPT_PATH).read()
    log_dir = os.path.join(out_dir, "b2_logs")
    os.makedirs(log_dir, exist_ok=True)

    cells = []
    print(f"=== B2 per-actual ({MODEL}) ===")
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals:
            continue
        pa = summary.get("per_analyst", {}).get(name) or {}
        preds = (pa.get("predictions") or {}).get("predicted_questions", [])
        if not preds:
            print(f"  ! {name}: no predictions; skip")
            continue
        if name == "robin farley":
            # Split into 2 cells
            for i, a in enumerate(actuals):
                ev = b2_for_one(name, preds, a,
                                log_to=os.path.join(log_dir, f"b2_{_safe(name)}_actual{i}.txt"),
                                tpl=tpl)
                ev["robin_actual_index"] = i
                cells.append(ev)
                print(f"  {name} Q{i}: score={ev.get('match_score_0_to_4')} binary={ev.get('binary_match')}")
        else:
            ev = b2_for_one(name, preds, actuals[0],
                            log_to=os.path.join(log_dir, f"b2_{_safe(name)}.txt"),
                            tpl=tpl)
            cells.append(ev)
            print(f"  {name:25s} score={ev.get('match_score_0_to_4')} binary={ev.get('binary_match')}")

    scored = [c for c in cells if isinstance(c.get("match_score_0_to_4"), (int, float))]
    n = len(scored)
    binary = sum(1 for c in scored if c.get("binary_match"))
    strong = sum(1 for c in scored if (c.get("match_score_0_to_4") or 0) >= 4)
    avg = sum(c["match_score_0_to_4"] for c in scored) / max(1, n) if scored else 0
    agg = {
        "evaluator_model": MODEL,
        "evaluated_count": n,
        "binary_match_count": binary,
        "binary_match_rate": binary / max(1, n),
        "strong_match_count": strong,
        "strong_match_rate": strong / max(1, n),
        "average_match_score_0_to_4": avg,
    }
    with open(os.path.join(out_dir, "b2_per_actual.json"), "w") as f:
        json.dump({"summary": agg, "cells": cells}, f, indent=2)
    with open(os.path.join(out_dir, "b2_summary.json"), "w") as f:
        json.dump(agg, f, indent=2)
    print(f"\nB2 aggregate: n={n} binary={binary} ({binary/max(1,n):.3f}) "
          f"strong={strong} ({strong/max(1,n):.3f}) avg={avg:.3f}")


def cmd_b4(in_summary: str, out_dir: str) -> None:
    pool_path = os.path.join(out_dir, "raw_pool.json")
    if not os.path.exists(pool_path):
        cmd_pool(in_summary, out_dir)
    pool = json.load(open(pool_path))
    predicted = pool["predicted"]
    actuals = pool["actual"]
    print(f"=== B4 set-level ({MODEL}): predicted={len(predicted)} actuals={len(actuals)} ===")
    tpl = open(B4_PROMPT_PATH).read()
    prompt = (tpl
              .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(predicted, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
    log_dir = os.path.join(out_dir, "b4_logs")
    os.makedirs(log_dir, exist_ok=True)
    log = os.path.join(log_dir, "b4_prompt.txt")
    out = call_llm(prompt, model=MODEL, expect_json=True, log_to=log)
    ev = parse_json_strict(out)

    # Augment with derived metrics
    pred_by_id = {p["candidate_id"]: p for p in predicted}
    act_by_id = {a["actual_id"]: a for a in actuals}
    id_match = 0
    cov_strong = 0
    for c in ev.get("actual_coverage", []):
        if (c.get("match_score_0_to_4") or 0) >= 4:
            cov_strong += 1
        if not c.get("covered"):
            continue
        bp = c.get("best_predicted_candidate_id")
        aid = c.get("actual_id")
        if bp and aid and pred_by_id.get(bp, {}).get("source_analyst") == act_by_id.get(aid, {}).get("source_analyst"):
            id_match += 1
    prec_strong = sum(1 for p in ev.get("predicted_precision", [])
                      if (p.get("match_score_0_to_4") or 0) >= 4)
    ev["derived"] = {
        "evaluator_model": MODEL,
        "identity_matched_coverage": id_match,
        "coverage_strong_count": cov_strong,
        "precision_strong_count": prec_strong,
    }
    with open(os.path.join(out_dir, "b4.json"), "w") as f:
        json.dump(ev, f, indent=2)
    m = ev.get("set_metrics", {})
    print(f"  coverage:  {m.get('coverage_count')}/{ev.get('actual_question_count')} = {m.get('coverage_rate')}")
    print(f"  precision: {m.get('useful_prediction_count')}/{ev.get('predicted_question_count')} = {m.get('precision_rate')}")
    print(f"  strong cov: {cov_strong}/{ev.get('actual_question_count')}; "
          f"strong prec: {prec_strong}/{ev.get('predicted_question_count')}; "
          f"id-matched: {id_match}/{ev.get('actual_question_count')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("pool", "b2", "b4", "all"):
        s = sub.add_parser(c)
        s.add_argument("--in-summary", required=True)
        s.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    if args.cmd == "pool":
        cmd_pool(args.in_summary, args.out_dir)
    elif args.cmd == "b2":
        cmd_b2(args.in_summary, args.out_dir)
    elif args.cmd == "b4":
        cmd_b4(args.in_summary, args.out_dir)
    elif args.cmd == "all":
        cmd_pool(args.in_summary, args.out_dir)
        cmd_b2(args.in_summary, args.out_dir)
        cmd_b4(args.in_summary, args.out_dir)


if __name__ == "__main__":
    main()
