"""Within-twin dedup on Auto K=10 candidates.

Algorithm (per analyst):
  accepted = []
  for cand in candidates (rank 0..9):
    is_dup = False
    for kept in accepted:
      # B2 pair similarity: kept as "actual", cand as "predicted"
      score = B2(predicted=[cand], actuals=[{question: kept.text}])
      if score >= 4:  # "very close substitute" → duplicate
        is_dup = True
        break
    if not is_dup:
      accepted.append(cand)

After dedup, re-run:
  - B2 per-actual (cell-level, 12 cells)
  - B4 set-level (1 call on trimmed pool)
  - Coarse judge per analyst (11 calls)

Writes:
  data_auto/final_eval_10q_auto_dedup/predictions.json
  data_auto/final_eval_10q_auto_dedup/dedup_trace.json
  data_auto/final_eval_10q_auto_dedup/b2_per_actual.json
  data_auto/final_eval_10q_auto_dedup/b4.json
  data_auto/final_eval_10q_auto_dedup/coarse_judge.json
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import (  # noqa: E402
    build_judge_prompt, stub_judgment, load_text,
)

DATA_AUTO = os.path.join(ROOT, "data_auto")
PROMPTS = os.path.join(ROOT, "prompts")
SRC_DIR = os.path.join(DATA_AUTO, "final_eval_10q_auto")
OUT_DIR = os.path.join(DATA_AUTO, "final_eval_10q_auto_dedup")
LOG_DIR = os.path.join(OUT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

B2_TPL = load_text(os.path.join(PROMPTS, "b2_eval.md"))
B4_TPL = load_text(os.path.join(PROMPTS, "b4_eval.md"))
JUDGE_TPL = load_text(os.path.join(PROMPTS, "judge_match.md"))


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def b2_pair_call(analyst: str, cand: dict, kept_text: str, log_to: str) -> dict:
    """B2 pair similarity: treat kept as actual, cand as predicted."""
    sim_block = {"analyst_name": analyst, "predicted_questions": [cand]}
    actuals_b2 = [{
        "tuple_id": f"{analyst}-kept-pair",
        "analyst_name": analyst,
        "call": "pair-similarity",
        "question": kept_text,
    }]
    stub = {"analyst_name": analyst, "match_score_0_to_4": 0, "binary_match": False,
            "topic_match": "none", "trigger_alignment": "none",
            "question_form_alignment": "none", "granularity_alignment": "none",
            "reasoning": "DRY", "miss_or_gap": "DRY"}
    prompt = (B2_TPL
              .replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b2, indent=2)))
    try:
        out = call_llm(prompt, expect_json=True, dry_run_stub=stub, log_to=log_to)
        return parse_json_strict(out)
    except Exception as e:
        print(f"    ! pair B2 failed: {type(e).__name__}: {str(e)[:120]}")
        return stub


def b2_per_actual_call(analyst: str, candidates: list, actual: dict, log_to: str) -> dict:
    """Re-run B2 per (analyst, single actual) with trimmed candidate set."""
    sim_block = {"analyst_name": analyst, "predicted_questions": candidates}
    actuals_b2 = [{
        "tuple_id": f"{analyst}-actual-single",
        "analyst_name": analyst,
        "call": actual.get("call"),
        "question": actual.get("question"),
    }]
    stub = {"analyst_name": analyst, "match_score_0_to_4": 0, "binary_match": False,
            "topic_match": "none", "trigger_alignment": "none",
            "question_form_alignment": "none", "granularity_alignment": "none",
            "reasoning": "DRY", "miss_or_gap": "DRY"}
    prompt = (B2_TPL
              .replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b2, indent=2)))
    try:
        out = call_llm(prompt, expect_json=True, dry_run_stub=stub, log_to=log_to)
        return parse_json_strict(out)
    except Exception as e:
        print(f"    ! per-actual B2 failed: {type(e).__name__}: {str(e)[:120]}")
        return stub


def step1_dedup() -> tuple[dict, dict]:
    """Greedy pairwise dedup. Returns (kept_predictions, trace)."""
    summary = json.load(open(os.path.join(SRC_DIR, "summary.json")))
    kept_predictions: dict[str, dict] = {}  # name -> {analyst, predicted_questions: [...]}
    trace: dict[str, list] = {}  # name -> [{dropped_index, dropped_text, kept_against_index, kept_against_text, score, reasoning}]

    print("=== Step 1: greedy pairwise dedup ===")
    pair_log_dir = os.path.join(LOG_DIR, "dedup_pairs")
    os.makedirs(pair_log_dir, exist_ok=True)

    for name in sorted(summary["per_analyst"].keys()):
        cell = summary["per_analyst"][name]
        preds = (cell.get("predictions") or {}).get("predicted_questions", [])
        if not preds:
            kept_predictions[name] = {"analyst": name, "predicted_questions": []}
            trace[name] = []
            continue

        accepted: list[tuple[int, dict]] = []  # (original_rank, candidate_dict)
        analyst_trace: list[dict] = []
        for i, cand in enumerate(preds):
            is_dup = False
            for kept_rank, kept_cand in accepted:
                log_path = os.path.join(pair_log_dir, f"{_safe(name)}_c{i}_vs_c{kept_rank}.txt")
                ev = b2_pair_call(name, cand, kept_cand.get("question_text", ""), log_path)
                score = ev.get("match_score_0_to_4", 0) or 0
                if score >= 4:
                    analyst_trace.append({
                        "dropped_rank": i,
                        "dropped_text": cand.get("question_text", "")[:200],
                        "kept_against_rank": kept_rank,
                        "kept_against_text": kept_cand.get("question_text", "")[:200],
                        "pair_score": score,
                        "reasoning": (ev.get("reasoning") or "")[:300],
                    })
                    is_dup = True
                    break
            if not is_dup:
                accepted.append((i, cand))
        kept_predictions[name] = {
            "analyst": name,
            "predicted_questions": [c for _, c in accepted],
            "kept_ranks": [r for r, _ in accepted],
        }
        trace[name] = analyst_trace
        print(f"  {name:25s}  10 → {len(accepted)} kept ({len(analyst_trace)} dropped)")

    # Persist
    with open(os.path.join(OUT_DIR, "predictions.json"), "w") as f:
        json.dump(kept_predictions, f, indent=2)
    with open(os.path.join(OUT_DIR, "dedup_trace.json"), "w") as f:
        json.dump(trace, f, indent=2)

    total_kept = sum(len(v["predicted_questions"]) for v in kept_predictions.values())
    total_dropped = sum(len(v) for v in trace.values())
    print(f"\n  total pool: 110 → {total_kept} ({total_dropped} dropped)")
    return kept_predictions, trace


def step2_b2_per_actual(kept_predictions: dict) -> dict:
    print("\n=== Step 2: B2 per-actual on trimmed pool ===")
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]
    log_dir = os.path.join(LOG_DIR, "b2_per_actual")
    os.makedirs(log_dir, exist_ok=True)

    cells = []
    for name in sorted(actuals_by.keys()):
        actuals = actuals_by.get(name, [])
        kept = kept_predictions.get(name, {}).get("predicted_questions", [])
        if not actuals or not kept:
            continue
        for i, a in enumerate(actuals):
            log_path = os.path.join(log_dir, f"{_safe(name)}_a{i}.txt")
            ev = b2_per_actual_call(name, kept, a, log_path)
            if name == "robin farley":
                ev["robin_actual_index"] = i
            ev["analyst_name"] = name
            cells.append(ev)
            print(f"  {name:25s} a{i}  score={ev.get('match_score_0_to_4', 0)}  binary={ev.get('binary_match')}")

    n = len(cells)
    bin_ = sum(1 for c in cells if c.get("binary_match"))
    strong = sum(1 for c in cells if (c.get("match_score_0_to_4") or 0) >= 4)
    avg = sum(c.get("match_score_0_to_4", 0) for c in cells) / max(1, n)
    agg = {
        "evaluated_count": n,
        "binary_match_count": bin_,
        "binary_match_rate": bin_ / max(1, n),
        "strong_match_count": strong,
        "strong_match_rate": strong / max(1, n),
        "average_match_score_0_to_4": avg,
        "cells": cells,
    }
    with open(os.path.join(OUT_DIR, "b2_per_actual.json"), "w") as f:
        json.dump(agg, f, indent=2)
    print(f"\n  B2 per-actual: bin>=3 {bin_}/{n}={agg['binary_match_rate']:.3f}  "
          f"strong>=4 {strong}/{n}={agg['strong_match_rate']:.3f}  avg={avg:.3f}")
    return agg


def step3_b4_set(kept_predictions: dict) -> dict:
    print("\n=== Step 3: B4 set-level on trimmed pool ===")
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]
    predicted, actuals = [], []
    for name in sorted(actuals_by.keys()):
        kept = kept_predictions.get(name, {}).get("predicted_questions", [])
        for i, q in enumerate(kept):
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

    prompt = (B4_TPL
              .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(predicted, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
    stub = {"actual_question_count": len(actuals),
            "predicted_question_count": len(predicted),
            "actual_coverage": [], "predicted_precision": [],
            "set_metrics": {"coverage_count": 0, "coverage_rate": 0,
                             "useful_prediction_count": 0, "precision_rate": 0,
                             "average_actual_best_score": 0,
                             "average_predicted_best_score": 0},
            "missed_actual_themes": [], "overpredicted_themes": [], "summary": "DRY"}
    try:
        out = call_llm(prompt, expect_json=True, dry_run_stub=stub,
                       log_to=os.path.join(LOG_DIR, "b4_set_level.txt"))
        b4 = parse_json_strict(out)
    except Exception as e:
        print(f"  ! B4 failed: {type(e).__name__}: {str(e)[:120]}")
        b4 = stub
    with open(os.path.join(OUT_DIR, "b4.json"), "w") as f:
        json.dump(b4, f, indent=2)
    m = b4.get("set_metrics", {})
    print(f"  B4: cov={m.get('coverage_count')}/{b4['actual_question_count']}={m.get('coverage_rate', 0):.3f}  "
          f"prec={m.get('useful_prediction_count')}/{b4['predicted_question_count']}={m.get('precision_rate', 0):.3f}  "
          f"avg_act={m.get('average_actual_best_score', 0):.3f}  avg_pred={m.get('average_predicted_best_score', 0):.3f}")

    ac = b4.get("actual_coverage", [])
    cov_strong = sum(1 for c in ac if (c.get("match_score_0_to_4") or 0) >= 4)
    pp = b4.get("predicted_precision", [])
    prec_strong = sum(1 for c in pp if (c.get("match_score_0_to_4") or 0) >= 4)
    print(f"  B4 strong: cov_strong>=4={cov_strong}/{b4['actual_question_count']}  "
          f"prec_strong>=4={prec_strong}/{b4['predicted_question_count']}")

    # Identity-matched
    id_same = 0
    for c in ac:
        if not c.get("covered"):
            continue
        aid = c.get("actual_id", "") or ""
        bpi = c.get("best_predicted_candidate_id", "") or ""
        if aid.rsplit("-actual-", 1)[0] == bpi.rsplit("-pred-", 1)[0]:
            id_same += 1
    print(f"  identity-matched: {id_same}/{b4['actual_question_count']} = {id_same/max(1, b4['actual_question_count']):.3f}")
    return b4


def step4_coarse_judge(kept_predictions: dict) -> dict:
    print("\n=== Step 4: Coarse judge per analyst on trimmed pool ===")
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]
    log_dir = os.path.join(LOG_DIR, "coarse_judge")
    os.makedirs(log_dir, exist_ok=True)

    per_analyst = {}
    total_a = total_e = total_p = total_m = 0
    for name in sorted(actuals_by.keys()):
        actuals = actuals_by.get(name, [])
        kept = kept_predictions.get(name, {}).get("predicted_questions", [])
        if not actuals or not kept:
            continue
        judge_prompt = build_judge_prompt(JUDGE_TPL, name, kept, actuals)
        try:
            out = call_llm(judge_prompt, expect_json=True,
                           dry_run_stub=stub_judgment(name, actuals, kept),
                           log_to=os.path.join(log_dir, f"{_safe(name)}.txt"))
            judgment = parse_json_strict(out)
        except Exception as e:
            print(f"  ! {name} judge failed: {type(e).__name__}")
            judgment = stub_judgment(name, actuals, kept)
        s = judgment["summary"]
        total_a += s["n_actual"]; total_e += s["n_exact"]
        total_p += s["n_partial"]; total_m += s["n_miss"]
        per_analyst[name] = judgment
        print(f"  {name:25s} ex={s['n_exact']} pa={s['n_partial']} ms={s['n_miss']} / {s['n_actual']}")

    hit_rate = (total_e + total_p) / total_a if total_a else 0
    out = {
        "per_analyst": per_analyst,
        "n_actual": total_a, "n_exact": total_e, "n_partial": total_p, "n_miss": total_m,
        "hit_rate_exact_or_partial": hit_rate,
    }
    with open(os.path.join(OUT_DIR, "coarse_judge.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"  coarse: ex={total_e} pa={total_p} ms={total_m} / {total_a}  hit={hit_rate:.3f}")
    return out


def main() -> None:
    kept, trace = step1_dedup()
    b2 = step2_b2_per_actual(kept)
    b4 = step3_b4_set(kept)
    coarse = step4_coarse_judge(kept)
    print("\n=== DONE ===")
    print(f"  trimmed pool: {sum(len(v['predicted_questions']) for v in kept.values())} candidates")
    print(f"  coarse hit: {coarse['hit_rate_exact_or_partial']:.3f}")
    print(f"  B2 per-actual binary: {b2['binary_match_rate']:.3f}  strong: {b2['strong_match_rate']:.3f}")
    m = b4.get("set_metrics", {})
    print(f"  B4 cov: {m.get('coverage_rate', 0):.3f}  prec: {m.get('precision_rate', 0):.3f}")


if __name__ == "__main__":
    main()
