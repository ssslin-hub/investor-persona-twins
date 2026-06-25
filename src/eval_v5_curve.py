"""Phase 19: evaluate v5 K-curve {K=12,14,16,18,20} under both gpt-5 and
gpt-5-mini, 5 runs each. For K>=16 also run chunked B4 precision (50-cand
chunks) because Phase 11 showed truncation kicks in at K=16+.

Output: data_auto/final_eval_<K>q_v5/v5_curve/{model}/run_{1..5}/
        data_auto/final_eval_<K>q_v5/v5_curve/{model}/aggregate.json
        data_auto/phase19_aggregate.json
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

K_VALUES = [12, 14, 16, 18, 20]
MODELS = ["gpt-5", "gpt-5-mini"]
N_RUNS = 5
CHUNK_K_THRESHOLD = 16  # K>=16 also gets chunked precision rerun


def run_one(in_summary: str, out_dir: str, model: str, do_chunked: bool) -> None:
    os.makedirs(out_dir, exist_ok=True)
    env = os.environ.copy()
    env["EVAL_MODEL"] = model
    for sub in ("pool", "b2", "b4"):
        log = os.path.join(out_dir, f"{sub}.log")
        cmd = ["python3", EVAL_SCRIPT, sub, "--in-summary", in_summary, "--out-dir", out_dir]
        with open(log, "w") as fp:
            subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, env=env, cwd=ROOT, check=False)
    if do_chunked:
        cmd = ["python3", CHUNKED_SCRIPT, "--in-summary", in_summary,
               "--out-dir", out_dir, "--chunk-size", "50"]
        with open(os.path.join(out_dir, "chunked.log"), "w") as fp:
            subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, env=env, cwd=ROOT, check=False)


def collect(out_dir: str, do_chunked: bool) -> dict:
    o = {}
    try:
        b2 = json.load(open(os.path.join(out_dir, "b2_summary.json")))
        o["b2_binary_rate"] = b2["binary_match_rate"]
        o["b2_strong_count"] = b2["strong_match_count"]
        o["b2_avg_score"] = b2["average_match_score_0_to_4"]
    except FileNotFoundError:
        pass
    try:
        b4 = json.load(open(os.path.join(out_dir, "b4.json")))
        m = b4.get("set_metrics", {})
        d = b4.get("derived", {})
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
    if do_chunked:
        try:
            ch = json.load(open(os.path.join(out_dir, "b4_precision_chunked.json")))
            o["chunked_useful"] = ch.get("useful_count")
            o["chunked_strong"] = ch.get("strong_count")
            o["chunked_total"] = ch.get("n_total_candidates")
            o["chunked_useful_rate_all"] = ch.get("useful_rate_on_all")
            o["chunked_strong_rate_all"] = ch.get("strong_rate_on_all")
        except FileNotFoundError:
            pass
    return o


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"mean": None, "min": None, "max": None, "runs": []}
    return {"mean": sum(vals)/len(vals), "min": min(vals), "max": max(vals), "runs": vals}


def main() -> None:
    aggregate_all = {}
    for K in K_VALUES:
        in_summary = os.path.join(ROOT, "data_auto", f"final_eval_{K}q_v5", "summary.json")
        if not os.path.exists(in_summary):
            print(f"  ! K={K}: missing {in_summary}; skip"); continue
        do_chunked = K >= CHUNK_K_THRESHOLD
        aggregate_all[f"K={K}"] = {}
        for model in MODELS:
            model_dir = os.path.join(ROOT, "data_auto", f"final_eval_{K}q_v5", "v5_curve", model)
            os.makedirs(model_dir, exist_ok=True)
            runs = []
            for i in range(1, N_RUNS + 1):
                out_dir = os.path.join(model_dir, f"run_{i}")
                cached = os.path.exists(os.path.join(out_dir, "b4.json"))
                if do_chunked:
                    cached = cached and os.path.exists(os.path.join(out_dir, "b4_precision_chunked.json"))
                if not cached:
                    print(f"=== K={K} | {model} | run {i}/{N_RUNS} (chunked={do_chunked}) ===")
                    run_one(in_summary, out_dir, model, do_chunked)
                else:
                    print(f"=== K={K} | {model} | run {i}/{N_RUNS} (cached) ===")
                runs.append(collect(out_dir, do_chunked))
            agg = {"n_runs": len(runs), "K": K, "model": model}
            for key in ("b2_binary_rate","b2_strong_count","b2_avg_score",
                        "b4_cov_rate","b4_cov_strong","b4_prec_rate","b4_prec_strong",
                        "b4_prec_rows","b4_id_matched",
                        "chunked_useful_rate_all","chunked_strong_rate_all","chunked_useful"):
                agg[key] = stats([r.get(key) for r in runs])
            agg["per_run"] = runs
            with open(os.path.join(model_dir, "aggregate.json"), "w") as f:
                json.dump(agg, f, indent=2)
            aggregate_all[f"K={K}"][model] = agg
            print(f"  K={K}/{model}: B2 bin {agg['b2_binary_rate']['runs']} mean={agg['b2_binary_rate']['mean']}")
    with open(os.path.join(ROOT, "data_auto", "phase19_aggregate.json"), "w") as f:
        json.dump(aggregate_all, f, indent=2)


if __name__ == "__main__":
    main()
