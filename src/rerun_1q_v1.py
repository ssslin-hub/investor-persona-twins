"""Generate V1 K=1 predictions on TEST (2026-Q1) using V1 personas.

Mirrors rerun_5q.py's --source v1 branch but K=1 and skips evaluator steps
(B2/B4 done separately under gpt-5 via eval_gpt5_generic.py).

Output: data_auto/final_eval_1q_v1/summary.json
"""

from __future__ import annotations

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
OUT_DIR = os.path.join(DATA_AUTO, "final_eval_1q_v1")
LOG_DIR = os.path.join(OUT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

SIM_PROMPT = os.path.join(PROMPTS, "simulate_questions_1q.md")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]
COLD_START = ["xian siew", "kevin kopelman"]
ALL_11 = TEST_RETURNING + COLD_START


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def _load_v1_persona(name: str) -> dict | None:
    if name in COLD_START:
        p = os.path.join(AUTO_PERSONAS, "_fallback.json")
    else:
        p = os.path.join(V1_PERSONAS, f"{_safe(name)}.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def main() -> None:
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]
    actuals_by = test["per_analyst_actual_questions"]

    sim_tpl = load_text(SIM_PROMPT)

    per_analyst: dict[str, dict] = {}
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals:
            continue
        persona = _load_v1_persona(name)
        if persona is None:
            print(f"  ! {name}: no V1 persona; skipping")
            continue
        sim_prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        sim_out = call_llm(sim_prompt, expect_json=True,
                           dry_run_stub=stub_predictions(name),
                           log_to=os.path.join(LOG_DIR, f"sim_{_safe(name)}.txt"))
        try:
            pred = parse_json_strict(sim_out)
        except Exception:
            pred = stub_predictions(name)
        if len(pred.get("predicted_questions", [])) > 1:
            pred["predicted_questions"] = pred["predicted_questions"][:1]
        per_analyst[name] = {
            "n_actual": len(actuals),
            "predictions": pred,
            "persona_source": "v1" if name in TEST_RETURNING else "auto-fallback",
        }
        q0 = (pred.get("predicted_questions") or [{}])[0].get("question_text", "")
        print(f"  {name:25s} K=1: {q0[:80]}")

    summary = {
        "n_analysts_scored": len(per_analyst),
        "K": 1,
        "source": "v1",
        "per_analyst": per_analyst,
    }
    with open(os.path.join(OUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {OUT_DIR}/summary.json with {len(per_analyst)} analysts")


if __name__ == "__main__":
    main()
