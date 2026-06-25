"""Phase 14: gpt-5-mini 3-run B2+B4+chunked-precision evaluator on the same 11
settings Phase 12 used. Compare against gpt-5 single-run results.

Each setting × each run produces:
  <setting>/gpt5_mini/run_{i}/{raw_pool,b2_per_actual,b2_summary,b4,b4_precision_chunked}.json
Aggregated into <setting>/gpt5_mini/aggregate.json

Then writes reports/phase14_mini_vs_gpt5.md side-by-side comparison.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVAL_SCRIPT = os.path.join(HERE, "eval_gpt5_generic.py")
CHUNKED_SCRIPT = os.path.join(HERE, "b4_chunked_precision.py")

SETTINGS = [
    ("parallel_K16_v1",    "data_auto/final_eval_16q_v1"),
    ("parallel_K18_auto",  "data_auto/final_eval_18q_auto"),
    ("parallel_K20_v1",    "data_auto/final_eval_20q_v1"),
    ("parallel_K20_auto",  "data_auto/final_eval_20q_auto"),
    ("seq_K14_v1",         "data_auto/final_eval_seq_14q_v1"),
    ("seq_K14_auto",       "data_auto/final_eval_seq_14q_auto"),
    ("seq_K16_v1",         "data_auto/final_eval_seq_16q_v1"),
    ("seq_K18_v1",         "data_auto/final_eval_seq_18q_v1"),
    ("seq_K18_auto",       "data_auto/final_eval_seq_18q_auto"),
    ("seq_K20_v1",         "data_auto/final_eval_seq_20q_v1"),
    ("seq_K20_auto",       "data_auto/final_eval_seq_20q_auto"),
]


def run_one(in_summary: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    env = os.environ.copy()
    env["EVAL_MODEL"] = "gpt-5-mini"
    for sub in ("pool", "b2", "b4"):
        cmd = ["python3", EVAL_SCRIPT, sub, "--in-summary", in_summary, "--out-dir", out_dir]
        log = os.path.join(out_dir, f"{sub}.log")
        with open(log, "w") as fp:
            subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, env=env, cwd=ROOT, check=False)
    # Chunked precision (50-cand chunks)
    cmd = ["python3", CHUNKED_SCRIPT, "--in-summary", in_summary,
           "--out-dir", out_dir, "--chunk-size", "50"]
    with open(os.path.join(out_dir, "chunked.log"), "w") as fp:
        subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, env=env, cwd=ROOT, check=False)


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"mean": None, "max": None, "min": None, "spread": None, "runs": []}
    return {"mean": sum(vals) / len(vals), "max": max(vals), "min": min(vals),
            "spread": max(vals) - min(vals), "runs": vals}


def collect(out_dir: str) -> dict:
    o = {}
    try:
        b2 = json.load(open(os.path.join(out_dir, "b2_summary.json")))
        o["b2_binary_rate"] = b2["binary_match_rate"]
        o["b2_strong_count"] = b2["strong_match_count"]
        o["b2_avg_score"] = b2["average_match_score_0_to_4"]
        o["b2_n_eval"] = b2["evaluated_count"]
    except FileNotFoundError:
        pass
    try:
        b4 = json.load(open(os.path.join(out_dir, "b4.json")))
        m = b4.get("set_metrics", {})
        d = b4.get("derived", {})
        o["b4_cov_count"] = m.get("coverage_count")
        o["b4_cov_rate"] = m.get("coverage_rate")
        o["b4_useful_count"] = m.get("useful_prediction_count")
        o["b4_prec_rate"] = m.get("precision_rate")
        o["b4_prec_rows"] = len(b4.get("predicted_precision", []))
        o["b4_predicted_count"] = b4.get("predicted_question_count")
        o["b4_actual_count"] = b4.get("actual_question_count")
        o["b4_cov_strong"] = d.get("coverage_strong_count")
        o["b4_prec_strong"] = d.get("precision_strong_count")
        o["b4_id_matched"] = d.get("identity_matched_coverage")
    except FileNotFoundError:
        pass
    try:
        ch = json.load(open(os.path.join(out_dir, "b4_precision_chunked.json")))
        o["chunked_useful"] = ch.get("useful_count")
        o["chunked_strong"] = ch.get("strong_count")
        o["chunked_n_eval"] = ch.get("n_evaluated_candidates")
        o["chunked_total"] = ch.get("n_total_candidates")
        o["chunked_useful_rate_eval"] = ch.get("useful_rate_on_eval")
        o["chunked_useful_rate_all"] = ch.get("useful_rate_on_all")
    except FileNotFoundError:
        pass
    return o


def main() -> None:
    summary_per_setting = {}
    for name, base_dir in SETTINGS:
        in_summary = os.path.join(base_dir, "summary.json")
        if not os.path.exists(in_summary):
            print(f"  ! {name}: missing {in_summary}; skip")
            continue
        mini_dir = os.path.join(base_dir, "gpt5_mini")
        os.makedirs(mini_dir, exist_ok=True)
        runs = []
        for i in range(1, 6):
            out_dir = os.path.join(mini_dir, f"run_{i}")
            if not os.path.exists(os.path.join(out_dir, "b4_precision_chunked.json")):
                print(f"=== {name} mini run {i}/3 ===")
                run_one(in_summary, out_dir)
            else:
                print(f"=== {name} mini run {i}/3 (cached) ===")
            runs.append(collect(out_dir))
        agg = {
            "n_runs": len(runs),
            "b2_binary_rate": stats([r.get("b2_binary_rate") for r in runs]),
            "b2_strong_count": stats([r.get("b2_strong_count") for r in runs]),
            "b2_avg_score": stats([r.get("b2_avg_score") for r in runs]),
            "b4_cov_rate": stats([r.get("b4_cov_rate") for r in runs]),
            "b4_cov_strong": stats([r.get("b4_cov_strong") for r in runs]),
            "b4_prec_rate_raw": stats([r.get("b4_prec_rate") for r in runs]),
            "b4_prec_rows": stats([r.get("b4_prec_rows") for r in runs]),
            "b4_id_matched": stats([r.get("b4_id_matched") for r in runs]),
            "chunked_useful_rate_all": stats([r.get("chunked_useful_rate_all") for r in runs]),
            "chunked_useful_rate_eval": stats([r.get("chunked_useful_rate_eval") for r in runs]),
            "chunked_n_eval": stats([r.get("chunked_n_eval") for r in runs]),
            "chunked_strong": stats([r.get("chunked_strong") for r in runs]),
            "per_run": runs,
        }
        with open(os.path.join(mini_dir, "aggregate.json"), "w") as f:
            json.dump(agg, f, indent=2)
        summary_per_setting[name] = agg
        print(f"  B2 binary: mean={agg['b2_binary_rate']['mean']} spread={agg['b2_binary_rate']['spread']}")
        print(f"  chunked useful_all: mean={agg['chunked_useful_rate_all']['mean']} spread={agg['chunked_useful_rate_all']['spread']}")


if __name__ == "__main__":
    main()
