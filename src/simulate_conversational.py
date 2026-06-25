"""Conversational simulation: sequential simulator that sees prior analysts'
Q&A history in operator order. K=1 per turn.

Pipeline per turn t (operator queue order from 2026-Q1):
  1. Identify analyst at turn t.
  2. Build conversational_context = prepared remarks + Q&A so far (turns 1..t-1)
     using actual previous questions and actual management responses.
  3. Load persona for that analyst (auto final personas + _fallback for cold-start).
  4. Call simulator (K=1) with persona + management_context + q_a_so_far.
  5. Run coarse judge + B2 evaluator on (prediction, actual at turn t).
  6. Append actual question + actual response to q_a_so_far for turn t+1.

After all turns:
  - Run B4 once on the full predicted_set vs actual_set.
  - Compute identity-matched coverage from B4 output.

Outputs:
  data_auto/final_eval_conv/predictions_by_turn.json
  data_auto/final_eval_conv/summary.json   (coarse + B2 aggregates)
  data_auto/final_eval_conv/b4.json
  data_auto/final_eval_conv/logs/
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
    build_judge_prompt, stub_predictions, stub_judgment, load_text, _fill,
)
from build_analyst_dataset import canon_name  # noqa: E402

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
FINAL_PERSONAS = os.path.join(DATA_AUTO, "final_personas")
OUT_DIR = os.path.join(DATA_AUTO, "final_eval_conv")
LOG_DIR = os.path.join(OUT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

SIM_PROMPT = os.path.join(PROMPTS, "simulate_questions_conversational.md")
JUDGE_PROMPT = os.path.join(PROMPTS, "judge_match.md")
B2_PROMPT = os.path.join(PROMPTS, "b2_eval.md")
B4_PROMPT = os.path.join(PROMPTS, "b4_eval.md")

PARSED_Q1 = os.path.join(ROOT, "parsed", "2026-q1-548547.json")
TEST_PATH = os.path.join(DATA_AUTO, "test.json")

COLD_START = {"xian siew", "kevin kopelman"}


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def _load_persona(name: str) -> dict | None:
    if name in COLD_START:
        p = os.path.join(FINAL_PERSONAS, "_fallback.json")
    else:
        p = os.path.join(FINAL_PERSONAS, f"{_safe(name)}.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def extract_turn_queue() -> list[dict]:
    """From parsed/2026-q1*.json:analyst_questions, produce an ordered list of
    turn dicts: {turn_index, analyst_name_lc, question, response}.
    """
    rec = json.load(open(PARSED_Q1))
    queue = []
    for i, q in enumerate(rec["analyst_questions"]):
        queue.append({
            "turn_index": i,
            "analyst_name_lc": canon_name(q["analyst"]),
            "operator_intro": q.get("operator_intro") or "",
            "question": q["question"],
            "response": q.get("response", "") or "",
        })
    return queue


def build_q_a_so_far(prior_turns: list[dict]) -> str:
    """Render the chronological Q&A so far up to but not including turn t."""
    if not prior_turns:
        return "(no prior turns — you are first in the queue)"
    blocks = []
    for k, t in enumerate(prior_turns, 1):
        intro = t.get("operator_intro", "").strip()
        q = t.get("question", "").strip()
        r = t.get("response", "").strip()
        # truncate response for budget
        r_short = r if len(r) <= 1500 else r[:1500] + "..."
        blocks.append(
            f"--- Prior turn {k}: analyst {t['analyst_name_lc']} ---\n"
            f"[Operator]: {intro[:200]}\n"
            f"[Analyst Q]: {q}\n"
            f"[Mgmt response]: {r_short}"
        )
    return "\n\n".join(blocks)


def build_simulator_prompt_conv(template: str, persona: dict, mgmt_pres: str,
                                  q_a_so_far: str) -> str:
    if "[Q&A SO FAR]" in mgmt_pres:
        mgmt_pres = mgmt_pres.split("[Q&A SO FAR]", 1)[0].rstrip()
    return _fill(
        template,
        persona_json=json.dumps(persona, indent=2),
        management_presentation=mgmt_pres,
        q_a_so_far=q_a_so_far,
    )


def main() -> None:
    test = json.load(open(TEST_PATH))
    mgmt = test["management_context"]

    queue = extract_turn_queue()
    print(f"=== Conversational simulation — 2026-Q1 operator queue ({len(queue)} turns) ===")
    for t in queue:
        print(f"  turn {t['turn_index']}: {t['analyst_name_lc']}")

    sim_tpl = load_text(SIM_PROMPT)
    judge_tpl = load_text(JUDGE_PROMPT)
    b2_tpl = load_text(B2_PROMPT)
    b4_tpl = load_text(B4_PROMPT)

    per_turn: list[dict] = []
    per_analyst: dict[str, dict] = {}
    total_a = total_e = total_p = total_m = 0
    b2_cells = []

    print("\nStep 1: sequential simulate + judge + B2")
    prior_turns: list[dict] = []
    for t in queue:
        idx = t["turn_index"]
        name = t["analyst_name_lc"]
        persona = _load_persona(name)
        if persona is None:
            print(f"  ! turn {idx} {name}: no persona; skipping")
            prior_turns.append(t)
            continue

        q_a_so_far = build_q_a_so_far(prior_turns)
        sim_prompt = build_simulator_prompt_conv(sim_tpl, persona, mgmt, q_a_so_far)
        log = os.path.join(LOG_DIR, f"sim_turn{idx:02d}_{_safe(name)}.txt")
        sim_out = call_llm(sim_prompt, expect_json=True,
                           dry_run_stub=stub_predictions(name), log_to=log)
        try:
            pred = parse_json_strict(sim_out)
        except Exception:
            pred = stub_predictions(name)
        # cap to 1
        if len(pred.get("predicted_questions", [])) > 1:
            pred["predicted_questions"] = pred["predicted_questions"][:1]

        # Leakage check: actual t question must NOT be verbatim inside q_a_so_far
        assert t["question"][:100] not in q_a_so_far, \
            f"LEAKAGE at turn {idx}: own actual present in q_a_so_far"

        # coarse judge against THIS turn's actual only
        actual_for_judge = [{"call": "2026-Q1", "question": t["question"]}]
        judge_prompt = build_judge_prompt(judge_tpl, name, pred["predicted_questions"],
                                          actual_for_judge)
        judge_out = call_llm(judge_prompt, expect_json=True,
                             dry_run_stub=stub_judgment(name, actual_for_judge,
                                                         pred["predicted_questions"]),
                             log_to=os.path.join(LOG_DIR, f"judge_turn{idx:02d}_{_safe(name)}.txt"))
        try:
            judgment = parse_json_strict(judge_out)
        except Exception:
            judgment = stub_judgment(name, actual_for_judge, pred["predicted_questions"])
        s = judgment["summary"]
        total_a += s["n_actual"]; total_e += s["n_exact"]
        total_p += s["n_partial"]; total_m += s["n_miss"]

        # B2 per turn
        sim_block = {"analyst_name": name, "predicted_questions": pred["predicted_questions"]}
        actuals_b2 = [{"tuple_id": f"{name}-actual-turn{idx}", "analyst_name": name,
                       "call": "2026-Q1", "question": t["question"]}]
        b2_prompt = (b2_tpl
                     .replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2))
                     .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b2, indent=2)))
        b2_stub = {"analyst_name": name, "match_score_0_to_4": 0, "binary_match": False,
                   "topic_match": "none", "trigger_alignment": "none",
                   "question_form_alignment": "none", "granularity_alignment": "none",
                   "reasoning": "DRY", "miss_or_gap": "DRY"}
        b2_out = call_llm(b2_prompt, expect_json=True, dry_run_stub=b2_stub,
                          log_to=os.path.join(LOG_DIR, f"b2_turn{idx:02d}_{_safe(name)}.txt"))
        try:
            b2_eval = parse_json_strict(b2_out)
        except Exception:
            b2_eval = b2_stub
        b2_eval["analyst_name"] = name
        b2_eval["turn_index"] = idx
        b2_cells.append(b2_eval)

        per_turn.append({
            "turn_index": idx, "analyst": name,
            "q_a_so_far_chars": len(q_a_so_far),
            "predicted_questions": pred.get("predicted_questions", []),
            "actual_question": t["question"],
            "judgment_summary": s, "b2": b2_eval,
        })
        agg = per_analyst.setdefault(name, {"n_actual": 0, "n_exact": 0, "n_partial": 0,
                                              "n_miss": 0, "turns": []})
        agg["n_actual"] += s["n_actual"]; agg["n_exact"] += s["n_exact"]
        agg["n_partial"] += s["n_partial"]; agg["n_miss"] += s["n_miss"]
        agg["turns"].append(idx)
        print(f"  turn {idx:2d} {name:22s} qa_so_far={len(q_a_so_far):>5} chars "
              f"coarse: ex={s['n_exact']} pa={s['n_partial']} ms={s['n_miss']}; "
              f"B2: score={b2_eval.get('match_score_0_to_4')}")

        prior_turns.append(t)

    for n, agg in per_analyst.items():
        agg["hit"] = (agg["n_exact"] + agg["n_partial"]) / agg["n_actual"] if agg["n_actual"] else 0

    coarse_hit = (total_e + total_p) / total_a if total_a else 0
    print(f"\nCoarse aggregate: ex={total_e} pa={total_p} ms={total_m} hit={coarse_hit:.3f}")
    scored = [c for c in b2_cells if isinstance(c.get("match_score_0_to_4"), (int, float))]
    binary = sum(1 for c in scored if c.get("binary_match"))
    avg = (sum(c["match_score_0_to_4"] for c in scored) / max(1, len(scored))) if scored else 0
    print(f"B2 aggregate: binary_rate={binary/max(1,len(scored)):.3f} "
          f"({binary}/{len(scored)}); avg={avg:.3f}")

    with open(os.path.join(OUT_DIR, "predictions_by_turn.json"), "w") as f:
        json.dump(per_turn, f, indent=2)

    summary = {
        "mode": "conversational", "K_per_turn": 1, "n_turns": len(per_turn),
        "n_actual": total_a, "n_exact": total_e, "n_partial": total_p, "n_miss": total_m,
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

    # Step 2: B4 set-level on the full set
    print("\nStep 2: B4 set-level + identity-matched")
    predicted, actuals = [], []
    for pt in per_turn:
        for i, q in enumerate(pt["predicted_questions"]):
            predicted.append({
                "candidate_id": f"{_safe(pt['analyst'])}-turn{pt['turn_index']}-pred-{i}",
                "source_analyst": pt["analyst"],
                "turn_index": pt["turn_index"],
                "question": q.get("question_text", ""),
                "topic_label": q.get("topic_label", ""),
            })
        actuals.append({
            "actual_id": f"{_safe(pt['analyst'])}-turn{pt['turn_index']}-actual",
            "source_analyst": pt["analyst"],
            "turn_index": pt["turn_index"],
            "question": pt["actual_question"],
        })
    print(f"  predicted set size: {len(predicted)}; actual set size: {len(actuals)}")

    b4_prompt = (b4_tpl
                 .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(predicted, indent=2))
                 .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
    b4_stub = {"actual_question_count": len(actuals), "predicted_question_count": len(predicted),
               "actual_coverage": [], "predicted_precision": [],
               "set_metrics": {"coverage_count": 0, "coverage_rate": 0,
                                "useful_prediction_count": 0, "precision_rate": 0,
                                "average_actual_best_score": 0,
                                "average_predicted_best_score": 0},
               "missed_actual_themes": [], "overpredicted_themes": [], "summary": "DRY"}
    b4_out = call_llm(b4_prompt, expect_json=True, dry_run_stub=b4_stub,
                      log_to=os.path.join(LOG_DIR, "b4_prompt.txt"))
    try:
        b4 = parse_json_strict(b4_out)
    except Exception:
        b4 = b4_stub
    with open(os.path.join(OUT_DIR, "b4.json"), "w") as f:
        json.dump(b4, f, indent=2)
    m = b4.get("set_metrics", {})
    print(f"  B4 coverage={m.get('coverage_count')}/{b4['actual_question_count']} "
          f"({m.get('coverage_rate'):.3f}) "
          f"precision={m.get('useful_prediction_count')}/{b4['predicted_question_count']} "
          f"({m.get('precision_rate'):.3f})")

    # Identity-matched coverage
    id_count = 0
    id_total = b4.get("actual_question_count", 0)
    for c in b4.get("actual_coverage", []):
        if not c.get("covered"):
            continue
        bpi = c.get("best_predicted_candidate_id") or ""
        # source_analyst encoded as prefix
        aid = c.get("actual_id", "")
        # actual_id format: <analyst>-turn<idx>-actual
        # candidate_id format: <analyst>-turn<idx>-pred-<i>
        # match on source_analyst prefix
        actual_an = aid.split("-turn", 1)[0]
        cand_an = bpi.split("-turn", 1)[0]
        if actual_an == cand_an:
            id_count += 1
    id_rate = id_count / id_total if id_total else 0
    print(f"  Identity-matched coverage: {id_count}/{id_total} = {id_rate:.3f}")

    summary["b4"] = {
        "actual_question_count": b4.get("actual_question_count"),
        "predicted_question_count": b4.get("predicted_question_count"),
        "set_metrics": m,
        "identity_matched_coverage": {"count": id_count, "total": id_total, "rate": id_rate},
    }
    with open(os.path.join(OUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
