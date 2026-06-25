"""K=20 simulation: produce predicted_questions only (no in-script eval).
Mirrors rerun_10q.py persona-loading + simulate loop. B2/B4 done separately
via eval_gpt5_generic.py to keep evaluator stable across all phases.

Outputs:
  data_auto/final_eval_20q_v1/summary.json
  data_auto/final_eval_20q_auto/summary.json
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
from run_pipeline import build_simulator_prompt, stub_predictions, load_text  # noqa: E402

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
V1_PERSONAS = os.path.join(ROOT, "data", "personas")
AUTO_PERSONAS = os.path.join(DATA_AUTO, "final_personas")
SIM_PROMPT = os.path.join(PROMPTS, "simulate_questions_20q.md")

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
    if source == "v1":
        if name in COLD_START:
            p = os.path.join(AUTO_PERSONAS, "_fallback.json")
        else:
            p = os.path.join(V1_PERSONAS, f"{_safe(name)}.json")
    else:
        if name in COLD_START:
            p = os.path.join(AUTO_PERSONAS, "_fallback.json")
        else:
            p = os.path.join(AUTO_PERSONAS, f"{_safe(name)}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def run(source: str) -> None:
    out_dir = os.path.join(DATA_AUTO, f"final_eval_20q_{source}")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]
    actuals_by = test["per_analyst_actual_questions"]
    sim_tpl = load_text(SIM_PROMPT)

    per_analyst: dict[str, dict] = {}
    total = 0
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals:
            continue
        persona = _load_persona(name, source)
        if persona is None:
            print(f"  ! {name}: no persona; skip")
            continue
        sim_prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        sim_out = call_llm(sim_prompt, expect_json=True,
                           dry_run_stub=stub_predictions(name),
                           log_to=os.path.join(log_dir, f"sim_{_safe(name)}.txt"))
        try:
            pred = parse_json_strict(sim_out)
        except Exception as e:
            print(f"  ! {name}: parse failed ({e}); stub")
            pred = stub_predictions(name)
        pq = pred.get("predicted_questions", [])
        if len(pq) > 20:
            pred["predicted_questions"] = pq[:20]
        elif len(pq) < 20:
            print(f"  ! {name}: simulator returned {len(pq)} questions (expected 20)")
        per_analyst[name] = {
            "n_actual": len(actuals),
            "predictions": pred,
            "persona_source": source if name in TEST_RETURNING else "auto-fallback",
        }
        total += len(pred.get("predicted_questions", []))
        print(f"  {name:25s} K={len(pred.get('predicted_questions',[]))}")

    summary = {
        "n_analysts_scored": len(per_analyst),
        "K": 20,
        "source": source,
        "total_predicted_questions": total,
        "per_analyst": per_analyst,
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_dir}/summary.json ({total} questions across {len(per_analyst)} analysts)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", choices=["v1", "auto"])
    args = ap.parse_args()
    run(args.source)


if __name__ == "__main__":
    main()
