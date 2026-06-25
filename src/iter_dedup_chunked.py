"""Strict iterative recursive-halving dedup with PER-ANALYST drop decision and
CHUNKED per-round evaluation — fixes the large-pool B4 blindness that made the
single-call version's coverage baseline too low and non-monotone.

Drop decision (per analyst, within-twin):
  Round with window m → for each analyst: anchors = ranks [0, m//2), candidates =
  ranks [m//2, m) (minus already dropped). Small strict B4 anchor-match call
  (anchors as actuals, candidates as predicted), gpt-5-mini x N, majority vote
  (>= majority_min) on predicted_precision[].useful. Drops restricted to that
  analyst's own candidate ids (no cross-analyst / stray ids).

Per-round evaluation (chunked, set-level):
  pool candidates split into chunks of <= chunk_size; each chunk scored by strict
  B4 against ALL 12 actuals. Coverage = (per actual, MAX score across chunks >= 3)
  / 12. Precision = useful candidates / total. gpt-5-mini x N, averaged.

Round 0 = original pool eval baseline. Stop when drop_rate < threshold or m//2 < 1.
Independent LLM calls within a phase run on a thread pool for speed.

Usage:
  python3 src/iter_dedup_chunked.py --source-dir final_eval_14q_v1 --source-K 14
"""
from __future__ import annotations
import argparse, json, os, re, sys, statistics
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

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
MAX_WORKERS = 8


def safe(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower())


def b4_prompt(predicted, actuals):
    return (STRICT_TPL.replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(predicted, indent=2))
                      .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))


def call_b4(prompt, model, log_to=None):
    out = call_llm(prompt, expect_json=True, model=model, log_to=log_to)
    return parse_json_strict(out)


# ---------- per-analyst drop ----------

def per_analyst_drop(per_analyst_ranks, m, dropped, model, n_runs, majority_min, round_dir):
    L = m // 2
    info = {}          # name -> {'prompt', 'cand_ids', 'n_anchor'}
    for name, ranks in per_analyst_ranks.items():
        anchors, cands = [], []
        for rank, q in ranks:
            if rank >= m:
                continue
            c = f"{safe(name)}-r{rank}"
            if c in dropped:
                continue
            qt = q.get('question_text', '')
            (anchors if rank < L else cands).append(
                {"actual_id": c, "question": qt} if rank < L else {"candidate_id": c, "question": qt})
        if not anchors or not cands:
            continue
        info[name] = {'prompt': b4_prompt(cands, anchors),
                      'cand_ids': {c['candidate_id'] for c in cands},
                      'n_anchor': len(anchors), 'n_cand': len(cands)}

    tasks = [(name, run_i) for name in info for run_i in range(1, n_runs + 1)]

    def work(t):
        name, run_i = t
        b4 = call_b4(info[name]['prompt'], model)
        useful = {pp['candidate_id'] for pp in b4.get('predicted_precision', []) if pp.get('useful')}
        return (name, run_i, useful)

    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for name, run_i, useful in ex.map(work, tasks):
            results[(name, run_i)] = useful

    drops = set()
    per_analyst_counts = {}
    for name, meta in info.items():
        cnt = Counter()
        for run_i in range(1, n_runs + 1):
            cnt.update(results.get((name, run_i), set()))
        a_drops = {c for c, n in cnt.items() if n >= majority_min and c in meta['cand_ids']}
        drops |= a_drops
        per_analyst_counts[name] = {'n_cand': meta['n_cand'], 'n_anchor': meta['n_anchor'],
                                    'dropped': len(a_drops)}
    total_cands = sum(meta['n_cand'] for meta in info.values())
    with open(os.path.join(round_dir, 'drops.json'), 'w') as f:
        json.dump({'m': m, 'L_anchors': L, 'total_candidates': total_cands,
                   'total_dropped': len(drops), 'drop_rate': len(drops) / max(1, total_cands),
                   'per_analyst': per_analyst_counts, 'dropped_ids': sorted(drops)}, f, indent=2)
    return drops, total_cands


