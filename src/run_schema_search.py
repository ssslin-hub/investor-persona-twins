"""Option-A schema search.

Pipeline:

  1. Build the CALIBRATION dataset by holding out the call ``2025-q4``:
     training = all calls strictly BEFORE 2025-Q4.
     Saved under ``data_cal/``.

  2. For each schema variant in {V1, V2, V3}:
       - Run extract → simulate → judge against the calibration dataset,
         using that variant's extraction prompt.
       - Outputs go under ``data_cal_<variant>/`` (we reuse build's
         analysts.json by symlink/copy).
       - Aggregate hit rate is recorded.

  3. Pick the winning variant by aggregate hit rate. Tie-break to V1 (simpler
     schema) within ±2pp, matching the paper's calibration-50 + earliest-round
     tie-break in spirit.

  4. Build the TEST dataset holding out ``2026-q1``: training = all calls
     including 2025-Q4. Saved under ``data_test/``.

  5. If winner == V1, reuse the prior 2026-Q1 results in ``data/``; otherwise
     run extract → simulate → judge against the test dataset using the winner.

  6. Print the calibration table and the final test result vs V1 baseline.

Usage:
  python3 src/run_schema_search.py
  DRY_RUN=1 python3 src/run_schema_search.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from run_pipeline import run as run_pipeline  # noqa: E402

ROOT = os.path.dirname(HERE)
PARSED = os.path.join(ROOT, "parsed")


VARIANTS = [
    {"name": "V1", "prompt": "extract_bde_v1.md"},
    {"name": "V2", "prompt": "extract_bde_v2.md"},
    {"name": "V3", "prompt": "extract_bde_v3.md"},
]

# Tie-break: pick a simpler schema if it's within this many percentage points
# of the leader. Set generously since calibration N is small (~10 questions).
TIE_BREAK_PP = 2.0


def build_dataset(held_out: str, out_dir: str) -> None:
    """Run build_analyst_dataset.py to populate analysts.json and
    analysts_test.json under ``out_dir``.
    """
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        sys.executable,
        os.path.join(HERE, "build_analyst_dataset.py"),
        "--held-out", held_out,
        "--out-dir", out_dir,
    ]
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def copy_dataset(src_dir: str, dst_dir: str) -> None:
    os.makedirs(dst_dir, exist_ok=True)
    for fname in ("analysts.json", "analysts_test.json"):
        shutil.copy2(os.path.join(src_dir, fname), os.path.join(dst_dir, fname))


def main() -> None:
    print("=" * 80)
    print("OPTION A: schema search")
    print("=" * 80)

    cal_master = os.path.join(ROOT, "data_cal")
    test_master = os.path.join(ROOT, "data_test")

    # --- 1. Build calibration split (training = pre-2025-Q4; hold out 2025-Q4)
    print("\n## 1. Building calibration split (hold out 2025-q4)")
    build_dataset("2025-q4", cal_master)

    # --- 2. Run each variant on the calibration split ---
    print("\n## 2. Running variants on calibration split")
    cal_results: dict[str, dict] = {}
    for v in VARIANTS:
        name = v["name"]
        var_dir = os.path.join(ROOT, f"data_cal_{name}")
        copy_dataset(cal_master, var_dir)
        print(f"\n--- {name} | prompt={v['prompt']} | dir={var_dir} ---")
        t0 = time.time()
        summary = run_pipeline(
            data_dir=var_dir,
            extraction_prompt=v["prompt"],
        )
        elapsed = time.time() - t0
        cal_results[name] = summary
        print(
            f"{name}: hit_rate={summary['hit_rate_exact_or_partial']:.3f} "
            f"({summary['n_exact']} exact + {summary['n_partial']} partial / "
            f"{summary['n_actual']}); {elapsed:.0f}s"
        )

    # --- 3. Pick winner ---
    print("\n## 3. Calibration results")
    print(f"{'variant':>8s} {'hit_rate':>10s} {'n_actual':>10s} {'exact':>7s} {'partial':>9s} {'miss':>6s}")
    for v in VARIANTS:
        s = cal_results[v["name"]]
        print(
            f"{v['name']:>8s} {s['hit_rate_exact_or_partial']:>10.3f} "
            f"{s['n_actual']:>10d} {s['n_exact']:>7d} {s['n_partial']:>9d} {s['n_miss']:>6d}"
        )

    # Tie-break: among variants within TIE_BREAK_PP/100 of the top, pick the
    # earliest-listed (V1 < V2 < V3).
    best_rate = max(s["hit_rate_exact_or_partial"] for s in cal_results.values())
    threshold = best_rate - TIE_BREAK_PP / 100.0
    winner = None
    for v in VARIANTS:
        if cal_results[v["name"]]["hit_rate_exact_or_partial"] >= threshold:
            winner = v
            break
    assert winner is not None
    print(
        f"\nWinner: {winner['name']} "
        f"(hit_rate={cal_results[winner['name']]['hit_rate_exact_or_partial']:.3f}, "
        f"top={best_rate:.3f}, tie-break window=±{TIE_BREAK_PP:.1f}pp)"
    )

    # --- 4. Build test split (training = all 16 quarters, hold out 2026-Q1) ---
    print("\n## 4. Building test split (hold out 2026-q1)")
    build_dataset("2026-q1", test_master)

    # --- 5. Run winner on test split (or reuse V1 result) ---
    print(f"\n## 5. Running winner ({winner['name']}) on 2026-Q1 test")
    test_dir = os.path.join(ROOT, f"data_test_{winner['name']}")
    copy_dataset(test_master, test_dir)
    test_summary = run_pipeline(
        data_dir=test_dir,
        extraction_prompt=winner["prompt"],
    )

    # --- 6. Compare to V1 baseline ---
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print("\nCalibration (held out 2025-Q4):")
    print(f"{'variant':>8s} {'hit_rate':>10s} {'n_actual':>10s}")
    for v in VARIANTS:
        s = cal_results[v["name"]]
        marker = "  ← winner" if v["name"] == winner["name"] else ""
        print(f"{v['name']:>8s} {s['hit_rate_exact_or_partial']:>10.3f} {s['n_actual']:>10d}{marker}")

    print("\nTest (held out 2026-Q1):")
    print(
        f"  V1 (baseline, prior run): hit_rate=0.500 (1 exact + 4 partial / 10)"
    )
    print(
        f"  {winner['name']} (winner): "
        f"hit_rate={test_summary['hit_rate_exact_or_partial']:.3f} "
        f"({test_summary['n_exact']} exact + {test_summary['n_partial']} partial / "
        f"{test_summary['n_actual']})"
    )

    # Save composite summary
    out = {
        "calibration": {v["name"]: cal_results[v["name"]] for v in VARIANTS},
        "winner": winner["name"],
        "test_summary": test_summary,
    }
    with open(os.path.join(ROOT, "schema_search_summary.json"), "w") as fp:
        json.dump(out, fp, indent=2)
    print(f"\nWrote {os.path.join(ROOT, 'schema_search_summary.json')}")


if __name__ == "__main__":
    main()
