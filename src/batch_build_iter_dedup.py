"""Build batch JSONL for evaluating the iterative_dedup filtered pool vs real 12 actuals."""
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


def build_b2_reqs(K, pool, actuals_by, model, run_i):
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
                act_b2 = [{"tuple_id": f"{name}-actual-{ai}", "analyst_name": name, "call": a.get("call"), "question": a.get("question")}]
                p = B2_TPL.replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2)).replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(act_b2, indent=2))
                cid = f"iter_dedup_K{K}__run{run_i}__{model}__b2__{safe(name)}__{ai}"
                reqs.append({"custom_id": cid, "method": "POST", "url": "/v1/chat/completions",
                             "body": {"model": model, "messages": [{"role":"user","content":p}], "response_format":{"type":"json_object"}}})
        else:
            sim_block = {"analyst_name": name, "predicted_questions": preds}
            act_b2 = [{"tuple_id": f"{name}-actual-{i}", "analyst_name": name, "call": a.get("call"), "question": a.get("question")} for i, a in enumerate(actuals)]
            p = B2_TPL.replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2)).replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(act_b2, indent=2))
            cid = f"iter_dedup_K{K}__run{run_i}__{model}__b2__{safe(name)}__0"
            reqs.append({"custom_id": cid, "method": "POST", "url": "/v1/chat/completions",
                         "body": {"model": model, "messages": [{"role":"user","content":p}], "response_format":{"type":"json_object"}}})
    return reqs


def build_b4_req(K, pool, actuals_by, model, run_i):
    cands = []
    for name in ANALYSTS:
        cell = pool["per_analyst"].get(name)
        if not cell: continue
        for i, p in enumerate((cell.get("predictions") or {}).get("predicted_questions", [])):
            cands.append({"candidate_id": f"{safe(name)}-pred-{i}", "question": p.get("question_text", "")})
    actuals = []
    for name in ANALYSTS:
        for ai, a in enumerate(actuals_by.get(name, [])):
            actuals.append({"actual_id": f"{safe(name)}-actual-{ai}", "question": a.get("question", "")})
    prompt = B4_TPL.replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(cands, indent=2)).replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2))
    cid = f"iter_dedup_K{K}__run{run_i}__{model}__b4"
    return {"custom_id": cid, "method": "POST", "url": "/v1/chat/completions",
            "body": {"model": model, "messages": [{"role":"user","content":prompt}], "response_format":{"type":"json_object"}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-K", type=int, required=True)
    ap.add_argument("--model", required=True, choices=["gpt-5", "gpt-5-mini"])
    ap.add_argument("--n-runs", type=int, default=5)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pool = json.load(open(f"{DATA_AUTO}/final_eval_{args.source_K}q_v5/iterative_dedup/filtered_pool.json"))
    test = json.load(open(f"{DATA_AUTO}/test.json"))
    actuals_by = test["per_analyst_actual_questions"]

    all_reqs = []
    for run_i in range(1, args.n_runs+1):
        all_reqs.extend(build_b2_reqs(args.source_K, pool, actuals_by, args.model, run_i))
        all_reqs.append(build_b4_req(args.source_K, pool, actuals_by, args.model, run_i))

    with open(args.out, "w") as f:
        for r in all_reqs: f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(all_reqs)} requests to {args.out}")


if __name__ == "__main__":
    main()
