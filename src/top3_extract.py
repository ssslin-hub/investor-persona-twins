"""Extract top-3 predicted questions per twin per setting into
data_auto/top_picks/{analyst_safe}/{setting_name}.json.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ALL_11 = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora", "xian siew", "kevin kopelman",
]

SETTINGS = [
    ("parallel_K10_v1",   "data_auto/final_eval_10q_v1/summary.json"),
    ("parallel_K10_auto", "data_auto/final_eval_10q_auto/summary.json"),
    ("parallel_K14_v1",   "data_auto/final_eval_14q_v1/summary.json"),
    ("parallel_K14_auto", "data_auto/final_eval_14q_auto/summary.json"),
    ("parallel_K20_v1",   "data_auto/final_eval_20q_v1/summary.json"),
    ("parallel_K20_auto", "data_auto/final_eval_20q_auto/summary.json"),
]


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def main() -> None:
    out_root = os.path.join(ROOT, "data_auto", "top_picks")
    os.makedirs(out_root, exist_ok=True)
    for name in ALL_11:
        d = os.path.join(out_root, _safe(name))
        os.makedirs(d, exist_ok=True)
    for setting_name, summary_rel in SETTINGS:
        p = os.path.join(ROOT, summary_rel)
        summary = json.load(open(p))
        for name in ALL_11:
            pa = summary.get("per_analyst", {}).get(name) or {}
            preds = (pa.get("predictions") or {}).get("predicted_questions", [])
            top3 = preds[:3]
            out_path = os.path.join(out_root, _safe(name), f"{setting_name}.json")
            with open(out_path, "w") as f:
                json.dump({"analyst": name, "setting": setting_name, "top3": top3}, f, indent=2)
        print(f"  {setting_name}: wrote top-3 for {len(ALL_11)} twins")
    print(f"\nDone. {out_root}/{{analyst}}/{{setting}}.json")


if __name__ == "__main__":
    main()
