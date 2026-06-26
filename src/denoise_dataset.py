#!/usr/bin/env python3
"""
Pre-evaluation gate: denoise the actual analyst questions at the DATA LAYER.

Why this lives here (not in each eval script)
---------------------------------------------
The repo has 40+ evaluation/build scripts that each load analysts_test.json
directly and read record["question"]. Routing every one through a shared
loader is fragile: any *new* script can forget to call denoise. Instead we
denoise the `question` field at rest, so every current and future reader gets
cleaned text for free — there is nothing to remember to call.

Guarantees
----------
- NON-DESTRUCTIVE: the original spoken text is preserved under `question_raw`.
- IDEMPOTENT: `question` is always re-derived from `question_raw`, so re-running
  (e.g. after editing denoise rules) is safe and picks up the new rules.
- FACT-CHECKED: each rewrite is verified to preserve every number / % / bps /
  quarter. Any record that fails keeps its RAW question and is reported —
  never silently trusted.
- TRAINING DATA UNTOUCHED: only analysts_test.json (evaluation actuals) is
  cleaned. analysts.json (persona-training history) is left raw on purpose so
  persona `rhetorical_signature` (openers/greetings) still works.

Usage
-----
    python3 denoise_dataset.py data/analysts_test.json          # clean in place
    python3 denoise_dataset.py data/analysts_test.json --dry-run

After ANY change to the denoise rules, just re-run the first command.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from denoise_questions import denoise, numbers_preserved


def clean_actuals(actuals: dict) -> tuple[dict, list[str]]:
    """Denoise the `question` field of every actual record IN PLACE.

    Single source of truth used both by the data-layer gate (denoise_test_file)
    and by run_pipeline.py's runtime call. Preserves `question_raw`, is
    idempotent (re-derives from raw), and is fail-safe (keeps raw on a failed
    number check). Returns (actuals, flagged_keys).
    """
    flagged: list[str] = []
    for name, records in actuals.items():
        for i, r in enumerate(records):
            raw = r.get("question_raw", r.get("question", ""))
            r["question_raw"] = raw
            cleaned, _ = denoise(raw)
            ok, _, _ = numbers_preserved(raw, cleaned)
            r["question"] = cleaned if ok else raw   # fail-safe: keep raw
            if not ok:
                flagged.append(f"{name} #{i}")
    return actuals, flagged


def denoise_test_file(path: str, write: bool = True) -> dict:
    data = json.load(open(path))
    blocks = data.get("per_analyst_actual_questions", {})
    n = sum(len(v) for v in blocks.values())
    _, flagged = clean_actuals(blocks)

    if write:
        json.dump(data, open(path, "w"), indent=2, ensure_ascii=False)

    where = os.path.basename(path)
    print(f"denoised {n} actual questions in {where} "
          f"({len(flagged)} kept raw on number-check fail)")
    for f in flagged:
        print(f"  !! number-check failed, left RAW: {f}")
    return data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("test_file", help="path to analysts_test.json")
    ap.add_argument("--dry-run", action="store_true",
                    help="report changes without writing the file")
    args = ap.parse_args()
    denoise_test_file(args.test_file, write=not args.dry_run)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
