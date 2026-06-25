"""B2_pred computed via the standard B2 evaluator (not B4).

For each (analyst, candidate) pair in K>=5 settings, call the B2 evaluator
with EXACTLY ONE candidate (SIMULATION_JSON.predicted_questions = [the one])
against that analyst's actuals. Returns the full B2 schema per pair:
  match_score_0_to_4, binary_match, topic_match, trigger_alignment,
  question_form_alignment, granularity_alignment, reasoning, miss_or_gap.

Then aggregate per setting and per analyst.

Only runs for K >= 5 settings.

Outputs:
  data_auto/<setting>/b2_pred_via_b2/<analyst>_cand<i>.json   per-pair
  data_auto/<setting>/b2_pred_via_b2_summary.json             per-setting aggregate
  data_auto/b2_pred_via_b2_all.json                            cross-setting summary
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import load_text  # noqa: E402

DATA_AUTO = os.path.join(ROOT, "data_auto")
PROMPTS = os.path.join(ROOT, "prompts")
B2_TPL = load_text(os.path.join(PROMPTS, "b2_eval.md"))


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def b2_call_one_pair(analyst: str, single_candidate: dict, actuals: list[dict], log_to: str) -> dict:
    """Call B2 evaluator with EXACTLY 1 candidate vs analyst's actuals."""
    sim_block = {"analyst_name": analyst, "predicted_questions": [single_candidate]}
    actuals_b2 = [{
        "tuple_id": f"{analyst}-actual-{i}",
        "analyst_name": analyst,
        "call": a.get("call"),
        "question": a.get("question"),
    } for i, a in enumerate(actuals)]
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
        print(f"    ! B2 call failed: {type(e).__name__}: {str(e)[:120]}")
        return stub


def process_cold_setting(label: str, setting_dir: str) -> dict:
    summary = json.load(open(os.path.join(setting_dir, "summary.json")))
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]
    out_dir = os.path.join(setting_dir, "b2_pred_via_b2")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    per_analyst: dict[str, list[dict]] = {}
    all_pair_scores: list[dict] = []

    for name, cell in summary["per_analyst"].items():
        preds = (cell.get("predictions") or {}).get("predicted_questions", [])
        actuals = actuals_by.get(name, [])
        if not preds or not actuals:
            continue
        pair_scores = []
        for i, q in enumerate(preds):
            log_path = os.path.join(log_dir, f"{_safe(name)}_cand{i}.txt")
            ev = b2_call_one_pair(name, q, actuals, log_path)
            score = ev.get("match_score_0_to_4", 0)
            pair_scores.append({
                "candidate_index": i,
                "candidate_text": q.get("question_text", "")[:120],
                "candidate_topic": q.get("topic_label", ""),
                "match_score_0_to_4": score,
                "binary_match": ev.get("binary_match", False),
                "topic_match": ev.get("topic_match"),
                "trigger_alignment": ev.get("trigger_alignment"),
                "question_form_alignment": ev.get("question_form_alignment"),
                "granularity_alignment": ev.get("granularity_alignment"),
                "best_match_actual_tuple_id": ev.get("best_match_actual_tuple_id"),
                "reasoning": (ev.get("reasoning") or "")[:200],
            })
            all_pair_scores.append({"analyst": name, "candidate_index": i, "score": score,
                                     "binary": ev.get("binary_match", False)})
        # Save per-analyst file
        per_analyst[name] = pair_scores
        useful = sum(1 for p in pair_scores if (p["match_score_0_to_4"] or 0) >= 3)
        strong = sum(1 for p in pair_scores if (p["match_score_0_to_4"] or 0) >= 4)
        with open(os.path.join(out_dir, f"{_safe(name)}.json"), "w") as f:
            json.dump({"analyst": name, "K": len(preds),
                        "useful_count": useful, "strong_count": strong,
                        "pair_scores": pair_scores}, f, indent=2)
        print(f"  {name:25s} K={len(preds):>2}  useful>=3={useful}/{len(preds)}  strong>=4={strong}/{len(preds)}")

    # Aggregate
    total = len(all_pair_scores)
    useful = sum(1 for s in all_pair_scores if s["score"] >= 3)
    strong = sum(1 for s in all_pair_scores if s["score"] >= 4)
    avg = sum(s["score"] for s in all_pair_scores) / max(1, total)
    agg = {
        "setting": label, "n_analysts": len(per_analyst), "total_candidates": total,
        "useful_count": useful, "useful_rate": useful / max(1, total),
        "strong_count": strong, "strong_rate": strong / max(1, total),
        "avg_score": avg, "per_analyst": per_analyst,
    }
    with open(os.path.join(setting_dir, "b2_pred_via_b2_summary.json"), "w") as f:
        json.dump(agg, f, indent=2)
    print(f"  {label} aggregate: useful={useful}/{total}={agg['useful_rate']:.3f}  "
          f"strong={strong}/{total}={agg['strong_rate']:.3f}  avg={avg:.3f}\n")
    return agg


