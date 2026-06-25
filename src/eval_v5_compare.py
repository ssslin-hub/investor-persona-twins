"""Phase 17: run B2+B4 3 times each under {gpt-5, gpt-5-mini} for 3 settings
(v5 K=10, V1 K=10, Auto K=10). Aggregate mean ± spread per setting per model.

Usage: python3 src/eval_v5_compare.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVAL_SCRIPT = os.path.join(HERE, "eval_gpt5_generic.py")

SETTINGS = [
    ("v5",   "data_auto/final_eval_10q_v5/summary.json",   "data_auto/final_eval_10q_v5"),
    ("v1",   "data_auto/final_eval_10q_v1/summary.json",   "data_auto/final_eval_10q_v1"),
    ("auto", "data_auto/final_eval_10q_auto/summary.json", "data_auto/final_eval_10q_auto"),
]
MODELS = ["gpt-5", "gpt-5-mini"]
N_RUNS = 5


def run_eval(summary_path: str, out_dir: str, model: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    env = os.environ.copy()
    env["EVAL_MODEL"] = model
    for sub in ("pool", "b2", "b4"):
        log = os.path.join(out_dir, f"{sub}.log")
        cmd = ["python3", EVAL_SCRIPT, sub, "--in-summary", summary_path, "--out-dir", out_dir]
        with open(log, "w") as fp:
            subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, env=env, cwd=ROOT, check=False)


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
    return o


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"mean": None, "max": None, "min": None, "spread": None, "runs": []}
    return {"mean": sum(vals)/len(vals), "max": max(vals), "min": min(vals),
            "spread": max(vals)-min(vals), "runs": vals}


def main() -> None:
    aggregate_all = {}
    for setting_name, summary_rel, base_rel in SETTINGS:
        in_summary = os.path.join(ROOT, summary_rel)
        if not os.path.exists(in_summary):
            print(f"! missing {in_summary}; skip {setting_name}")
            continue
        aggregate_all[setting_name] = {}
        for model in MODELS:
            model_dir = os.path.join(ROOT, base_rel, "v5_compare", model)
            os.makedirs(model_dir, exist_ok=True)
            runs = []
            for i in range(1, N_RUNS + 1):
                out_dir = os.path.join(model_dir, f"run_{i}")
                if not os.path.exists(os.path.join(out_dir, "b4.json")):
                    print(f"=== {setting_name} | {model} | run {i}/{N_RUNS} ===")
                    run_eval(in_summary, out_dir, model)
                else:
                    print(f"=== {setting_name} | {model} | run {i}/{N_RUNS} (cached) ===")
                runs.append(collect(out_dir))
            agg = {
                "n_runs": N_RUNS,
                "model": model,
                "b2_binary_rate": stats([r.get("b2_binary_rate") for r in runs]),
                "b2_strong_count": stats([r.get("b2_strong_count") for r in runs]),
                "b2_avg_score": stats([r.get("b2_avg_score") for r in runs]),
                "b4_cov_rate": stats([r.get("b4_cov_rate") for r in runs]),
                "b4_cov_strong": stats([r.get("b4_cov_strong") for r in runs]),
                "b4_prec_rate": stats([r.get("b4_prec_rate") for r in runs]),
                "b4_prec_strong": stats([r.get("b4_prec_strong") for r in runs]),
                "b4_id_matched": stats([r.get("b4_id_matched") for r in runs]),
                "per_run": runs,
            }
            with open(os.path.join(model_dir, "aggregate.json"), "w") as f:
                json.dump(agg, f, indent=2)
            aggregate_all[setting_name][model] = agg
            print(f"  {setting_name}/{model}: B2 bin mean={agg['b2_binary_rate']['mean']} spread={agg['b2_binary_rate']['spread']}")
    with open(os.path.join(ROOT, "data_auto", "phase17_aggregate.json"), "w") as f:
        json.dump(aggregate_all, f, indent=2)


if __name__ == "__main__":
    main()
