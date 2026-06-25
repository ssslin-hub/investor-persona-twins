"""Phase 13a: 3-run B2+B4 variance on a fixed set of summary.json inputs.
Reuses eval_gpt5_generic's b2/b4 logic (via subprocess shell-out so each run is
fully independent, no shared LLM state).

Usage:
  python3 src/eval_gpt5_variance.py --settings <name1>:<summary_path1> <name2>:<summary_path2> ... --n-runs 3

For each setting, runs B2 + B4 n times under data_auto/.../variance/run_{i}/.
Aggregates per-setting variance metrics into variance/aggregate.json and a
consolidated table in reports/phase13_variance.md.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVAL_SCRIPT = os.path.join(HERE, "eval_gpt5_generic.py")


def run_once(in_summary: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for sub in ("pool", "b2", "b4"):
        cmd = ["python3", EVAL_SCRIPT, sub, "--in-summary", in_summary, "--out-dir", out_dir]
        env = os.environ.copy()
        log = os.path.join(out_dir, f"{sub}.log")
        with open(log, "w") as fp:
            subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, env=env, check=False, cwd=ROOT)


def collect_run(out_dir: str) -> dict:
    b2 = json.load(open(os.path.join(out_dir, "b2_summary.json")))
    cells = json.load(open(os.path.join(out_dir, "b2_per_actual.json")))["cells"]
    b4 = json.load(open(os.path.join(out_dir, "b4.json")))
    m = b4.get("set_metrics", {})
    d = b4.get("derived", {})
    return {
        "b2_binary_rate": b2["binary_match_rate"],
        "b2_strong_count": b2["strong_match_count"],
        "b2_avg_score": b2["average_match_score_0_to_4"],
        "b2_n_eval": b2["evaluated_count"],
        "b2_cell_scores": {
            (f"robin_farley-actual-{c.get('robin_actual_index',0)}" if c['analyst_name']=='robin farley'
             else f"{c['analyst_name'].replace(' ','_')}-actual-0"):
            c.get("match_score_0_to_4")
            for c in cells
        },
        "b4_actual_count": b4.get("actual_question_count"),
        "b4_predicted_count": b4.get("predicted_question_count"),
        "b4_coverage_count_raw": m.get("coverage_count"),
        "b4_coverage_rate_raw": m.get("coverage_rate"),
        "b4_useful_count_raw": m.get("useful_prediction_count"),
        "b4_precision_rate_raw": m.get("precision_rate"),
        "b4_precision_rows": len(b4.get("predicted_precision", [])),
        "b4_coverage_strong": d.get("coverage_strong_count"),
        "b4_precision_strong": d.get("precision_strong_count"),
        "b4_identity_matched": d.get("identity_matched_coverage"),
    }


def aggregate(runs: list[dict]) -> dict:
    def stats(vals):
        vals = [v for v in vals if v is not None]
        if not vals:
            return {"mean": None, "max": None, "min": None, "spread": None}
        return {
            "mean": sum(vals) / len(vals),
            "max": max(vals),
            "min": min(vals),
            "spread": max(vals) - min(vals),
            "runs": vals,
        }
    # cell stability
    all_cells = set()
    for r in runs:
        all_cells.update(r["b2_cell_scores"].keys())
    cell_stable = 0
    cell_details = {}
    for c in all_cells:
        vals = [r["b2_cell_scores"].get(c) for r in runs]
        cell_details[c] = vals
        if len(set(vals)) == 1 and None not in vals:
            cell_stable += 1
    n_cells = len(all_cells)
    return {
        "n_runs": len(runs),
        "b2_binary_rate": stats([r["b2_binary_rate"] for r in runs]),
        "b2_strong_count": stats([r["b2_strong_count"] for r in runs]),
        "b2_avg_score": stats([r["b2_avg_score"] for r in runs]),
        "b2_cells_stable": cell_stable,
        "b2_cells_total": n_cells,
        "b2_cell_scores_by_run": cell_details,
        "b4_coverage_rate_raw": stats([r["b4_coverage_rate_raw"] for r in runs]),
        "b4_precision_rate_raw": stats([r["b4_precision_rate_raw"] for r in runs]),
        "b4_useful_count_raw": stats([r["b4_useful_count_raw"] for r in runs]),
        "b4_precision_rows": stats([r["b4_precision_rows"] for r in runs]),
        "b4_coverage_strong": stats([r["b4_coverage_strong"] for r in runs]),
        "b4_precision_strong": stats([r["b4_precision_strong"] for r in runs]),
        "b4_identity_matched": stats([r["b4_identity_matched"] for r in runs]),
        "per_run": runs,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", nargs="+", required=True,
                    help="name:summary_path pairs")
    ap.add_argument("--n-runs", type=int, default=3)
    args = ap.parse_args()

    for spec in args.settings:
        name, summary = spec.split(":", 1)
        base_dir = os.path.dirname(summary)
        var_dir = os.path.join(base_dir, "variance")
        os.makedirs(var_dir, exist_ok=True)
        runs = []
        for i in range(1, args.n_runs + 1):
            out_dir = os.path.join(var_dir, f"run_{i}")
            if not os.path.exists(os.path.join(out_dir, "b4.json")):
                print(f"=== {name} run {i}/{args.n_runs} ===")
                run_once(summary, out_dir)
            else:
                print(f"=== {name} run {i}/{args.n_runs} (cached) ===")
            runs.append(collect_run(out_dir))
        agg = aggregate(runs)
        with open(os.path.join(var_dir, "aggregate.json"), "w") as f:
            json.dump(agg, f, indent=2)
        print(f"  binary_rate runs={agg['b2_binary_rate']['runs']} "
              f"mean={agg['b2_binary_rate']['mean']:.3f} spread={agg['b2_binary_rate']['spread']:.3f}")
        print(f"  cells stable {agg['b2_cells_stable']}/{agg['b2_cells_total']}")
        print(f"  b4_cov rate runs={agg['b4_coverage_rate_raw']['runs']} spread={agg['b4_coverage_rate_raw']['spread']:.3f}")


if __name__ == "__main__":
    main()