# ---------- chunked eval ----------

def chunked_eval(pool, actuals_by, model, n_runs, chunk_size, round_dir):
    cands = []
    for name in ANALYSTS:
        for i, p in enumerate(pool.get(name, [])):
            cands.append({"candidate_id": f"{safe(name)}-pred-{i}", "question": p.get("question_text", "")})
    actuals = []
    for name in ANALYSTS:
        for ai, a in enumerate(actuals_by.get(name, [])):
            actuals.append({"actual_id": f"{safe(name)}-actual-{ai}", "question": a.get("question", "")})
    n_actual = len(actuals)
    chunks = [cands[i:i + chunk_size] for i in range(0, len(cands), chunk_size)] or [[]]

    tasks = [(run_i, ci) for run_i in range(1, n_runs + 1) for ci in range(len(chunks))]

    def work(t):
        run_i, ci = t
        if not chunks[ci]:
            return (run_i, ci, {"actual_coverage": [], "predicted_precision": []})
        b4 = call_b4(b4_prompt(chunks[ci], actuals), model)
        return (run_i, ci, b4)

    by_run = {r: [] for r in range(1, n_runs + 1)}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for run_i, ci, b4 in ex.map(work, tasks):
            by_run[run_i].append(b4)

    covs, precs = [], []
    for run_i in range(1, n_runs + 1):
        best = {a['actual_id']: 0 for a in actuals}
        prec_rows = []
        for b4 in by_run[run_i]:
            for x in b4.get('actual_coverage', []):
                aid = x.get('actual_id'); s = x.get('match_score_0_to_4') or 0
                if aid in best and s > best[aid]:
                    best[aid] = s
            prec_rows += b4.get('predicted_precision', [])
        cov = sum(1 for v in best.values() if v >= 3) / n_actual if n_actual else 0.0
        prec = sum(1 for r in prec_rows if (r.get('match_score_0_to_4') or 0) >= 3) / len(prec_rows) if prec_rows else 0.0
        covs.append(cov); precs.append(prec)
        with open(os.path.join(round_dir, f'eval_run_{run_i}.json'), 'w') as f:
            json.dump({'coverage_best_per_actual': best, 'cov': cov, 'prec': prec}, f, indent=2)

    mean = {'pool_size': len(cands), 'n_chunks': len(chunks),
            'cov_mean': statistics.mean(covs), 'cov_range': [min(covs), max(covs)], 'cov_runs': covs,
            'prec_mean': statistics.mean(precs), 'prec_range': [min(precs), max(precs)], 'prec_runs': precs,
            'n_runs': n_runs}
    with open(os.path.join(round_dir, 'eval_mean.json'), 'w') as f:
        json.dump(mean, f, indent=2)
    return mean


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-dir', required=True)
    ap.add_argument('--source-K', type=int, required=True)
    ap.add_argument('--threshold', type=float, default=0.10)
    ap.add_argument('--drop-runs', type=int, default=3)
    ap.add_argument('--eval-runs', type=int, default=3)
    ap.add_argument('--chunk-size', type=int, default=50)
    ap.add_argument('--majority-min', type=int, default=2)
    ap.add_argument('--drop-model', default='gpt-5-mini')
    ap.add_argument('--eval-model', default='gpt-5-mini')
    ap.add_argument('--out-subdir', default='dedup_strict')
    args = ap.parse_args()

    src_dir = os.path.join(DATA_AUTO, args.source_dir)
    summary = json.load(open(os.path.join(src_dir, 'summary.json')))
    actuals_by = json.load(open(f"{DATA_AUTO}/test.json"))["per_analyst_actual_questions"]
    out_dir = os.path.join(src_dir, args.out_subdir)
    os.makedirs(out_dir, exist_ok=True)

    per_analyst_ranks = {n: list(enumerate((c.get('predictions') or {}).get('predicted_questions', [])))
                         for n, c in summary['per_analyst'].items()}

    def build_pool(dropped):
        return {name: [q for rank, q in ranks if f"{safe(name)}-r{rank}" not in dropped]
                for name, ranks in per_analyst_ranks.items()}

    print(f"=== {args.source_dir} (K={args.source_K}) chunked strict dedup; drop={args.drop_model} eval={args.eval_model} ===")
    dropped = set()
    trace = []

    r0 = os.path.join(out_dir, 'round_0'); os.makedirs(r0, exist_ok=True)
    pool0 = build_pool(dropped)
    m0 = chunked_eval(pool0, actuals_by, args.eval_model, args.eval_runs, args.chunk_size, r0)
    print(f"Round 0: pool {m0['pool_size']} ({m0['n_chunks']} chunks) cov={m0['cov_mean']:.3f} prec={m0['prec_mean']:.3f}")
    trace.append({'round': 0, 'm': args.source_K, 'pool_size': m0['pool_size'], 'drops_this_round': 0,
                  'cov_mean': m0['cov_mean'], 'cov_range': m0['cov_range'],
                  'prec_mean': m0['prec_mean'], 'prec_range': m0['prec_range']})

    m = args.source_K
    rn = 0
    while True:
        rn += 1
        if m // 2 < 1 or (m - m // 2) < 1:
            print(f"Stop: half-size too small at m={m}"); break
        rd = os.path.join(out_dir, f'round_{rn}'); os.makedirs(rd, exist_ok=True)
        print(f"\n=== Round {rn}: m={m} (per-analyst drop) ===")
        drops, total_cands = per_analyst_drop(per_analyst_ranks, m, dropped, args.drop_model,
                                              args.drop_runs, args.majority_min, rd)
        if total_cands == 0:
            print("  no candidates; stop"); break
        drop_rate = len(drops) / total_cands
        dropped |= drops
        print(f"  dropped {len(drops)}/{total_cands} = {drop_rate:.3f}")
        pool = build_pool(dropped)
        me = chunked_eval(pool, actuals_by, args.eval_model, args.eval_runs, args.chunk_size, rd)
        print(f"  pool {me['pool_size']} ({me['n_chunks']} chunks) cov={me['cov_mean']:.3f} prec={me['prec_mean']:.3f}")
        trace.append({'round': rn, 'm': m, 'pool_size': me['pool_size'],
                      'drops_this_round': len(drops), 'cumulative_drops': len(dropped),
                      'drop_rate': drop_rate, 'cov_mean': me['cov_mean'], 'cov_range': me['cov_range'],
                      'prec_mean': me['prec_mean'], 'prec_range': me['prec_range']})
        if drop_rate < args.threshold:
            print(f"  drop_rate {drop_rate:.3f} < threshold {args.threshold}; stop")
            trace[-1]['stopped_at_threshold'] = True
            break
        m = m // 2

    final_pool = build_pool(dropped)
    total_kept = sum(len(v) for v in final_pool.values())
    with open(os.path.join(out_dir, 'trace.json'), 'w') as f:
        json.dump({'source_dir': args.source_dir, 'source_K': args.source_K, 'method': 'chunked_per_analyst_strict',
                   'threshold': args.threshold, 'drop_runs': args.drop_runs, 'eval_runs': args.eval_runs,
                   'chunk_size': args.chunk_size, 'majority_min': args.majority_min,
                   'total_dropped': len(dropped), 'total_kept': total_kept, 'rounds': trace}, f, indent=2)
    with open(os.path.join(out_dir, 'filtered_pool.json'), 'w') as f:
        json.dump({'source_dir': args.source_dir, 'total_predicted_questions': total_kept,
                   'per_analyst': {n: {'predictions': {'analyst': n, 'predicted_questions': qs}}
                                   for n, qs in final_pool.items()}}, f, indent=2)
    print(f"\n=== DONE {args.source_dir}: dropped {len(dropped)}/{args.source_K*11}, kept {total_kept} ===")


if __name__ == '__main__':
    main()
