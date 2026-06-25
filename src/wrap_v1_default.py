"""Wrap V1 K=2-3 raw per-analyst predictions (`data/predictions/<analyst>.json`)
into the summary.json shape expected by the generic gpt-5 evaluator.

Output: data_auto/final_eval_v1_default/summary.json
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

PRED_DIR = os.path.join(ROOT, "data", "predictions")
OUT_DIR = os.path.join(ROOT, "data_auto", "final_eval_v1_default")
TEST_JSON = os.path.join(ROOT, "data_auto", "test.json")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]
COLD_START = ["xian siew", "kevin kopelman"]
ALL_11 = TEST_RETURNING + COLD_START


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    test = json.load(open(TEST_JSON))
    actuals_by = test["per_analyst_actual_questions"]

    per_analyst: dict[str, dict] = {}
    total_q = 0
    for name in ALL_11:
        path = os.path.join(PRED_DIR, f"{_safe(name)}.json")
        if not os.path.exists(path):
            print(f"  ! {name}: no V1 prediction at {path}")
            continue
        raw = json.load(open(path))
        qs = raw.get("predicted_questions", [])
        per_analyst[name] = {
            "n_actual": len(actuals_by.get(name, [])),
            "predictions": {"predicted_questions": qs},
            "v1_analyst_alias": raw.get("analyst"),
        }
        total_q += len(qs)
        print(f"  {name:25s} K={len(qs)}")

    summary = {
        "n_analysts_scored": len(per_analyst),
        "K": "default (1-3)",
        "source": "v1-default",
        "total_predicted_questions": total_q,
        "per_analyst": per_analyst,
    }
    with open(os.path.join(OUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {OUT_DIR}/summary.json with {len(per_analyst)} analysts, {total_q} questions")


if __name__ == "__main__":
    main()
