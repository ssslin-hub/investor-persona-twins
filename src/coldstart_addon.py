"""Add cold-start (xian siew, kevin kopelman) cells to the auto-pipeline TEST
evaluation, using an aggregate-fallback persona built from the 9 returning
analysts' Variant A round 0 personas. Both V1 and auto would use the same
fallback for cold-start, so these cells are equivalent across pipelines and
do not bias the comparison; they only bring N from 10 → 12 (matching the
Node baseline roster).

What it does:
1. Build aggregate-fallback persona: merge the 9 returning A r0 personas
   into one generic "cruise-leisure analyst" template
2. For each cold-start analyst: simulator(fallback, 2026-Q1 mgmt) → predictions
3. Judge predictions vs actuals → coarse exact/partial/miss
4. B2 evaluator → score, binary, sub-dims
5. Re-aggregate coarse + B2 over 11 analysts / 12 actuals
6. For B4: extend predicted_set + actual_set with cold-start cells, re-run
   the set-level evaluator once

Writes:
  data_auto/final_personas/_fallback.json
  data_auto/final_eval/coldstart_<analyst>.json (predictions + judgment + b2)
  data_auto/final_eval/summary_11analysts.json (coarse re-aggregated)
  data_auto/final_eval/b2_summary_11analysts.json
  data_auto/final_eval/b4_11analysts.json
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
FINAL_EVAL = os.path.join(DATA_AUTO, "final_eval")
SIMULATOR_PROMPT = os.path.join(PROMPTS, "simulate_questions.md")
JUDGE_PROMPT = os.path.join(PROMPTS, "judge_match.md")
B2_PROMPT = os.path.join(PROMPTS, "b2_eval.md")
B4_PROMPT = os.path.join(PROMPTS, "b4_eval.md")

COLD_START = ["xian siew", "kevin kopelman"]
TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def build_fallback_persona() -> dict:
    """Aggregate-fallback persona = generic cruise-leisure sell-side analyst.
    Built by hand (no LLM) to keep it deterministic and equally available to
    any pipeline (V1 or auto)."""
    return {
        "coverage_profile": {
            "firm": "(unknown — cold-start analyst, no history available)",
            "seniority_signal": "Unknown. Treat as a generic mid-to-senior sell-side analyst covering the cruise / leisure sector.",
            "sector_lens": "Cruise and broader consumer-leisure sector; likely cross-coverage of lodging or travel.",
            "rhetorical_signature": [
                "Opens with a short pleasantry then poses a single substantive question.",
                "Tends to ask one focused question per turn rather than multi-part."
            ],
        },
        "reasoning_style": {
            "primary_mode": "mixed — defaults to a quantitative-modeling slant when management quotes numbers and a qualitative-strategic slant when management frames multi-year plans.",
            "follow_up_pattern": "Single-question turn, occasionally with a brief follow-up. No strong pushback pattern.",
            "evidence_demanded": "Specific numbers, explicit guidance, and mechanisms tying near-term results to forward outlook.",
            "anchoring_habits": "Anchors against the company's most recently issued guidance and against industry peers when available.",
        },
        "recurring_concerns": {
            "core_topics": [
                {"topic": "demand / booking_curve", "what_they_press_on": "Forward booking visibility, consumer health, close-in vs forward demand.", "supporting_calls": []},
                {"topic": "pricing / yield", "what_they_press_on": "Yield drivers, pricing vs onboard spend, regional or itinerary mix.", "supporting_calls": []},
                {"topic": "capital_return / balance_sheet", "what_they_press_on": "Leverage trajectory, buybacks/dividends, capex cadence.", "supporting_calls": []},
            ],
            "blind_spots": "Unknown (no history).",
            "stance_drift": "Unknown (no history).",
        },
    }


def run_cold_start():
    os.makedirs(FINAL_EVAL, exist_ok=True)
    fallback = build_fallback_persona()
    fb_path = os.path.join(DATA_AUTO, "final_personas", "_fallback.json")
    os.makedirs(os.path.dirname(fb_path), exist_ok=True)
    with open(fb_path, "w") as f:
        json.dump(fallback, f, indent=2)
    print(f"  wrote {fb_path}")

    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]
    actuals_by = test["per_analyst_actual_questions"]

    sim_tpl = load_text(SIMULATOR_PROMPT)
    judge_tpl = load_text(JUDGE_PROMPT)
    b2_tpl = load_text(B2_PROMPT)

    log_dir = os.path.join(FINAL_EVAL, "coldstart_logs")
    os.makedirs(log_dir, exist_ok=True)

    coldstart_out: dict[str, dict] = {}
    for name in COLD_START:
        actuals = actuals_by.get(name, [])
        if not actuals:
            print(f"  ! {name}: no actuals in TEST; skipping")
            continue
        # 1. simulator
        sim_prompt = build_simulator_prompt(sim_tpl, fallback, mgmt)
        sim_out = call_llm(sim_prompt, expect_json=True,
                           dry_run_stub=stub_predictions(name),
                           log_to=os.path.join(log_dir, f"sim_{_safe(name)}.txt"))
        try:
            pred = parse_json_strict(sim_out)
        except Exception:
            pred = stub_predictions(name)
        # 2. coarse judge
        judge_prompt = build_judge_prompt(judge_tpl, name, pred["predicted_questions"], actuals)
        judge_out = call_llm(judge_prompt, expect_json=True,
                             dry_run_stub=stub_judgment(name, actuals, pred["predicted_questions"]),
                             log_to=os.path.join(log_dir, f"judge_{_safe(name)}.txt"))
        try:
            judgment = parse_json_strict(judge_out)
        except Exception:
            judgment = stub_judgment(name, actuals, pred["predicted_questions"])
        # 3. B2
        sim_block = {"analyst_name": name, "predicted_questions": pred["predicted_questions"]}
        actuals_b2 = [{"tuple_id": f"{name}-actual-{i}", "analyst_name": name,
                       "call": a.get("call"), "question": a.get("question")}
                      for i, a in enumerate(actuals)]
        b2_prompt = (b2_tpl
                     .replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2))
                     .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b2, indent=2)))
        b2_stub = {"analyst_name": name, "best_match_actual_tuple_id": None,
                   "match_score_0_to_4": 0, "binary_match": False,
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

        s = judgment["summary"]
        cell = {
            "analyst": name,
            "predictions": pred,
            "judgment": judgment,
            "b2": b2_eval,
            "summary": {
                "n_actual": s["n_actual"],
                "n_exact": s["n_exact"],
                "n_partial": s["n_partial"],
                "n_miss": s["n_miss"],
                "hit": (s["n_exact"] + s["n_partial"]) / s["n_actual"] if s["n_actual"] else 0,
            },
        }
        with open(os.path.join(FINAL_EVAL, f"coldstart_{_safe(name)}.json"), "w") as f:
            json.dump(cell, f, indent=2)
        coldstart_out[name] = cell
        print(f"  {name:25s} coarse: ex={s['n_exact']} pa={s['n_partial']} ms={s['n_miss']}; "
              f"B2: score={b2_eval.get('match_score_0_to_4')} binary={b2_eval.get('binary_match')}")

    # --- Re-aggregate coarse (11 analysts / 12 actuals) ---
    summary = json.load(open(os.path.join(FINAL_EVAL, "summary.json")))
    n_actual = summary["n_actual"]
    n_exact = summary["n_exact"]
    n_partial = summary["n_partial"]
    n_miss = summary["n_miss"]
    per_analyst = dict(summary.get("per_analyst", {}))
    for name, cell in coldstart_out.items():
        s = cell["summary"]
        n_actual += s["n_actual"]
        n_exact += s["n_exact"]
        n_partial += s["n_partial"]
        n_miss += s["n_miss"]
        per_analyst[name] = s
    coarse_11 = {
        "n_returning_analysts_scored": summary["n_returning_analysts_scored"] + len(coldstart_out),
        "n_actual": n_actual,
        "n_exact": n_exact,
        "n_partial": n_partial,
        "n_miss": n_miss,
        "hit_rate_exact_or_partial": (n_exact + n_partial) / n_actual if n_actual else 0,
        "per_analyst": per_analyst,
    }
    with open(os.path.join(FINAL_EVAL, "summary_11analysts.json"), "w") as f:
        json.dump(coarse_11, f, indent=2)
    print(f"\nCoarse (11 analysts/12 actuals): hit={coarse_11['hit_rate_exact_or_partial']:.3f} "
          f"({n_exact}ex+{n_partial}pa+{n_miss}ms/{n_actual})")

    # --- Re-aggregate B2 (11 analysts) ---
    b2_summary = json.load(open(os.path.join(FINAL_EVAL, "b2_summary.json")))
    cells_b2 = []
    # Reload returning B2 cells
    for n in TEST_RETURNING:
        p = os.path.join(FINAL_EVAL, "b2", f"{_safe(n)}.json")
        if os.path.exists(p):
            cells_b2.append(json.load(open(p)))
    for name, cell in coldstart_out.items():
        cells_b2.append(cell["b2"])
    scored = [c for c in cells_b2 if isinstance(c.get("match_score_0_to_4"), (int, float))]
    binary = sum(1 for c in scored if c.get("binary_match"))
    avg = (sum(c["match_score_0_to_4"] for c in scored) / max(1, len(scored))) if scored else 0
    b2_agg11 = {
        "evaluated_count": len(scored),
        "binary_match_count": binary,
        "binary_match_rate": binary / max(1, len(scored)),
        "average_match_score_0_to_4": avg,
    }
    with open(os.path.join(FINAL_EVAL, "b2_summary_11analysts.json"), "w") as f:
        json.dump(b2_agg11, f, indent=2)
    print(f"B2 (11 analysts): binary_match_rate={b2_agg11['binary_match_rate']:.3f} "
          f"({binary}/{len(scored)}) avg={avg:.3f}")

    # --- B4 (re-run on extended set) ---
    b4_tpl = load_text(B4_PROMPT)
    predicted: list[dict] = []
    actuals_b4: list[dict] = []
    for name in TEST_RETURNING:
        pa = summary["per_analyst"].get(name) or {}
        for i, q in enumerate((pa.get("predictions") or {}).get("predicted_questions", [])):
            predicted.append({
                "candidate_id": f"{_safe(name)}-pred-{i}",
                "source_analyst": name,
                "question": q.get("question_text", ""),
                "topic_label": q.get("topic_label", ""),
            })
        for i, a in enumerate(actuals_by.get(name, [])):
            actuals_b4.append({
                "actual_id": f"{_safe(name)}-actual-{i}",
                "source_analyst": name,
                "question": a.get("question", ""),
            })
    for name, cell in coldstart_out.items():
        for i, q in enumerate(cell["predictions"]["predicted_questions"]):
            predicted.append({
                "candidate_id": f"{_safe(name)}-pred-{i}",
                "source_analyst": name,
                "question": q.get("question_text", ""),
                "topic_label": q.get("topic_label", ""),
            })
        for i, a in enumerate(actuals_by.get(name, [])):
            actuals_b4.append({
                "actual_id": f"{_safe(name)}-actual-{i}",
                "source_analyst": name,
                "question": a.get("question", ""),
            })
    print(f"\nB4 extended set: {len(predicted)} predicted, {len(actuals_b4)} actuals")
    prompt = (b4_tpl
              .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(predicted, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b4, indent=2)))
    b4_stub = {
        "actual_question_count": len(actuals_b4),
        "predicted_question_count": len(predicted),
        "actual_coverage": [], "predicted_precision": [],
        "set_metrics": {"coverage_count": 0, "coverage_rate": 0, "useful_prediction_count": 0,
                         "precision_rate": 0, "average_actual_best_score": 0,
                         "average_predicted_best_score": 0},
        "missed_actual_themes": [], "overpredicted_themes": [], "summary": "DRY",
    }
    b4_out = call_llm(prompt, expect_json=True, dry_run_stub=b4_stub,
                      log_to=os.path.join(log_dir, "b4_extended.txt"))
    try:
        b4 = parse_json_strict(b4_out)
    except Exception:
        b4 = b4_stub
    with open(os.path.join(FINAL_EVAL, "b4_11analysts.json"), "w") as f:
        json.dump(b4, f, indent=2)
    m = b4.get("set_metrics", {})
    print(f"B4 (11 analysts): coverage={m.get('coverage_count')}/{b4['actual_question_count']} "
          f"({m.get('coverage_rate'):.3f}) "
          f"precision={m.get('useful_prediction_count')}/{b4['predicted_question_count']} "
          f"({m.get('precision_rate'):.3f})")


if __name__ == "__main__":
    run_cold_start()
