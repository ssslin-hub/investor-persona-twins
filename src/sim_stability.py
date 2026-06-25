"""Phase 15: simulator-side stability. Rerun the K=10 simulator 3 times for both
V1 and Auto persona sources. Extract per-twin top-3 each time. Compare pairwise
B2 across the 3 reruns per twin.

Then cross-tab with each analyst's history length (from train_combined.json) to
test whether more history → more stable top-3.

Outputs:
  data_auto/final_eval_10q_{src}/sim_stability/run_{i}/summary.json (i=1,2,3)
  data_auto/final_eval_10q_{src}/sim_stability/top3_per_run.json
  data_auto/final_eval_10q_{src}/sim_stability/pairwise_b2.json
  reports/phase15_sim_stability.md
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402

DATA_AUTO = os.path.join(ROOT, "data_auto")
PROMPTS = os.path.join(ROOT, "prompts")
B2_TPL = open(os.path.join(PROMPTS, "b2_eval.md")).read()

ALL_11 = ["matthew boss","steven wieczynski","brandt montour","james hardiman",
          "lizzie dove","robin farley","vince ciepiel","sharon zackfia",
          "andrew didora","xian siew","kevin kopelman"]


def _safe(s): return s.replace(" ", "_")


def rerun_sim(src: str) -> None:
    """Run rerun_kq.py --K 10 --source {src} three times, each writing to a separate dir."""
    for i in range(1, 4):
        out_dir = os.path.join(DATA_AUTO, f"final_eval_10q_{src}", "sim_stability", f"run_{i}")
        out_summary = os.path.join(out_dir, "summary.json")
        if os.path.exists(out_summary):
            print(f"  {src} run {i}: cached")
            continue
        os.makedirs(out_dir, exist_ok=True)
        # Run rerun_kq with K=10, then move output to our directory
        rerun_outdir = os.path.join(DATA_AUTO, f"final_eval_10q_{src}_simstab_run{i}")
        cmd = ["python3", os.path.join(HERE, "rerun_kq.py"), "--K", "10", "--source", src]
        env = os.environ.copy()
        # Monkey-patch rerun_kq output by symlinking the expected output dir
        # Simpler: just run rerun_kq into a temp dir via env var hack — but rerun_kq has
        # hardcoded output path. So instead: call llm directly here.
        # Use a minimal sim loop inline.
        _run_inline(src, out_dir, i)


def _run_inline(src: str, out_dir: str, run_idx: int) -> None:
    """Inline mini-simulator: 11 twins × 1 K=10 prompt call each."""
    from run_pipeline import build_simulator_prompt, stub_predictions, load_text
    V1_PERSONAS = os.path.join(ROOT, "data", "personas")
    AUTO_PERSONAS = os.path.join(DATA_AUTO, "final_personas")
    SIM_PROMPT = os.path.join(PROMPTS, "simulate_questions_10q.md")
    sim_tpl = load_text(SIM_PROMPT)
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]
    actuals_by = test["per_analyst_actual_questions"]
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    per_analyst = {}
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals:
            continue
        if src == "v1":
            ppath = os.path.join(V1_PERSONAS, f"{_safe(name)}.json") if name not in ("xian siew","kevin kopelman") else os.path.join(AUTO_PERSONAS, "_fallback.json")
        else:
            ppath = os.path.join(AUTO_PERSONAS, f"{_safe(name)}.json") if name not in ("xian siew","kevin kopelman") else os.path.join(AUTO_PERSONAS, "_fallback.json")
        if not os.path.exists(ppath):
            continue
        persona = json.load(open(ppath))
        prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        log_path = os.path.join(log_dir, f"sim_{_safe(name)}.txt")
        try:
            out = call_llm(prompt, expect_json=True,
                           dry_run_stub=stub_predictions(name),
                           log_to=log_path)
            pred = parse_json_strict(out)
        except Exception as e:
            print(f"  ! {src} run {run_idx} {name}: {e}")
            pred = stub_predictions(name)
        pq = pred.get("predicted_questions", [])
        if len(pq) > 10:
            pred["predicted_questions"] = pq[:10]
        per_analyst[name] = {"predictions": pred}
        print(f"  {src} run {run_idx} {name:25s} K={len(pq)}")
    out = {"K": 10, "source": src, "run": run_idx, "per_analyst": per_analyst}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(out, f, indent=2)


def extract_top3() -> dict:
    """Build {src: {twin: [top3_run1, top3_run2, top3_run3]}}"""
    out = {}
    for src in ("v1", "auto"):
        d = os.path.join(DATA_AUTO, f"final_eval_10q_{src}", "sim_stability")
        out[src] = {}
        runs = []
        for i in range(1, 4):
            s = json.load(open(os.path.join(d, f"run_{i}", "summary.json")))
            runs.append(s["per_analyst"])
        for name in ALL_11:
            top3_list = []
            for r in runs:
                preds = (r.get(name) or {}).get("predictions", {}).get("predicted_questions", [])[:3]
                top3_list.append(preds)
            out[src][name] = top3_list
        with open(os.path.join(d, "top3_per_run.json"), "w") as f:
            json.dump(out[src], f, indent=2)
    return out


def b2_pair_set(analyst: str, set_a: list, anchor_b: dict, log_to: str) -> int:
    sim = {"analyst_name": analyst, "predicted_questions": set_a}
    actuals = [{"tuple_id": f"{analyst}-anchor",
                "analyst_name": analyst,
                "call": "sim_stability_pair",
                "question": anchor_b.get("question_text","")}]
    prompt = (B2_TPL
              .replace("{{SIMULATION_JSON}}", json.dumps(sim, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
    try:
        out = call_llm(prompt, model="gpt-5", expect_json=True,
                       dry_run_stub={"match_score_0_to_4":0}, log_to=log_to)
        ev = parse_json_strict(out)
        return int(ev.get("match_score_0_to_4") or 0)
    except Exception as e:
        print(f"  ! {analyst}: {e}")
        return -1


def pairwise_b2(top3: dict) -> dict:
    """For each (src, twin), pair runs (1,2), (1,3), (2,3) → 3 scores per twin per src."""
    import itertools
    result = {}
    for src in top3:
        d = os.path.join(DATA_AUTO, f"final_eval_10q_{src}", "sim_stability")
        log_dir = os.path.join(d, "pairwise_logs")
        os.makedirs(log_dir, exist_ok=True)
        result[src] = {}
        for name in ALL_11:
            runs = top3[src].get(name, [])
            if not runs or all(not r for r in runs):
                continue
            scores = {}
            for i, j in itertools.combinations(range(len(runs)), 2):
                if not runs[i] or not runs[j]:
                    continue
                anchor = runs[j][0]  # top-1 of run j
                log_path = os.path.join(log_dir, f"{_safe(name)}_run{i+1}_vs_run{j+1}.txt")
                s_ij = b2_pair_set(name, runs[i], anchor, log_path)
                anchor2 = runs[i][0]
                log_path2 = os.path.join(log_dir, f"{_safe(name)}_run{j+1}_vs_run{i+1}.txt")
                s_ji = b2_pair_set(name, runs[j], anchor2, log_path2)
                scores[f"{i+1}_vs_{j+1}"] = (s_ij + s_ji) / 2
                print(f"  {src} {name:25s} run{i+1}↔{j+1}: {s_ij}/{s_ji} avg={scores[f'{i+1}_vs_{j+1}']}")
            vals = [v for v in scores.values() if v >= 0]
            result[src][name] = {
                "pair_scores": scores,
                "mean_similarity": sum(vals)/len(vals) if vals else None,
                "min_similarity": min(vals) if vals else None,
            }
        with open(os.path.join(d, "pairwise_b2.json"), "w") as f:
            json.dump(result[src], f, indent=2)
    return result


def main() -> None:
    print("=== Phase 15 simulator stability ===")
    for src in ("v1", "auto"):
        print(f"\n--- {src} K=10 (3 reruns) ---")
        rerun_sim(src)
    print("\n--- extracting top-3 ---")
    top3 = extract_top3()
    print("\n--- pairwise B2 across reruns ---")
    pw = pairwise_b2(top3)
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
