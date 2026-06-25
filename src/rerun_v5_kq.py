"""Generic v5 K-simulator: one LLM call per twin produces K ranked questions
using v5 personas. Mirrors rerun_v5_k10.py but takes --K as a parameter.

Usage: python3 src/rerun_v5_kq.py --K <int>

Output: data_auto/final_eval_<K>q_v5/summary.json
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
V5_PERSONAS = os.path.join(ROOT, "data", "personas_v5")
AUTO_PERSONAS = os.path.join(DATA_AUTO, "final_personas")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]
COLD_START = ["xian siew", "kevin kopelman"]
ALL_11 = TEST_RETURNING + COLD_START


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def _load_persona(name: str) -> dict | None:
    if name in COLD_START:
        p = os.path.join(AUTO_PERSONAS, "_fallback.json")
    else:
        p = os.path.join(V5_PERSONAS, f"{_safe(name)}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def run(K: int) -> None:
    sim_prompt_path = os.path.join(PROMPTS, f"simulate_questions_{K}q.md")
    if not os.path.exists(sim_prompt_path):
        raise FileNotFoundError(f"Prompt missing: {sim_prompt_path}")
    out_dir = os.path.join(DATA_AUTO, f"final_eval_{K}q_v5")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]
    actuals_by = test["per_analyst_actual_questions"]
    sim_tpl = load_text(sim_prompt_path)

    per_analyst: dict[str, dict] = {}
    total = 0
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals:
            continue
        persona = _load_persona(name)
        if persona is None:
            print(f"  ! {name}: no v5 persona; skip")
            continue
        prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        out = call_llm(prompt, expect_json=True,
                       dry_run_stub=stub_predictions(name),
                       log_to=os.path.join(log_dir, f"sim_{_safe(name)}.txt"))
        try:
            pred = parse_json_strict(out)
        except Exception as e:
            print(f"  ! {name}: parse failed ({e}); stub")
            pred = stub_predictions(name)
        pq = pred.get("predicted_questions", [])
        if len(pq) > K:
            pred["predicted_questions"] = pq[:K]
        elif len(pq) < K:
            print(f"  ! {name}: simulator returned {len(pq)} (expected {K})")
        per_analyst[name] = {
            "n_actual": len(actuals),
            "predictions": pred,
            "persona_source": "v5" if name in TEST_RETURNING else "auto-fallback",
        }
        total += len(pred.get("predicted_questions", []))
        print(f"  {name:25s} K={len(pred.get('predicted_questions', []))}")

    summary = {
        "n_analysts_scored": len(per_analyst),
        "K": K,
        "source": "v5",
        "total_predicted_questions": total,
        "per_analyst": per_analyst,
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_dir}/summary.json ({total} questions, {len(per_analyst)} analysts)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, required=True)
    args = ap.parse_args()
    run(args.K)


if __name__ == "__main__":
    main()
