"""B2_pred = within-analyst candidate-level precision.

For each analyst, call B4-style evaluator restricted to (this analyst's K
candidates, this analyst's actuals). The evaluator returns one score per
candidate (predicted_precision[]). Aggregate over all analysts:

  - useful_count      = candidates with score >= 3 (across all analysts)
  - strong_count      = candidates with score >= 4
  - rates / total candidates
  - per-analyst breakdown

This measures: of each digital twin's K predictions, how many are
substantively useful for predicting THAT analyst's actuals. Different from
B4 precision (which allows cross-analyst matches) and from B2 binary
(which only scores the BEST candidate per analyst).
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import load_text  # noqa: E402

DATA_AUTO = os.path.join(ROOT, "data_auto")
PROMPTS = os.path.join(ROOT, "prompts")
B4_TPL = load_text(os.path.join(PROMPTS, "b4_eval.md"))


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def b2_pred_for_analyst(analyst: str, predictions: list, actuals: list, log_to: str) -> dict:
    """Use B4 evaluator with within-analyst inputs; returns predicted_precision[]."""
    predicted_set = [
        {"candidate_id": f"{_safe(analyst)}-pred-{i}", "source_analyst": analyst,
         "question": q.get("question_text", "")}
        for i, q in enumerate(predictions)
    ]
    actual_set = [
        {"actual_id": f"{_safe(analyst)}-actual-{i}", "source_analyst": analyst,
         "question": a.get("question", "")}
        for i, a in enumerate(actuals)
    ]
    prompt = (B4_TPL
              .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(predicted_set, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actual_set, indent=2)))
    stub = {"actual_question_count": len(actual_set),
            "predicted_question_count": len(predicted_set),
            "actual_coverage": [], "predicted_precision": [],
            "set_metrics": {"coverage_count": 0, "coverage_rate": 0,
                             "useful_prediction_count": 0, "precision_rate": 0,
                             "average_actual_best_score": 0,
                             "average_predicted_best_score": 0},
            "missed_actual_themes": [], "overpredicted_themes": [], "summary": "DRY"}
    try:
        out = call_llm(prompt, expect_json=True, dry_run_stub=stub, log_to=log_to)
        return parse_json_strict(out)
    except Exception as e:
        print(f"  ! B2_pred call failed for {analyst}: {type(e).__name__}: {str(e)[:150]}")
        return stub


def collect_setting(label: str, setting_dir: str) -> dict:
    """Return per-analyst B2_pred + aggregate for one cold setting."""
    summary = json.load(open(os.path.join(setting_dir, "summary.json")))
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]
    log_dir = os.path.join(setting_dir, "b2_pred_logs")
    os.makedirs(log_dir, exist_ok=True)

    per_analyst: dict[str, dict] = {}
    all_scores: list[dict] = []  # flat list of all candidate scores

    for name, cell in summary["per_analyst"].items():
        preds = (cell.get("predictions") or {}).get("predicted_questions", [])
        actuals = actuals_by.get(name, [])
        if not preds or not actuals:
            continue
        log_path = os.path.join(log_dir, f"{_safe(name)}.txt")
        b4_within = b2_pred_for_analyst(name, preds, actuals, log_path)
        pp = b4_within.get("predicted_precision", [])
        per_analyst[name] = {
            "K": len(preds),
            "n_actuals": len(actuals),
            "predicted_precision": pp,
        }
        for p in pp:
            all_scores.append({"analyst": name, "candidate_id": p.get("candidate_id"),
                                "match_score_0_to_4": p.get("match_score_0_to_4", 0),
                                "useful": p.get("useful", False)})
        useful = sum(1 for p in pp if p.get("useful"))
        strong = sum(1 for p in pp if (p.get("match_score_0_to_4") or 0) >= 4)
        print(f"  {name:25s} K={len(preds):>2}  useful>=3={useful}/{len(pp)}  strong>=4={strong}/{len(pp)}")

    # Aggregate
    total = len(all_scores)
    useful = sum(1 for s in all_scores if s["useful"])
    strong = sum(1 for s in all_scores if s["match_score_0_to_4"] >= 4)
    avg = sum(s["match_score_0_to_4"] for s in all_scores) / max(1, total)
    agg = {
        "setting": label,
        "n_analysts": len(per_analyst),
        "total_candidates": total,
        "useful_count": useful,
        "useful_rate": useful / max(1, total),
        "strong_count": strong,
        "strong_rate": strong / max(1, total),
        "avg_score": avg,
        "per_analyst": per_analyst,
    }
    out_path = os.path.join(setting_dir, "b2_pred.json")
    with open(out_path, "w") as f:
        json.dump(agg, f, indent=2)
    print(f"  {label} aggregate: useful={useful}/{total}={agg['useful_rate']:.3f}  "
          f"strong={strong}/{total}={agg['strong_rate']:.3f}  avg={avg:.3f}")
    print(f"  wrote {out_path}\n")
    return agg


def collect_conv(label: str, setting_dir: str) -> dict:
    """For conv settings, treat each turn's (predictions, single actual) as
    its own within-analyst-within-turn B2_pred input."""
    pt_path = os.path.join(setting_dir, "predictions_by_turn.json")
    pt = json.load(open(pt_path))
    log_dir = os.path.join(setting_dir, "b2_pred_logs")
    os.makedirs(log_dir, exist_ok=True)

    per_turn = []
    all_scores = []
    for t in pt:
        name = t["analyst"]; idx = t["turn_index"]
        preds = t.get("predicted_questions", [])
        actuals = [{"question": t["actual_question"]}]
        if not preds:
            continue
        log_path = os.path.join(log_dir, f"turn{idx:02d}_{_safe(name)}.txt")
        b4_within = b2_pred_for_analyst(name, preds, actuals, log_path)
        pp = b4_within.get("predicted_precision", [])
        per_turn.append({
            "turn_index": idx, "analyst": name, "K": len(preds),
            "predicted_precision": pp,
        })
        for p in pp:
            all_scores.append({"analyst": name, "turn_index": idx,
                                "candidate_id": p.get("candidate_id"),
                                "match_score_0_to_4": p.get("match_score_0_to_4", 0),
                                "useful": p.get("useful", False)})
        useful = sum(1 for p in pp if p.get("useful"))
        strong = sum(1 for p in pp if (p.get("match_score_0_to_4") or 0) >= 4)
        print(f"  turn{idx:>2} {name:22s} K={len(preds):>2}  useful>=3={useful}/{len(pp)}  strong>=4={strong}/{len(pp)}")

    total = len(all_scores)
    useful = sum(1 for s in all_scores if s["useful"])
    strong = sum(1 for s in all_scores if s["match_score_0_to_4"] >= 4)
    avg = sum(s["match_score_0_to_4"] for s in all_scores) / max(1, total)
    agg = {
        "setting": label, "n_turns": len(per_turn), "total_candidates": total,
        "useful_count": useful, "useful_rate": useful / max(1, total),
        "strong_count": strong, "strong_rate": strong / max(1, total),
        "avg_score": avg, "per_turn": per_turn,
    }
    out_path = os.path.join(setting_dir, "b2_pred.json")
    with open(out_path, "w") as f:
        json.dump(agg, f, indent=2)
    print(f"  {label} aggregate: useful={useful}/{total}={agg['useful_rate']:.3f}  "
          f"strong={strong}/{total}={agg['strong_rate']:.3f}  avg={avg:.3f}")
    print(f"  wrote {out_path}\n")
    return agg


def main() -> None:
    cold_settings = [
        ("Auto K=1", os.path.join(DATA_AUTO, "final_eval_1q")),
        ("V1 K=5", os.path.join(DATA_AUTO, "final_eval_5q_v1")),
        ("Auto K=5", os.path.join(DATA_AUTO, "final_eval_5q_auto")),
        ("V1 K=10", os.path.join(DATA_AUTO, "final_eval_10q_v1")),
        ("Auto K=10", os.path.join(DATA_AUTO, "final_eval_10q_auto")),
    ]
    conv_settings = [
        ("Conv K=1", os.path.join(DATA_AUTO, "final_eval_conv")),
        ("Conv K=10", os.path.join(DATA_AUTO, "final_eval_conv_10q")),
    ]

    all_results = []
    for label, d in cold_settings:
        print(f"\n=== {label} ===")
        all_results.append(collect_setting(label, d))
    for label, d in conv_settings:
        print(f"\n=== {label} ===")
        all_results.append(collect_conv(label, d))

    with open(os.path.join(DATA_AUTO, "b2_pred_all.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    print("\n=== SUMMARY ===")
    print(f"{'setting':12s} {'cands':>6s} {'useful>=3':>14s} {'strong>=4':>14s} {'avg':>6s}")
    for r in all_results:
        print(f"{r['setting']:12s} {r['total_candidates']:>6} "
              f"{r['useful_count']:>3}/{r['total_candidates']:<3}={r['useful_rate']:.3f}   "
              f"{r['strong_count']:>3}/{r['total_candidates']:<3}={r['strong_rate']:.3f}   "
              f"{r['avg_score']:>6.3f}")


if __name__ == "__main__":
    main()
