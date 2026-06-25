"""Evaluate intermediate iter-dedup pools after each round.

For each round R: pool = source minus union(drops from rounds 1..R).
Write intermediate pool file + run mini B4 eval N times.
"""
from __future__ import annotations
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict
from run_pipeline import load_text

DATA_AUTO = os.path.join(ROOT, "data_auto")
B4_TPL = load_text(os.path.join(ROOT, "prompts", "b4_eval.md"))
ANALYSTS = ['matthew boss','steven wieczynski','brandt montour','james hardiman','lizzie dove','robin farley','vince ciepiel','sharon zackfia','andrew didora','xian siew','kevin kopelman']


def safe(s): return re.sub(r"[^a-z0-9]+", "_", s.lower())


def build_b4_prompt(pool_per_analyst, actuals_by):
    candidates = []
    for name in ANALYSTS:
        preds = pool_per_analyst.get(name, [])
        for i, p in enumerate(preds):
            candidates.append({"candidate_id": f"{safe(name)}-pred-{i}", "question": p.get("question_text", "")})
    actuals = []
    for name in ANALYSTS:
        for ai, a in enumerate(actuals_by.get(name, [])):
            actuals.append({"actual_id": f"{safe(name)}-actual-{ai}", "question": a.get("question", "")})
    return (B4_TPL.replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(candidates, indent=2))
                  .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2))), len(candidates)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n-runs-per-round', type=int, default=5)
    ap.add_argument('--n-runs-round-3', type=int, default=10, help='Extra runs for round 3 (L=4 territory)')
    args = ap.parse_args()

    source = json.load(open(f"{DATA_AUTO}/final_eval_18q_v5/summary.json"))
    test = json.load(open(f"{DATA_AUTO}/test.json"))
    actuals_by = test["per_analyst_actual_questions"]

    # Build {analyst: [(rank, q)]}
    per_analyst_ranks = {n: list(enumerate((c.get('predictions') or {}).get('predicted_questions', [])))
                          for n, c in source['per_analyst'].items()}
    def cid(name, rank): return f"{safe(name)}-r{rank}"

    # Load drops per round
    rounds_data = []
    cumulative_dropped = set()
    for r in [1, 2, 3, 4]:
        round_drops_file = f"{DATA_AUTO}/final_eval_18q_v5/iterative_dedup/round_{r}/drops.json"
        if not os.path.exists(round_drops_file): continue
        d = json.load(open(round_drops_file))
        round_cids = {x['candidate_id'] for x in d['drops']}
        cumulative_dropped |= round_cids
        # Build intermediate pool
        pool = {}
        for name, ranks in per_analyst_ranks.items():
            kept = [q for rank, q in ranks if cid(name, rank) not in cumulative_dropped]
            pool[name] = kept
        n_kept = sum(len(qs) for qs in pool.values())
        rounds_data.append((r, n_kept, pool, len(round_cids), len(cumulative_dropped)))
        print(f"Round {r}: this round dropped {len(round_cids)}, cumulative dropped {len(cumulative_dropped)}, pool size = {n_kept}")

    # Eval each intermediate pool
    out_root = f"{DATA_AUTO}/final_eval_18q_v5/iterative_dedup/round_eval"
    os.makedirs(out_root, exist_ok=True)
    results = []
    for r, n_kept, pool, this_drops, cum_drops in rounds_data:
        n_runs = args.n_runs_round_3 if r == 3 else args.n_runs_per_round
        prompt, n_cand = build_b4_prompt(pool, actuals_by)
        round_dir = f"{out_root}/after_round_{r}"
        os.makedirs(round_dir, exist_ok=True)
        # Save pool snapshot
        with open(f"{round_dir}/filtered_pool.json", 'w') as f:
            json.dump({"after_round": r, "pool_size": n_kept,
                       "this_round_drops": this_drops, "cumulative_drops": cum_drops,
                       "per_analyst": pool}, f, indent=2)
        print(f"\n=== After round {r}: pool {n_kept}, running mini × {n_runs} ===")
        covs = []; precs = []
        for run_i in range(1, n_runs+1):
            log = f"{round_dir}/mini_run_{run_i}.txt"
            try:
                out = call_llm(prompt, expect_json=True, model='gpt-5-mini', log_to=log)
                b4 = parse_json_strict(out)
                ac = b4.get('actual_coverage', [])
                cov = sum(1 for x in ac if x.get('covered'))/len(ac) if ac else 0
                pp = b4.get('predicted_precision', [])
                prec = sum(1 for x in pp if x.get('useful'))/len(pp) if pp else 0
                covs.append(cov); precs.append(prec)
                with open(f"{round_dir}/mini_b4_{run_i}.json", 'w') as f: json.dump(b4, f, indent=2)
                print(f"  run {run_i}: cov={cov:.3f}, prec={prec:.3f}")
            except Exception as e:
                print(f"  run {run_i}: ERR {str(e)[:100]}")
        if covs:
            import statistics
            results.append({
                'round': r, 'pool_size': n_kept,
                'mini_cov_mean': statistics.mean(covs), 'mini_cov_range': [min(covs), max(covs)], 'mini_cov_n': len(covs),
                'mini_prec_mean': statistics.mean(precs), 'mini_prec_range': [min(precs), max(precs)],
            })
            print(f"  → cov mean={statistics.mean(covs):.3f}, prec mean={statistics.mean(precs):.3f}")

    with open(f"{out_root}/summary.json", 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_root}/summary.json")


if __name__ == "__main__":
    main()
