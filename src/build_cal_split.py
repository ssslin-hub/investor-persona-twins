"""Build data_auto/cal.json containing the 2025-Q3 + 2025-Q4 management
contexts and per-analyst actual questions.

Output schema:
  {
    "calls": [
      {
        "call": "2025-Q3",
        "management_context": "<presentation text>",
        "per_analyst_actual_questions": { "<name>": [ {actual1}, ... ] }
      },
      {
        "call": "2025-Q4",
        ...
      }
    ]
  }

Also copies data/analysts_test.json (2026-Q1) to data_auto/test.json for
uniform downstream access.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_analyst_dataset import (  # noqa: E402
    canon_name, is_noise, find_question_turn_index, build_context_for_question,
)

PARSED = os.path.join(ROOT, "parsed")
OUT_DIR = os.path.join(ROOT, "data_auto")
os.makedirs(OUT_DIR, exist_ok=True)

CAL_CALLS = ["2025-q3", "2025-q4"]


def load_call(stem: str) -> dict:
    files = [f for f in os.listdir(PARSED) if f.startswith(stem) and f.endswith(".json")]
    if not files:
        raise FileNotFoundError(f"no parsed file for {stem}")
    return json.load(open(os.path.join(PARSED, files[0])))


def extract_call(rec: dict) -> dict:
    actuals: dict[str, list] = {}
    for i, q in enumerate(rec["analyst_questions"]):
        name_lc = canon_name(q["analyst"])
        aff = q.get("affiliation")
        if is_noise(name_lc, aff):
            continue
        j = find_question_turn_index(rec, i)
        ctx = build_context_for_question(rec, j)
        actuals.setdefault(name_lc, []).append({
            "call": f"{rec['year']}-Q{rec['quarter']}",
            "year": rec["year"],
            "quarter": rec["quarter"],
            "affiliation": aff,
            "operator_intro": q.get("operator_intro"),
            "context": ctx,
            "question": q["question"],
            "response": q.get("response", ""),
        })
    # Management-only context = context up to first analyst question
    if rec["analyst_questions"]:
        first_j = find_question_turn_index(rec, 0)
        mgmt = build_context_for_question(rec, first_j)
    else:
        mgmt = ""
    return {
        "call": f"{rec['year']}-Q{rec['quarter']}",
        "management_context": mgmt,
        "per_analyst_actual_questions": actuals,
    }


def main() -> None:
    print("=== Building CAL split ===")
    calls_out = []
    for stem in CAL_CALLS:
        rec = load_call(stem)
        block = extract_call(rec)
        n_anal = len(block["per_analyst_actual_questions"])
        n_q = sum(len(v) for v in block["per_analyst_actual_questions"].values())
        print(f"  {block['call']}: {n_anal} analysts, {n_q} actuals")
        calls_out.append(block)

    cal_path = os.path.join(OUT_DIR, "cal.json")
    with open(cal_path, "w") as f:
        json.dump({"calls": calls_out}, f, indent=2)
    print(f"  wrote {cal_path}")

    # Copy 2026-Q1 test
    src = os.path.join(ROOT, "data", "analysts_test.json")
    dst = os.path.join(OUT_DIR, "test.json")
    shutil.copy2(src, dst)
    print(f"  copied {src} -> {dst}")


if __name__ == "__main__":
    main()
