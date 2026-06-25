"""Re-simulate TEST with EXACTLY 1 predicted question per analyst
(Node-baseline-aligned). Re-judge, recompute coarse / B2 / B4.

Reuses the FINAL personas already on disk:
  data_auto/final_personas/<analyst>.json        (9 returning)
  data_auto/final_personas/_fallback.json        (cold-start fallback)

Outputs under data_auto/final_eval_1q/.
"""

from __future__ import annotations

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
FINAL_PERSONAS = os.path.join(DATA_AUTO, "final_personas")
OUT_DIR = os.path.join(DATA_AUTO, "final_eval_1q")
LOG_DIR = os.path.join(OUT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

SIM_PROMPT = os.path.join(PROMPTS, "simulate_questions_1q.md")
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


def _load_persona(name: str) -> dict:
    if name in COLD_START:
        p = os.path.join(FINAL_PERSONAS, "_fallback.json")
    else:
        p = os.path.join(FINAL_PERSONAS, f"{_safe(name)}.json")
    return json.load(open(p))


def main() -> None:
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]
    actuals_by = test["per_analyst_actual_questions"]

    sim_tpl = load_text(SIM_PROMPT)
    judge_tpl = load_text(JUDGE_PROMPT)
    b2_tpl = load_text(B2_PROMPT)
    b4_tpl = load_text(B4_PROMPT)

    per_analyst: dict[str, dict] = {}
    total_a = total_e = total_p = total_m = 0
    b2_cells = []

    print("=== Step 1: simulate (1 Q each) + judge + B2 per analyst ===")
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals:
            continue
        persona = _load_persona(name)

        # 1 simulate
        sim_prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        sim_out = call_llm(sim_prompt, expect_json=True,
                           dry_run_stub=stub_predictions(name),
                           log_to=os.path.join(LOG_DIR, f"sim_{_safe(name)}.txt"))
        try:
            pred = parse_json_strict(sim_out)
        except Exception:
            pred = stub_predictions(name)
        # Hard-cap to 1 question (defensive: LLM might disobey)
        if len(pred.get("predicted_questions", [])) > 1:
            pred["predicted_questions"] = pred["predicted_questions"][:1]

        # 2 judge
        judge_prompt = build_judge_prompt(judge_tpl, name, pred["predicted_questions"], actuals)
        judge_out = call_llm(judge_prompt, expect_json=True,
                             dry_run_stub=stub_judgment(name, actuals, pred["predicted_questions"]),
                             log_to=os.path.join(LOG_DIR, f"judge_{_safe(name)}.txt"))
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
                          log_to=os.path.join(LOG_DIR, f"b2_{_safe(name)}.txt"))
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
            "predictions": pred, "judgment": judgment, "b2": b2_eval,
        }
        print(f"  {name:25s} coarse: ex={s['n_exact']} pa={s['n_partial']} ms={s['n_miss']}; "
              f"B2: score={b2_eval.get('match_score_0_to_4')} binary={b2_eval.get('binary_match')}")

    coarse_hit = (total_e + total_p) / total_a if total_a else 0
    print(f"\nCoarse aggregate (11 analysts/12 actuals): "
          f"ex={total_e} pa={total_p} ms={total_m} hit={coarse_hit:.3f}")

    scored = [c for c in b2_cells if isinstance(c.get("match_score_0_to_4"), (int, float))]
    binary = sum(1 for c in scored if c.get("binary_match"))
    avg = (sum(c["match_score_0_to_4"] for c in scored) / max(1, len(scored))) if scored else 0
    print(f"B2 aggregate: binary_rate={binary/max(1,len(scored)):.3f} "
          f"({binary}/{len(scored)}); avg={avg:.3f}")

    summary = {
        "n_analysts_scored": len(per_analyst), "n_actual": total_a,
        "n_exact": total_e, "n_partial": total_p, "n_miss": total_m,
        "hit_rate_exact_or_partial": coarse_hit,
        "per_analyst": per_analyst,
        "b2_summary": {
            "evaluated_count": len(scored),
            "binary_match_count": binary,
            "binary_match_rate": binary / max(1, len(scored)),
            "average_match_score_0_to_4": avg,
        },
    }
    with open(os.path.join(OUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # Step 2: B4
    print("\n=== Step 2: B4 set-level ===")
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
    b4_out = call_llm(b4_prompt, expect_json=True, dry_run_stub=b4_stub,
                      log_to=os.path.join(LOG_DIR, "b4_prompt.txt"))
    try:
        b4 = parse_json_strict(b4_out)
    except Exception:
        b4 = b4_stub
    with open(os.path.join(OUT_DIR, "b4.json"), "w") as f:
        json.dump(b4, f, indent=2)
    m = b4.get("set_metrics", {})
    print(f"  B4 set_metrics: coverage={m.get('coverage_count')}/{b4['actual_question_count']} "
          f"({m.get('coverage_rate'):.3f}) "
          f"precision={m.get('useful_prediction_count')}/{b4['predicted_question_count']} "
          f"({m.get('precision_rate'):.3f}) "
          f"avg_act={m.get('average_actual_best_score'):.3f} "
          f"avg_pred={m.get('average_predicted_best_score'):.3f}")


if __name__ == "__main__":
    main()