def process_conv_setting(label: str, setting_dir: str) -> dict:
    pt = json.load(open(os.path.join(setting_dir, "predictions_by_turn.json")))
    out_dir = os.path.join(setting_dir, "b2_pred_via_b2")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    per_turn = []
    all_pair_scores = []

    for t in pt:
        name = t["analyst"]; idx = t["turn_index"]
        preds = t.get("predicted_questions", [])
        actuals = [{"call": "2026-Q1", "question": t["actual_question"]}]
        if not preds:
            continue
        pair_scores = []
        for i, q in enumerate(preds):
            log_path = os.path.join(log_dir, f"turn{idx:02d}_{_safe(name)}_cand{i}.txt")
            ev = b2_call_one_pair(name, q, actuals, log_path)
            score = ev.get("match_score_0_to_4", 0)
            pair_scores.append({
                "candidate_index": i,
                "candidate_text": q.get("question_text", "")[:120],
                "candidate_topic": q.get("topic_label", ""),
                "match_score_0_to_4": score,
                "binary_match": ev.get("binary_match", False),
                "topic_match": ev.get("topic_match"),
                "trigger_alignment": ev.get("trigger_alignment"),
                "question_form_alignment": ev.get("question_form_alignment"),
                "question_form_alignment": ev.get("question_form_alignment"),
                "granularity_alignment": ev.get("granularity_alignment"),
                "reasoning": (ev.get("reasoning") or "")[:200],
            })
            all_pair_scores.append({"analyst": name, "turn_index": idx, "score": score})
        per_turn.append({"turn_index": idx, "analyst": name, "K": len(preds), "pair_scores": pair_scores})
        useful = sum(1 for p in pair_scores if (p["match_score_0_to_4"] or 0) >= 3)
        strong = sum(1 for p in pair_scores if (p["match_score_0_to_4"] or 0) >= 4)
        print(f"  turn{idx:>2} {name:22s} K={len(preds):>2}  useful>=3={useful}/{len(preds)}  strong>=4={strong}/{len(preds)}")
        with open(os.path.join(out_dir, f"turn{idx:02d}_{_safe(name)}.json"), "w") as f:
            json.dump({"turn_index": idx, "analyst": name, "K": len(preds),
                        "useful_count": useful, "strong_count": strong,
                        "pair_scores": pair_scores}, f, indent=2)

    total = len(all_pair_scores)
    useful = sum(1 for s in all_pair_scores if s["score"] >= 3)
    strong = sum(1 for s in all_pair_scores if s["score"] >= 4)
    avg = sum(s["score"] for s in all_pair_scores) / max(1, total)
    agg = {
        "setting": label, "n_turns": len(per_turn), "total_candidates": total,
        "useful_count": useful, "useful_rate": useful / max(1, total),
        "strong_count": strong, "strong_rate": strong / max(1, total),
        "avg_score": avg, "per_turn": per_turn,
    }
    with open(os.path.join(setting_dir, "b2_pred_via_b2_summary.json"), "w") as f:
        json.dump(agg, f, indent=2)
    print(f"  {label} aggregate: useful={useful}/{total}={agg['useful_rate']:.3f}  "
          f"strong={strong}/{total}={agg['strong_rate']:.3f}  avg={avg:.3f}\n")
    return agg


def main() -> None:
    cold_settings = [
        ("V1 K=5", os.path.join(DATA_AUTO, "final_eval_5q_v1")),
        ("Auto K=5", os.path.join(DATA_AUTO, "final_eval_5q_auto")),
        ("V1 K=10", os.path.join(DATA_AUTO, "final_eval_10q_v1")),
        ("Auto K=10", os.path.join(DATA_AUTO, "final_eval_10q_auto")),
    ]
    conv_settings = [
        ("Conv K=10", os.path.join(DATA_AUTO, "final_eval_conv_10q")),
    ]

    all_results = []
    for label, d in cold_settings:
        print(f"\n=== {label} ===")
        all_results.append(process_cold_setting(label, d))
    for label, d in conv_settings:
        print(f"\n=== {label} ===")
        all_results.append(process_conv_setting(label, d))

    with open(os.path.join(DATA_AUTO, "b2_pred_via_b2_all.json"), "w") as f:
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
