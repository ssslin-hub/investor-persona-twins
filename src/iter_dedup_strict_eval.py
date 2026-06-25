"""Strict iterative recursive-halving dedup ("deadout") with per-round strict eval.

Source-agnostic generalization of iter_dedup_consensus_batch.py (the dedup loop) +
iter_round_eval.py (per-round pool eval), using the STRICT rubric for BOTH the drop
decision and the per-round evaluation, synchronous gpt-5-mini.

Per round (recursive halving):
  anchors = ranks [0, m//2) per analyst, candidates = ranks [m//2, m) (minus already dropped)
  drop decision: strict B4 anchor-match (anchors as actuals, candidates as predicted),
                 gpt-5-mini x N, majority vote (>= majority_min) on predicted_precision[].useful
  then evaluate the cumulative filtered pool vs the true holdout: strict B4 mini x N, average
       coverage + precision. Stop if drop_rate < threshold or m//2 < 1; else m = m//2.
Round 0 = original pool eval (baseline, no drops).

Usage:
  python3 src/iter_dedup_strict_eval.py --source-dir final_eval_14q_v1 --source-K 14
"""
from __future__ import annotations
import argparse, json, os, re, sys, statistics
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import load_text  # noqa: E402

DATA_AUTO = os.path.join(ROOT, "data_auto")
STRICT_TPL = load_text(os.path.join(ROOT, "prompts", "b4_eval_strict.md"))
ANALYSTS = ['matthew boss', 'steven wieczynski', 'brandt montour', 'james hardiman',
            'lizzie dove', 'robin farley', 'vince ciepiel', 'sharon zackfia',
            'andrew didora', 'xian siew', 'kevin kopelman']


def safe(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower())


def drop_prompt(anchors, cands):
    return (STRICT_TPL.replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(cands, indent=2))
                      .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(anchors, indent=2)))


def eval_prompt(pool_per_analyst, actuals_by):
    candidates = []
    for name in ANALYSTS:
        for i, p in enumerate(pool_per_analyst.get(name, [])):
            candidates.append({"candidate_id": f"{safe(name)}-pred-{i}", "question": p.get("question_text", "")})
    actuals = []
    for name in ANALYSTS:
        for ai, a in enumerate(actuals_by.get(name, [])):
            actuals.append({"actual_id": f"{safe(name)}-actual-{ai}", "question": a.get("question", "")})
    return (STRICT_TPL.replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(candidates, indent=2))
                      .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)), len(candidates))


def majority_vote(per_run_useful_sets, min_votes=2):
    cnt = Counter()
    for s in per_run_useful_sets:
        cnt.update(s)
    return {cid for cid, n in cnt.items() if n >= min_votes}


