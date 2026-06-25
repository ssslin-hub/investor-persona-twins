"""Build OpenAI Batch JSONL for evaluating 8 anchor-dedup filtered pools.

For each (source_K ∈ {10, 18}, L ∈ {2,3,4,5}) combo × n_runs × model:
  - 12 B2 per-actual cell requests (1 per analyst, robin split into 2)
  - 1 B4 set-level request
= 13 calls per (combo, run, model).

Total per evaluator: 8 × 5 × 13 = 520 requests.

custom_id schema:
  dedup_K{10|18}_L{2|3|4|5}__run{N}__{model}__b2__{analyst_safe}__{actual_idx}
  dedup_K{10|18}_L{2|3|4|5}__run{N}__{model}__b4
"""
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from run_pipeline import load_text

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
B2_TPL = load_text(os.path.join(PROMPTS, "b2_eval.md"))
B4_TPL = load_text(os.path.join(PROMPTS, "b4_eval.md"))

ANALYSTS = ['matthew boss','steven wieczynski','brandt montour','james hardiman','lizzie dove','robin farley','vince ciepiel','sharon zackfia','andrew didora','xian siew','kevin kopelman']


def safe(s): return re.sub(r"[^a-z0-9]+", "_", s.lower())


def find_pools():
    """Return list of (K, L, path)."""
    out = []
    for K in [10, 18]:
        for L in [2, 3, 4, 5]:
            p = f"{DATA_AUTO}/final_eval_{K}q_v5/anchor_dedup/L{L}/filtered_pool.json"
            if os.path.exists(p):
                out.append((K, L, p))
    return out


def build_b2_reqs(K, L, pool, actuals_by, model, run_i):
    reqs = []
    for name in ANALYSTS:
        cell = pool["per_analyst"].get(name)
        if not cell: continue
        preds = (cell.get("predictions") or {}).get("predicted_questions", [])
        actuals = actuals_by.get(name, [])
        if not preds or not actuals: continue
        if name == "robin farley":
            for ai, a in enumerate(actuals):
                sim_block = {"analyst_name": name, "predicted_questions": preds}
                actuals_b2 = [{"tuple_id": f"{name}-actual-{ai}", "analyst_name": name, "call": a.get("call"), "question": a.get("question")}]
                prompt = B2_TPL.replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2)).replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b2, indent=2))
                cid = f"dedup_K{K}_L{L}__run{run_i}__{model}__b2__{safe(name)}__{ai}"
                reqs.append({"custom_id": cid, "method": "POST", "url": "/v1/chat/completions",
                             "body": {"model": model, "messages": [{"role":"user","content":prompt}], "response_format":{"type":"json_object"}}})
        else:
            sim_block = {"analyst_name": name, "predicted_questions": preds}
            actuals_b2 = [{"tuple_id": f"{name}-actual-{i}", "analyst_name": name, "call": a.get("call"), "question": a.get("question")} for i, a in enumerate(actuals)]
            prompt = B2_TPL.replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2)).replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b2, indent=2))
            cid = f"dedup_K{K}_L{L}__run{run_i}__{model}__b2__{safe(name)}__0"
            reqs.append({"custom_id": cid, "method": "POST", "url": "/v1/chat/completions",
                         "body": {"model": model, "messages": [{"role":"user","content":prompt}], "response_format":{"type":"json_object"}}})
    return reqs


def build_b4_req(K, L, pool, actuals_by, model, run_i):
    candidates = []
    for name in ANALYSTS:
        cell = pool["per_analyst"].get(name)
        if not cell: continue
        for i, p in enumerate((cell.get("predictions") or {}).get("predicted_questions", [])):
            candidates.append({"candidate_id": f"{safe(name)}-pred-{i}", "question": p.get("question_text", "")})
    actuals = []
    for name in ANALYSTS:
        cell = pool["per_analyst"].get(name)
        if not cell: continue
        for ai, a in enumerate(actuals_by.get(name, [])):
            actuals.append({"actual_id": f"{safe(name)}-actual-{ai}", "question": a.get("question", "")})
    prompt = B4_TPL.replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(candidates, indent=2)).replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2))
    cid = f"dedup_K{K}_L{L}__run{run_i}__{model}__b4"
    return {"custom_id": cid, "method": "POST", "url": "/v1/chat/completions",
            "body": {"model": model, "messages": [{"role":"user","content":prompt}], "response_format":{"type":"json_object"}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=["gpt-5", "gpt-5-mini"])
    ap.add_argument("--n-runs", type=int, default=5)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    test = json.load(open(f"{DATA_AUTO}/test.json"))
    actuals_by = test["per_analyst_actual_questions"]
    pools = find_pools()
    print(f"Found {len(pools)} filtered pools")

    all_reqs = []
    for K, L, pool_path in pools:
        pool = json.load(open(pool_path))
        for run_i in range(1, args.n_runs+1):
            all_reqs.extend(build_b2_reqs(K, L, pool, actuals_by, args.model, run_i))
            all_reqs.append(build_b4_req(K, L, pool, actuals_by, args.model, run_i))

    with open(args.out, "w") as f:
        for r in all_reqs:
            f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(all_reqs)} requests to {args.out}")


if __name__ == "__main__":
    main()
