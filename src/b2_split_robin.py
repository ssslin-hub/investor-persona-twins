"""Split Robin Farley's per-analyst B2 cell into 2 per-actual cells so all
B2 aggregates match the 12-actual denominator (parity with coarse / B4).

For each cold setting:
  - Load summary.json, find robin's K predicted_questions
  - For each of robin's 2 actuals (test.json), call B2 with (predictions, [single actual])
  - Replace the 1 robin cell with 2 cells in the aggregation
  - Write b2_per_actual_aggregated.json with denominator=12

Conv settings are already per-turn (per-actual); we just re-aggregate from
the existing per_turn data into the same schema for fair comparison.
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


def b2_for_one(analyst: str, predicted_questions: list, actual: dict, log_to: str) -> dict:
    """Call B2 evaluator with this analyst's K candidates and exactly 1 actual."""
    sim_block = {"analyst_name": analyst, "predicted_questions": predicted_questions}
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
        ev = parse_json_strict(out)
    except Exception as e:
        print(f"  ! B2 call failed for {analyst}: {type(e).__name__}: {str(e)[:150]}")
        ev = stub
    ev["analyst_name"] = analyst
    return ev


def aggregate(cells: list[dict], label: str) -> dict:
    scored = [c for c in cells if isinstance(c.get("match_score_0_to_4"), (int, float))]
    n = len(scored)
    binary = sum(1 for c in scored if c.get("binary_match"))
    strong = sum(1 for c in scored if (c.get("match_score_0_to_4") or 0) >= 4)
    avg = sum(c["match_score_0_to_4"] for c in scored) / max(1, n) if scored else 0
    return {
        "setting": label,
        "evaluated_count": n,
        "binary_match_count": binary,
        "binary_match_rate": binary / max(1, n),
        "strong_match_count": strong,
        "strong_match_rate": strong / max(1, n),
        "average_match_score_0_to_4": avg,
        "cells": cells,
    }


def main() -> None:
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    robin_actuals = test["per_analyst_actual_questions"].get("robin farley", [])
    assert len(robin_actuals) == 2, f"expected 2 robin actuals, got {len(robin_actuals)}"
    print(f"Robin actuals (n={len(robin_actuals)}):")
    for i, a in enumerate(robin_actuals):
        print(f"  Q{i}: {a['question'][:100]}")
    print()

    settings = [
        ("Auto K=1", os.path.join(DATA_AUTO, "final_eval_1q")),
        ("V1 K=5", os.path.join(DATA_AUTO, "final_eval_5q_v1")),
        ("Auto K=5", os.path.join(DATA_AUTO, "final_eval_5q_auto")),
        ("V1 K=10", os.path.join(DATA_AUTO, "final_eval_10q_v1")),
        ("Auto K=10", os.path.join(DATA_AUTO, "final_eval_10q_auto")),
    ]

    results = []
    print(f"{'setting':12s} {'n':>3s} {'binary>=3':>14s} {'strong>=4':>14s} {'avg_score':>10s}")
    print("-" * 60)
    for label, d in settings:
        summary = json.load(open(os.path.join(d, "summary.json")))
        per_analyst = summary["per_analyst"]
        log_dir = os.path.join(d, "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Build new B2 cell list: keep non-robin cells as-is; split robin into 2 per-actual cells
        new_cells = []
        for name, cell in per_analyst.items():
            if name == "robin farley":
                continue
            if isinstance(cell.get("b2"), dict):
                new_cells.append(cell["b2"])
        # Robin's K predictions
        robin_cell = per_analyst.get("robin farley", {})
        robin_preds = (robin_cell.get("predictions") or {}).get("predicted_questions", [])
        # Two B2 calls, one per robin actual
        for i, a in enumerate(robin_actuals):
            ev = b2_for_one("robin farley", robin_preds, a,
                            log_to=os.path.join(log_dir, f"b2_robin_actual{i}.txt"))
            ev["robin_actual_index"] = i
            new_cells.append(ev)

        agg = aggregate(new_cells, label)
        with open(os.path.join(d, "b2_per_actual.json"), "w") as f:
            json.dump(agg, f, indent=2)
        results.append(agg)
        print(f"{label:12s} {agg['evaluated_count']:>3} "
              f"{agg['binary_match_count']:>2}/{agg['evaluated_count']:<2}={agg['binary_match_rate']:.3f}    "
              f"{agg['strong_match_count']:>2}/{agg['evaluated_count']:<2}={agg['strong_match_rate']:.3f}    "
              f"{agg['average_match_score_0_to_4']:>10.3f}")

    # Conv settings: already per-turn (12 cells)
    for label, d in [("Conv K=1", os.path.join(DATA_AUTO, "final_eval_conv")),
                      ("Conv K=10", os.path.join(DATA_AUTO, "final_eval_conv_10q"))]:
        pt_path = os.path.join(d, "predictions_by_turn.json")
        if not os.path.exists(pt_path):
            continue
        cells = []
        for t in json.load(open(pt_path)):
            b2 = t.get("b2") if isinstance(t.get("b2"), dict) else None
            if b2:
                cells.append(b2)
        agg = aggregate(cells, label)
        with open(os.path.join(d, "b2_per_actual.json"), "w") as f:
            json.dump(agg, f, indent=2)
        results.append(agg)
        print(f"{label:12s} {agg['evaluated_count']:>3} "
              f"{agg['binary_match_count']:>2}/{agg['evaluated_count']:<2}={agg['binary_match_rate']:.3f}    "
              f"{agg['strong_match_count']:>2}/{agg['evaluated_count']:<2}={agg['strong_match_rate']:.3f}    "
              f"{agg['average_match_score_0_to_4']:>10.3f}")

    with open(os.path.join(DATA_AUTO, "b2_per_actual_all.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {os.path.join(DATA_AUTO, 'b2_per_actual_all.json')}")


if __name__ == "__main__":
    main()
