"""v5 K=2 simulator: rerun 3 times, compare pairwise B2 across reruns per twin.
Output: data_auto/final_eval_2q_v5/run_{1,2,3}/summary.json + pairwise_b2.json
"""

from __future__ import annotations

import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import build_simulator_prompt, stub_predictions, load_text  # noqa: E402

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
V5_PERSONAS = os.path.join(ROOT, "data", "personas_v5")
AUTO_PERSONAS = os.path.join(DATA_AUTO, "final_personas")
SIM_PROMPT = os.path.join(PROMPTS, "simulate_questions_2q.md")
B2_TPL = open(os.path.join(PROMPTS, "b2_eval.md")).read()
OUT_BASE = os.path.join(DATA_AUTO, "final_eval_2q_v5")

ALL_11 = ["matthew boss","steven wieczynski","brandt montour","james hardiman",
          "lizzie dove","robin farley","vince ciepiel","sharon zackfia",
          "andrew didora","xian siew","kevin kopelman"]
COLD = ["xian siew","kevin kopelman"]


def _safe(s): return s.replace(" ", "_")


def _load_persona(name):
    p = os.path.join(AUTO_PERSONAS, "_fallback.json") if name in COLD else os.path.join(V5_PERSONAS, f"{_safe(name)}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def sim_one_run(run_idx: int) -> dict:
    out_dir = os.path.join(OUT_BASE, f"run_{run_idx}")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    out_summary = os.path.join(out_dir, "summary.json")
    if os.path.exists(out_summary):
        return json.load(open(out_summary))
    sim_tpl = load_text(SIM_PROMPT)
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]
    actuals_by = test["per_analyst_actual_questions"]
    per = {}
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals: continue
        persona = _load_persona(name)
        if persona is None:
            print(f"  ! {name}: no persona"); continue
        prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        try:
            out = call_llm(prompt, expect_json=True, dry_run_stub=stub_predictions(name),
                           log_to=os.path.join(log_dir, f"sim_{_safe(name)}.txt"))
            pred = parse_json_strict(out)
        except Exception as e:
            print(f"  ! {name}: {e}"); pred = stub_predictions(name)
        pq = pred.get("predicted_questions", [])
        if len(pq) > 2: pred["predicted_questions"] = pq[:2]
        per[name] = {"predictions": pred}
        print(f"  run {run_idx} {name:25s} K={len(pq)}")
    summary = {"K": 2, "source": "v5", "run": run_idx, "per_analyst": per}
    with open(out_summary, "w") as f: json.dump(summary, f, indent=2)
    return summary


def b2_pair_set(analyst, set_a, anchor_b, log_to):
    sim = {"analyst_name": analyst, "predicted_questions": set_a}
    actuals = [{"tuple_id": f"{analyst}-anchor", "analyst_name": analyst,
                "call": "v5_k2_stability", "question": anchor_b.get("question_text","")}]
    prompt = (B2_TPL.replace("{{SIMULATION_JSON}}", json.dumps(sim, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
    try:
        out = call_llm(prompt, model="gpt-5", expect_json=True,
                       dry_run_stub={"match_score_0_to_4":0}, log_to=log_to)
        ev = parse_json_strict(out)
        return int(ev.get("match_score_0_to_4") or 0)
    except Exception as e:
        print(f"  ! {analyst}: {e}"); return -1


def main():
    os.makedirs(OUT_BASE, exist_ok=True)
    runs = [sim_one_run(i) for i in range(1, 4)]
    print("\n=== pairwise B2 (gpt-5) across 3 reruns ===")
    log_dir = os.path.join(OUT_BASE, "pairwise_logs")
    os.makedirs(log_dir, exist_ok=True)
    result = {}
    for name in ALL_11:
        per_run_top = [(r['per_analyst'].get(name) or {}).get('predictions', {}).get('predicted_questions', []) for r in runs]
        if not any(per_run_top):
            continue
        scores = {}
        for i, j in itertools.combinations(range(3), 2):
            if not per_run_top[i] or not per_run_top[j]: continue
            anchor_j = per_run_top[j][0]
            anchor_i = per_run_top[i][0]
            log1 = os.path.join(log_dir, f"{_safe(name)}_r{i+1}_vs_r{j+1}.txt")
            log2 = os.path.join(log_dir, f"{_safe(name)}_r{j+1}_vs_r{i+1}.txt")
            s_ij = b2_pair_set(name, per_run_top[i], anchor_j, log1)
            s_ji = b2_pair_set(name, per_run_top[j], anchor_i, log2)
            scores[f"{i+1}_vs_{j+1}"] = (s_ij + s_ji) / 2
            print(f"  {name:25s} r{i+1}↔{j+1}: {s_ij}/{s_ji} avg={scores[f'{i+1}_vs_{j+1}']}")
        vals = [v for v in scores.values() if v >= 0]
        result[name] = {
            "pair_scores": scores,
            "mean_similarity": sum(vals)/len(vals) if vals else None,
            "min_similarity": min(vals) if vals else None,
        }
    with open(os.path.join(OUT_BASE, "pairwise_b2.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote {OUT_BASE}/pairwise_b2.json")


if __name__ == "__main__":
    main()
