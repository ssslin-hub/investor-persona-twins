"""Backfill the B2 strong_match (score >= 4) metric across all existing
evaluation directories that already have per-cell B2 JSONs (or B2 nested
inside summary.json under per_analyst/per_turn).

Scans the following candidate dirs and (re)writes an enriched summary at
data_auto/<dir>/b2_aggregated.json including:
  - evaluated_count
  - binary_match_count, binary_match_rate (score >= 3)
  - strong_match_count, strong_match_rate (score >= 4)
  - average_match_score_0_to_4

Also prints a side-by-side console table for all settings discovered.
"""

from __future__ import annotations

import json
import os
import sys
from glob import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_AUTO = os.path.join(ROOT, "data_auto")


def collect_b2_cells_from_dir(d: str) -> list[dict]:
    """Return list of B2 cell dicts found in directory d."""
    cells: list[dict] = []
    # Pattern A: per-analyst files under d/b2/*.json
    b2_dir = os.path.join(d, "b2")
    if os.path.isdir(b2_dir):
        for fp in sorted(glob(os.path.join(b2_dir, "*.json"))):
            cells.append(json.load(open(fp)))
    # Pattern B: cells nested in summary.json under per_analyst[name].b2
    sj = os.path.join(d, "summary.json")
    if not cells and os.path.exists(sj):
        s = json.load(open(sj))
        for name, pa in (s.get("per_analyst") or {}).items():
            if isinstance(pa.get("b2"), dict):
                cells.append(pa["b2"])
    # Pattern C: per-turn cells inside predictions_by_turn.json
    pt = os.path.join(d, "predictions_by_turn.json")
    if not cells and os.path.exists(pt):
        for t in json.load(open(pt)):
            if isinstance(t.get("b2"), dict):
                cells.append(t["b2"])
    return cells


def aggregate(cells: list[dict]) -> dict:
    scored = [c for c in cells if isinstance(c.get("match_score_0_to_4"), (int, float))]
    n = len(scored)
    binary = sum(1 for c in scored if c.get("binary_match"))
    strong = sum(1 for c in scored if (c.get("match_score_0_to_4") or 0) >= 4)
    avg = sum(c["match_score_0_to_4"] for c in scored) / max(1, n) if scored else 0
    return {
        "evaluated_count": n,
        "binary_match_count": binary,
        "binary_match_rate": binary / max(1, n),
        "strong_match_count": strong,
        "strong_match_rate": strong / max(1, n),
        "average_match_score_0_to_4": avg,
    }


def main() -> None:
    candidate_dirs = [
        ("Auto cold 2-3Q (9 returning)", os.path.join(DATA_AUTO, "final_eval")),
        ("Auto cold 1Q (11)", os.path.join(DATA_AUTO, "final_eval_1q")),
        ("V1 K=5", os.path.join(DATA_AUTO, "final_eval_5q_v1")),
        ("Auto K=5", os.path.join(DATA_AUTO, "final_eval_5q_auto")),
        ("V1 K=10", os.path.join(DATA_AUTO, "final_eval_10q_v1")),
        ("Auto K=10", os.path.join(DATA_AUTO, "final_eval_10q_auto")),
        ("Conv K=1", os.path.join(DATA_AUTO, "final_eval_conv")),
        ("Conv K=10", os.path.join(DATA_AUTO, "final_eval_conv_10q")),
    ]

    print(f"{'Setting':28s} {'N':>4s} {'binary>=3':>11s} {'strong>=4':>11s} {'avg_score':>10s}")
    print("-" * 70)
    out = {}
    for label, d in candidate_dirs:
        if not os.path.isdir(d):
            print(f"{label:28s} (dir missing)")
            continue
        cells = collect_b2_cells_from_dir(d)
        if not cells:
            print(f"{label:28s} (no B2 cells found)")
            continue
        agg = aggregate(cells)
        print(f"{label:28s} {agg['evaluated_count']:>4d} "
              f"{agg['binary_match_count']:>3d}/{agg['evaluated_count']:<3d}={agg['binary_match_rate']:.3f} "
              f"{agg['strong_match_count']:>3d}/{agg['evaluated_count']:<3d}={agg['strong_match_rate']:.3f} "
              f"{agg['average_match_score_0_to_4']:>10.3f}")
        with open(os.path.join(d, "b2_aggregated.json"), "w") as f:
            json.dump(agg, f, indent=2)
        out[label] = agg

    print()
    out_path = os.path.join(DATA_AUTO, "b2_aggregated_all.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
