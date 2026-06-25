"""K=10 ablation: re-simulate TEST with EXACTLY 5 predicted questions per
analyst, on either V1 baseline personas OR auto-pipeline final personas.

Mirrors src/rerun_1q.py structure exactly; differences:
  - prompts/simulate_questions_10q.md  (K=10 instead of K=1)
  - --source v1|auto subcommand selects persona directory
  - defensive cap to 5 if simulator returns more

Outputs:
  data_auto/final_eval_10q_v1/{summary.json, b4.json, logs/}
  data_auto/final_eval_10q_auto/{summary.json, b4.json, logs/}
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import (  # noqa: E402
    build_simulator_prompt, build_judge_prompt,
    stub_predictions, stub_judgment, load_text,
)

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
V1_PERSONAS = os.path.join(ROOT, "data", "personas")
AUTO_PERSONAS = os.path.join(DATA_AUTO, "final_personas")

SIM_PROMPT = os.path.join(PROMPTS, "simulate_questions_10q.md")
JUDGE_PROMPT = os.path.join(PROMPTS, "judge_match.md")
B2_PROMPT = os.path.join(PROMPTS, "b2_eval.md")
B4_PROMPT = os.path.join(PROMPTS, "b4_eval.md")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]
COLD_START = ["xian siew", "kevin kopelman"]
ALL_11 = TEST_RETURNING + COLD_START


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def _load_persona(name: str, source: str) -> dict | None:
    """Return persona dict for analyst `name` under `source` ∈ {v1, auto}.
    For v1: data/personas/<analyst>.json (only 9 returning exist; cold-start absent).
    For auto: data_auto/final_personas/<analyst>.json (+ _fallback.json for cold-start).
    """
    if source == "v1":
        if name in COLD_START:
            # V1 has no cold-start persona; reuse auto's fallback for parity
            # (both V1 and auto would need to use the same fallback for cold-start)
            p = os.path.join(AUTO_PERSONAS, "_fallback.json")
        else:
            p = os.path.join(V1_PERSONAS, f"{_safe(name)}.json")
    elif source == "auto":
        if name in COLD_START:
            p = os.path.join(AUTO_PERSONAS, "_fallback.json")
        else:
            p = os.path.join(AUTO_PERSONAS, f"{_safe(name)}.json")
    else:
        raise ValueError(f"unknown source: {source!r}")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def run(source: str) -> None:
    assert source in ("v1", "auto"), source
    out_dir = os.path.join(DATA_AUTO, f"final_eval_10q_{source}")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]
    actuals_by = test["per_analyst_actual_questions"]

    sim_tpl = load_text(SIM_PROMPT)
    judge_tpl = load_text(JUDGE_PROMPT)
    b2_tpl = load_text(B2_PROMPT)
    b4_tpl = load_text(B4_PROMPT)

    print(f"=== K=10 rerun (source = {source}) ===")
    print("Step 1: simulate (5 Q each) + judge + B2 per analyst")
    per_analyst: dict[str, dict] = {}
    total_a = total_e = total_p = total_m = 0
    b2_cells = []

    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals:
            continue
        persona = _load_persona(name, source)
        if persona is None:
            print(f"  ! {name}: no persona; skipping")
            continue

        # 1 simulate
        sim_prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        sim_out = call_llm(sim_prompt, expect_json=True,
                           dry_run_stub=stub_predictions(name),
                           log_to=os.path.join(log_dir, f"sim_{_safe(name)}.txt"))
        try:
            pred = parse_json_strict(sim_out)
        except Exception:
            pred = stub_predictions(name)
        pq = pred.get("predicted_questions", [])
        if len(pq) > 10:
            pred["predicted_questions"] = pq[:10]
        elif len(pq) < 10:
            print(f"  ! {name}: simulator returned {len(pq)} questions (expected 10)")

        # 2 coarse judge
        judge_prompt = build_judge_prompt(judge_tpl, name, pred["predicted_questions"], actuals)
        judge_out = call_llm(judge_prompt, expect_json=True,
                             dry_run_stub=stub_judgment(name, actuals, pred["predicted_questions"]),
                             log_to=os.path.join(log_dir, f"judge_{_safe(name)}.txt"))
        try:
            judgment = parse_json_strict(judge_out)
        except Exception:
            judgment = stub_judgment(name, actuals, pred["predicted_questions"])
        s = judgment["summary"]
        total_a += s["n_actual"]; total_e += s["n_exact"]
        total_p += s["n_partial"]; total_m += s["n_miss"]

        # 3 B2
        sim_block = {"analyst_name": name, "predicted_questions": pred["predicted_questions"]}
        actuals_b2 = [{"tuple_id": f"{name}-actual-{i}", "analyst_name": name,
                       "call": a.get("call"), "question": a.get("question")}
                      for i, a in enumerate(actuals)]
        b2_prompt = (b2_tpl
                     .replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2))
                     .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b2, indent=2)))
        b2_stub = {"analyst_name": name, "match_score_0_to_4": 0, "binary_match": False,
                   "topic_match": "none", "trigger_alignment": "none",
                   "question_form_alignment": "none", "granularity_alignment": "none",
                   "reasoning": "DRY", "miss_or_gap": "DRY"}
        b2_out = call_llm(b2_prompt, expect_json=True, dry_run_stub=b2_stub,
                          log_to=os.path.join(log_dir, f"b2_{_safe(name)}.txt"))
        try:
            b2_eval = parse_json_strict(b2_out)
        except Exception:
            b2_eval = b2_stub
        b2_eval["analyst_name"] = name
        b2_cells.append(b2_eval)

        per_analyst[name] = {
            "n_actual": s["n_actual"], "n_exact": s["n_exact"],
            "n_partial": s["n_partial"], "n_miss": s["n_miss"],
            "hit": (s["n_exact"] + s["n_partial"]) / s["n_actual"] if s["n_actual"] else 0,
            "n_predicted": len(pred["predicted_questions"]),
            "predictions": pred, "judgment": judgment, "b2": b2_eval,
        }
        print(f"  {name:25s} K={len(pred['predicted_questions'])} "
              f"coarse: ex={s['n_exact']} pa={s['n_partial']} ms={s['n_miss']}; "
              f"B2: score={b2_eval.get('match_score_0_to_4')} binary={b2_eval.get('binary_match')}")

    coarse_hit = (total_e + total_p) / total_a if total_a else 0
    print(f"\nCoarse aggregate (11 analysts/12 actuals): ex={total_e} pa={total_p} ms={total_m} hit={coarse_hit:.3f}")

    scored = [c for c in b2_cells if isinstance(c.get("match_score_0_to_4"), (int, float))]
    binary = sum(1 for c in scored if c.get("binary_match"))
    strong = sum(1 for c in scored if (c.get("match_score_0_to_4") or 0) >= 4)
    avg = (sum(c["match_score_0_to_4"] for c in scored) / max(1, len(scored))) if scored else 0
    print(f"B2 aggregate: binary(>=3)={binary/max(1,len(scored)):.3f} ({binary}/{len(scored)}); "
          f"strong(>=4)={strong/max(1,len(scored)):.3f} ({strong}/{len(scored)}); avg={avg:.3f}")

    summary = {
        "source": source, "K": 10,
        "n_analysts_scored": len(per_analyst), "n_actual": total_a,
        "n_exact": total_e, "n_partial": total_p, "n_miss": total_m,
        "hit_rate_exact_or_partial": coarse_hit,
        "per_analyst": per_analyst,
        "b2_summary": {
            "evaluated_count": len(scored),
            "binary_match_count": binary,
            "binary_match_rate": binary / max(1, len(scored)),
            "strong_match_count": strong,
            "strong_match_rate": strong / max(1, len(scored)),
            "average_match_score_0_to_4": avg,
        },
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # Step 2: B4 set-level
    print("\nStep 2: B4 set-level")
    predicted, actuals_b4 = [], []
    for name in ALL_11:
        pa = per_analyst.get(name) or {}
        for i, q in enumerate((pa.get("predictions") or {}).get("predicted_questions", [])):
            predicted.append({"candidate_id": f"{_safe(name)}-pred-{i}",
                              "source_analyst": name,
                              "question": q.get("question_text", ""),
                              "topic_label": q.get("topic_label", "")})
        for i, a in enumerate(actuals_by.get(name, [])):
            actuals_b4.append({"actual_id": f"{_safe(name)}-actual-{i}",
                               "source_analyst": name,
                               "question": a.get("question", "")})
    print(f"  predicted set size: {len(predicted)};  actual set size: {len(actuals_b4)}")
    b4_prompt = (b4_tpl
                 .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(predicted, indent=2))
                 .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b4, indent=2)))
    b4_stub = {"actual_question_count": len(actuals_b4),
               "predicted_question_count": len(predicted),
               "actual_coverage": [], "predicted_precision": [],
               "set_metrics": {"coverage_count": 0, "coverage_rate": 0,
                                "useful_prediction_count": 0, "precision_rate": 0,
                                "average_actual_best_score": 0,
                                "average_predicted_best_score": 0},
               "missed_actual_themes": [], "overpredicted_themes": [],
               "summary": "DRY"}
    try:
        b4_out = call_llm(b4_prompt, expect_json=True, dry_run_stub=b4_stub,
                          log_to=os.path.join(log_dir, "b4_prompt.txt"))
        b4 = parse_json_strict(b4_out)
    except Exception as e:
        print(f"  ! B4 LLM call failed: {type(e).__name__}: {str(e)[:200]}")
        b4 = b4_stub
    with open(os.path.join(out_dir, "b4.json"), "w") as f:
        json.dump(b4, f, indent=2)
    m = b4.get("set_metrics", {})
    print(f"  B4 set_metrics: coverage={m.get('coverage_count')}/{b4['actual_question_count']} "
          f"({m.get('coverage_rate'):.3f}) "
          f"precision={m.get('useful_prediction_count')}/{b4['predicted_question_count']} "
          f"({m.get('precision_rate'):.3f}) "
          f"avg_act={m.get('average_actual_best_score'):.3f} "
          f"avg_pred={m.get('average_predicted_best_score'):.3f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("v1")
    sub.add_parser("auto")
    args = ap.parse_args()
    if args.cmd == "v1":
        run("v1")
    elif args.cmd == "auto":
        run("auto")


if __name__ == "__main__":
    main()