def eval_pool(pool, actuals_by, model, n_runs, round_dir):
    """Run strict B4 eval n_runs times; return mean cov/prec + raw payloads. Persists per-run files."""
    prompt, n_cand = eval_prompt(pool, actuals_by)
    covs, precs = [], []
    for run_i in range(1, n_runs + 1):
        out = call_llm(prompt, expect_json=True, model=model,
                       log_to=os.path.join(round_dir, f"eval_prompt_{run_i}.txt"))
        b4 = parse_json_strict(out)
        ac = b4.get('actual_coverage', [])
        cov = sum(1 for x in ac if x.get('covered')) / len(ac) if ac else 0.0
        pp = b4.get('predicted_precision', [])
        prec = sum(1 for x in pp if x.get('useful')) / len(pp) if pp else 0.0
        covs.append(cov); precs.append(prec)
        with open(os.path.join(round_dir, f"eval_run_{run_i}.json"), 'w') as f:
            json.dump(b4, f, indent=2)
    mean = {
        'pool_size': n_cand,
        'cov_mean': statistics.mean(covs), 'cov_range': [min(covs), max(covs)], 'cov_runs': covs,
        'prec_mean': statistics.mean(precs), 'prec_range': [min(precs), max(precs)], 'prec_runs': precs,
        'n_runs': len(covs),
    }
    with open(os.path.join(round_dir, "eval_mean.json"), 'w') as f:
        json.dump(mean, f, indent=2)
    return mean


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-dir', required=True, help='e.g. final_eval_14q_v1')
    ap.add_argument('--source-K', type=int, required=True)
    ap.add_argument('--threshold', type=float, default=0.10)
    ap.add_argument('--drop-runs', type=int, default=3)
    ap.add_argument('--eval-runs', type=int, default=3)
    ap.add_argument('--majority-min', type=int, default=2)
    ap.add_argument('--model', default='gpt-5-mini')
    args = ap.parse_args()

    src_dir = os.path.join(DATA_AUTO, args.source_dir)
    summary = json.load(open(os.path.join(src_dir, 'summary.json')))
    actuals_by = json.load(open(f"{DATA_AUTO}/test.json"))["per_analyst_actual_questions"]
    out_dir = os.path.join(src_dir, 'dedup_strict')
    os.makedirs(out_dir, exist_ok=True)

    per_analyst_ranks = {n: list(enumerate((c.get('predictions') or {}).get('predicted_questions', [])))
                         for n, c in summary['per_analyst'].items()}
    def cid(name, rank): return f"{safe(name)}-r{rank}"

    def build_pool(dropped):
        return {name: [q for rank, q in ranks if cid(name, rank) not in dropped]
                for name, ranks in per_analyst_ranks.items()}

    print(f"=== {args.source_dir} (K={args.source_K}) strict dedup; model={args.model} ===")
    dropped_globally = set()
    trace = []

    # Round 0: baseline eval of full pool
    r0 = os.path.join(out_dir, 'round_0'); os.makedirs(r0, exist_ok=True)
    pool0 = build_pool(dropped_globally)
    with open(os.path.join(r0, 'pool.json'), 'w') as f:
        json.dump({'round': 0, 'pool': {n: [p.get('question_text', '') for p in qs] for n, qs in pool0.items()}}, f, indent=2)
    print(f"Round 0: pool {sum(len(v) for v in pool0.values())}, eval mini x{args.eval_runs} ...")
    m0 = eval_pool(pool0, actuals_by, args.model, args.eval_runs, r0)
    print(f"  round0 cov={m0['cov_mean']:.3f} prec={m0['prec_mean']:.3f}")
    trace.append({'round': 0, 'm': args.source_K, 'pool_size': m0['pool_size'],
                  'drops_this_round': 0, 'cov_mean': m0['cov_mean'], 'cov_range': m0['cov_range'],
                  'prec_mean': m0['prec_mean'], 'prec_range': m0['prec_range']})

    m = args.source_K
    round_num = 0
    while True:
        round_num += 1
        L_anchors = m // 2
        if L_anchors < 1 or (m - L_anchors) < 1:
            print(f"Stop: half-size too small at m={m}"); break
        anchors, candidates = [], []
        for name, ranks in per_analyst_ranks.items():
            for rank, q in ranks:
                if rank >= m:
                    continue
                c = cid(name, rank)
                if c in dropped_globally:
                    continue
                qt = q.get('question_text', '')
                (anchors if rank < L_anchors else candidates).append(
                    {"actual_id": c, "question": qt} if rank < L_anchors
                    else {"candidate_id": c, "question": qt})
        if not anchors or not candidates:
            print(f"Round {round_num}: empty anchors/cands; stop"); break

        rd = os.path.join(out_dir, f'round_{round_num}'); os.makedirs(rd, exist_ok=True)
        dp = drop_prompt(anchors, candidates)
        print(f"\n=== Round {round_num}: m={m} |anchors|={len(anchors)} |cands|={len(candidates)} ===")
        per_run_useful, per_run_counts = [], []
        for run_i in range(1, args.drop_runs + 1):
            out = call_llm(dp, expect_json=True, model=args.model,
                           log_to=os.path.join(rd, f"drop_prompt_{run_i}.txt"))
            try:
                b4 = parse_json_strict(out)
                useful = {pp['candidate_id'] for pp in b4.get('predicted_precision', []) if pp.get('useful')}
            except Exception as e:  # noqa: BLE001
                print(f"  ! drop parse fail run{run_i}: {e}"); useful = set()
            with open(os.path.join(rd, f"drop_run_{run_i}.json"), 'w') as f:
                f.write(out if isinstance(out, str) else json.dumps(out))
            per_run_useful.append(useful); per_run_counts.append(len(useful))
        drops = majority_vote(per_run_useful, min_votes=args.majority_min)
        drop_rate = len(drops) / len(candidates)
        dropped_globally |= drops
        print(f"  per-run drop counts {per_run_counts}; majority drops {len(drops)}/{len(candidates)} = {drop_rate:.3f}")
        with open(os.path.join(rd, 'drops.json'), 'w') as f:
            json.dump({'round': round_num, 'm': m, 'L_anchors': L_anchors,
                       'anchors_count': len(anchors), 'candidates_count': len(candidates),
                       'per_run_drop_counts': per_run_counts,
                       'majority_drops': sorted(drops), 'drop_rate': drop_rate}, f, indent=2)

        # Evaluate cumulative filtered pool
        pool = build_pool(dropped_globally)
        with open(os.path.join(rd, 'pool.json'), 'w') as f:
            json.dump({'round': round_num, 'cumulative_drops': len(dropped_globally),
                       'pool': {n: [p.get('question_text', '') for p in qs] for n, qs in pool.items()}}, f, indent=2)
        print(f"  eval cumulative pool {sum(len(v) for v in pool.values())} mini x{args.eval_runs} ...")
        me = eval_pool(pool, actuals_by, args.model, args.eval_runs, rd)
        print(f"  round{round_num} cov={me['cov_mean']:.3f} prec={me['prec_mean']:.3f}")
        trace.append({'round': round_num, 'm': m, 'L_anchors': L_anchors,
                      'pool_size': me['pool_size'], 'drops_this_round': len(drops),
                      'cumulative_drops': len(dropped_globally), 'drop_rate': drop_rate,
                      'cov_mean': me['cov_mean'], 'cov_range': me['cov_range'],
                      'prec_mean': me['prec_mean'], 'prec_range': me['prec_range']})

        if drop_rate < args.threshold:
            print(f"  drop_rate {drop_rate:.3f} < threshold {args.threshold}; stop")
            trace[-1]['stopped_at_threshold'] = True
            break
        m = L_anchors

    # Final filtered pool
    final_pool = build_pool(dropped_globally)
    total_kept = sum(len(v) for v in final_pool.values())
    with open(os.path.join(out_dir, 'filtered_pool.json'), 'w') as f:
        json.dump({'source_dir': args.source_dir, 'source_K': args.source_K,
                   'method': f'iter_dedup_strict_mini_x{args.drop_runs}',
                   'total_predicted_questions': total_kept,
                   'per_analyst': {n: {'predictions': {'analyst': n, 'predicted_questions': qs}}
                                   for n, qs in final_pool.items()}}, f, indent=2)
    with open(os.path.join(out_dir, 'trace.json'), 'w') as f:
        json.dump({'source_dir': args.source_dir, 'source_K': args.source_K,
                   'threshold': args.threshold, 'drop_runs': args.drop_runs,
                   'eval_runs': args.eval_runs, 'majority_min': args.majority_min,
                   'total_dropped': len(dropped_globally), 'total_kept': total_kept,
                   'rounds': trace}, f, indent=2)
    print(f"\n=== DONE {args.source_dir}: dropped {len(dropped_globally)}/{args.source_K*11}, kept {total_kept} ===")


if __name__ == '__main__':
    main()
