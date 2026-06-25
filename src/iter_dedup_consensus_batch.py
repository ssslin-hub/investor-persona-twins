"""Iterative recursive-halving dedup with mini × 3 majority-vote per round,
using BATCH API for each round. Sequential: round k waits for previous batch
to complete before submitting round k+1.

Usage:
  python3 src/iter_dedup_consensus_batch.py --source-K 18 --threshold 0.10
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from collections import Counter
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from run_pipeline import load_text

DATA_AUTO = os.path.join(ROOT, "data_auto")
B4_TPL = load_text(os.path.join(ROOT, "prompts", "b4_eval.md"))

def safe(s): return re.sub(r"[^a-z0-9]+", "_", s.lower())


def build_prompt(anchors, cands):
    return (B4_TPL
            .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(cands, indent=2))
            .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(anchors, indent=2)))


def submit_batch(client, requests, description, jsonl_path):
    with open(jsonl_path, 'w') as f:
        for r in requests: f.write(json.dumps(r) + '\n')
    with open(jsonl_path, 'rb') as f:
        fobj = client.files.create(file=f, purpose='batch')
    batch = client.batches.create(
        input_file_id=fobj.id,
        endpoint='/v1/chat/completions',
        completion_window='24h',
        metadata={'description': description},
    )
    print(f"  → submitted batch={batch.id}")
    return batch.id


def wait_for_batch(client, batch_id, poll_interval=60):
    print(f"  Polling batch every {poll_interval}s ...")
    while True:
        b = client.batches.retrieve(batch_id)
        pend = b.request_counts.total - b.request_counts.completed - b.request_counts.failed
        print(f"    [{time.strftime('%H:%M:%S')}] status={b.status} {b.request_counts.completed}/{b.request_counts.total} done {b.request_counts.failed} failed {pend} pending", flush=True)
        if b.status in ('completed', 'failed', 'cancelled', 'expired'):
            return b
        time.sleep(poll_interval)


def download_output(client, batch):
    if not batch.output_file_id: return []
    text = client.files.content(batch.output_file_id).text
    return [json.loads(l) for l in text.splitlines() if l.strip()]


def majority_vote(per_run_useful_sets, min_votes=2):
    cnt = Counter()
    for s in per_run_useful_sets: cnt.update(s)
    return {cid for cid, n in cnt.items() if n >= min_votes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-K', type=int, default=18)
    ap.add_argument('--threshold', type=float, default=0.10)
    ap.add_argument('--n-runs-per-round', type=int, default=3)
    ap.add_argument('--majority-min', type=int, default=2)
    ap.add_argument('--model', default='gpt-5-mini')
    ap.add_argument('--poll-interval', type=int, default=60)
    args = ap.parse_args()

    src_dir = os.path.join(DATA_AUTO, f'final_eval_{args.source_K}q_v5')
    summary = json.load(open(os.path.join(src_dir, 'summary.json')))
    out_dir = os.path.join(src_dir, 'iterative_dedup_consensus')
    os.makedirs(out_dir, exist_ok=True)

    per_analyst_ranks = {n: list(enumerate((c.get('predictions') or {}).get('predicted_questions', [])))
                         for n, c in summary['per_analyst'].items()}
    def cid(name, rank): return f"{safe(name)}-r{rank}"

    client = OpenAI()
    dropped_globally = set()
    trace_rounds = []
    m = args.source_K
    round_num = 0

    while True:
        round_num += 1
        L_anchors = m // 2
        L_candidates = m - L_anchors
        if L_anchors < 1 or L_candidates < 1:
            print(f"Stop: L too small at m={m}"); break

        # Build anchors + candidates
        anchors, candidates = [], []
        for name, ranks in per_analyst_ranks.items():
            for rank, q in ranks:
                if rank >= m: continue
                c = cid(name, rank)
                if c in dropped_globally: continue
                qtext = q.get('question_text', '')
                if rank < L_anchors:
                    anchors.append({"actual_id": c, "question": qtext})
                else:
                    candidates.append({"candidate_id": c, "question": qtext})

        if not anchors or not candidates: print(f"  Round {round_num}: empty; stop"); break

        round_dir = os.path.join(out_dir, f'round_{round_num}')
        os.makedirs(round_dir, exist_ok=True)
        prompt = build_prompt(anchors, candidates)
        with open(f'{round_dir}/prompt.txt', 'w') as f: f.write(prompt)
        print(f"\n=== Round {round_num}: m={m}, |anchors|={len(anchors)}, |cands|={len(candidates)} ===")

        # Build 3 identical mini requests (sampling will vary the output)
        reqs = []
        for run_i in range(1, args.n_runs_per_round+1):
            reqs.append({
                'custom_id': f'iter_consensus_K{args.source_K}__round{round_num}__run{run_i}__{args.model}__b4',
                'method': 'POST', 'url': '/v1/chat/completions',
                'body': {'model': args.model, 'messages': [{'role':'user','content':prompt}], 'response_format':{'type':'json_object'}}
            })
        jsonl_path = f'{round_dir}/batch_input.jsonl'
        batch_id = submit_batch(client, reqs, f'iter_consensus K={args.source_K} round={round_num}', jsonl_path)
        with open(f'{round_dir}/batch_id.txt', 'w') as f: f.write(batch_id)

        # Wait
        b = wait_for_batch(client, batch_id, poll_interval=args.poll_interval)
        if b.status != 'completed':
            print(f"  ! Batch {batch_id} status={b.status}; aborting"); sys.exit(1)
        outputs = download_output(client, b)
        with open(f'{round_dir}/batch_output.jsonl', 'w') as f:
            for o in outputs: f.write(json.dumps(o) + '\n')

        # Per-run useful sets
        per_run_useful = []
        per_run_drop_counts = []
        for rec in outputs:
            try:
                content = rec['response']['body']['choices'][0]['message']['content']
                b4 = json.loads(content)
                useful = {pp['candidate_id'] for pp in b4.get('predicted_precision',[]) if pp.get('useful')}
            except Exception as e:
                print(f"  ! parse fail for {rec['custom_id']}: {e}"); useful = set()
            per_run_useful.append(useful)
            per_run_drop_counts.append(len(useful))
        print(f"  Per-run drop counts: {per_run_drop_counts}")

        drops_this_round = majority_vote(per_run_useful, min_votes=args.majority_min)
        drop_rate = len(drops_this_round) / len(candidates)
        dropped_globally |= drops_this_round
        print(f"  Majority (≥{args.majority_min}/{args.n_runs_per_round}) drops: {len(drops_this_round)}/{len(candidates)} = {drop_rate:.3f}")

        with open(f'{round_dir}/drops.json', 'w') as f:
            json.dump({'round': round_num, 'm': m, 'L_anchors': L_anchors,
                       'anchors_count': len(anchors), 'candidates_count': len(candidates),
                       'per_run_drop_counts': per_run_drop_counts,
                       'majority_drops': sorted(drops_this_round),
                       'drop_rate': drop_rate}, f, indent=2)
        trace_rounds.append({'round': round_num, 'm': m, 'L_anchors': L_anchors,
                              'anchors_count': len(anchors), 'candidates_count': len(candidates),
                              'per_run_drop_counts': per_run_drop_counts,
                              'majority_drop_count': len(drops_this_round),
                              'drop_rate': drop_rate})

        if drop_rate < args.threshold:
            print(f"  Drop rate {drop_rate:.3f} < threshold {args.threshold}; stop")
            trace_rounds[-1]['stopped_at_threshold'] = True
            break
        m = L_anchors

    # Build final filtered pool
    filtered = {}
    total_kept = 0; counts = []
    for name, ranks in per_analyst_ranks.items():
        kept = [q for rank, q in ranks if cid(name, rank) not in dropped_globally]
        filtered[name] = {'n_actual': summary['per_analyst'][name].get('n_actual'),
                          'predictions': {'analyst': name, 'predicted_questions': kept},
                          'persona_source': summary['per_analyst'][name].get('persona_source', 'v5')}
        total_kept += len(kept); counts.append(len(kept))

    with open(f'{out_dir}/filtered_pool.json', 'w') as f:
        json.dump({'source_K': args.source_K, 'method': f'iter_consensus_mini_x{args.n_runs_per_round}',
                   'source': 'v5', 'total_predicted_questions': total_kept,
                   'per_analyst': filtered}, f, indent=2)
    with open(f'{out_dir}/trace.json', 'w') as f:
        json.dump({'source_K': args.source_K, 'threshold': args.threshold,
                   'n_runs_per_round': args.n_runs_per_round,
                   'majority_min': args.majority_min, 'rounds': trace_rounds,
                   'total_dropped': len(dropped_globally), 'total_kept': total_kept,
                   'per_analyst_kept': {n: c for n, c in zip(per_analyst_ranks, counts)}}, f, indent=2)

    s = sorted(counts); n = len(s)
    print(f"\n=== DONE ===")
    print(f"Total dropped: {len(dropped_globally)} / {args.source_K * 11}")
    print(f"Total kept: {total_kept}, per-analyst min/med/max = {s[0]}/{s[n//2]}/{s[-1]}")


if __name__ == '__main__':
    main()
