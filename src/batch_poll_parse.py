"""Poll a batch tracker; if completed, download output and parse back into
per-(setting,sim,run) b2_per_actual.json + b4.json files.

Idempotent: safe to run repeatedly via cron.
"""
import argparse, json, os, re, sys, datetime
from collections import defaultdict
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_AUTO = os.path.join(ROOT, 'data_auto')

ANALYST_FROM_SAFE = {
    'matthew_boss':'matthew boss','steven_wieczynski':'steven wieczynski',
    'brandt_montour':'brandt montour','james_hardiman':'james hardiman',
    'lizzie_dove':'lizzie dove','robin_farley':'robin farley',
    'vince_ciepiel':'vince ciepiel','sharon_zackfia':'sharon zackfia',
    'andrew_didora':'andrew didora','xian_siew':'xian siew','kevin_kopelman':'kevin kopelman',
}


def out_dir_for(K, src, label, run, model):
    """Where to write the parsed per-cell file."""
    # Dedup outputs go under final_eval_<K>q_v5/anchor_dedup/L<L>/variance_batch/{model}/run_{N}/
    if src == 'dedup':
        # label here is 'L<N>' and K is the source K
        base = f'{DATA_AUTO}/final_eval_{K}q_v5/anchor_dedup/{label}'
        model_safe = model.replace('-', '_')
        return f'{base}/variance_batch/{model_safe}/run_{run}'
    # Iter dedup outputs go under final_eval_<K>q_v5/iterative_dedup/variance_batch/{model}/run_{N}/
    if src == 'iter_dedup':
        base = f'{DATA_AUTO}/final_eval_{K}q_v5/iterative_dedup'
        model_safe = model.replace('-', '_')
        return f'{base}/variance_batch/{model_safe}/run_{run}'
    # Iter consensus outputs go under iterative_dedup_consensus/variance_batch/{model}/run_{N}/
    if src == 'iter_consensus':
        base = f'{DATA_AUTO}/final_eval_{K}q_v5/iterative_dedup_consensus'
        model_safe = model.replace('-', '_')
        return f'{base}/variance_batch/{model_safe}/run_{run}'
    # Iter round eval (per-intermediate-pool): separate by model
    if src == 'iter_round_eval':
        base = f'{DATA_AUTO}/final_eval_{K}q_v5/iterative_dedup/round_eval_batch/{label}'
        model_safe = model.replace('-', '_')
        return f'{base}/{model_safe}/run_{run}'
    # K=10 dedup 5-sim eval: write under final_eval_10q_v5_<sim>/anchor_dedup/L<L>/variance_batch/{model}/run_{N}/
    if src == 'k10_dedup_5sims':
        # label = '{sim_label}_L{L}', e.g. 's2_L3'
        sim_label, L = label.split('_')
        base = f'{DATA_AUTO}/final_eval_10q_v5_{sim_label}/anchor_dedup/{L}'
        model_safe = model.replace('-', '_')
        return f'{base}/variance_batch/{model_safe}/run_{run}'
    # sim_1 dedup variants: write under final_eval_10q_v5/anchor_dedup_d{D}_L3/variance_batch/{model}/run_{N}/
    if src == 'k10_sim1_dedup_variants':
        # label = 'd2'..'d5'
        base = f'{DATA_AUTO}/final_eval_10q_v5/anchor_dedup_{label}_L3'
        model_safe = model.replace('-', '_')
        return f'{base}/variance_batch/{model_safe}/run_{run}'
    # K-curve eval outputs
    if src == 'v1' and label.startswith('rerun'):
        base = f'{DATA_AUTO}/final_eval_{K}q_v1_{label}'
    elif label == 's1':
        if src == 'v5' and K == 14:
            base = f'{DATA_AUTO}/final_eval_14q_v5'
        elif src == 'auto' and K == 14:
            base = f'{DATA_AUTO}/final_eval_14q_auto'
        else:
            base = f'{DATA_AUTO}/final_eval_{K}q_{src}'
    else:
        base = f'{DATA_AUTO}/final_eval_{K}q_{src}_{label}'
    model_safe = model.replace('-', '_')
    return f'{base}/variance_batch/{model_safe}/run_{run}'


def parse_cid(cid):
    """Parse custom_id back into (K, src, label, run, model, kind, analyst_safe, actual_idx)."""
    # Dedup eval schema: dedup_K{N}_L{L}__run{R}__{model}__b2|b4[__{analyst}__{ai}]
    m = re.match(r'dedup_K(\d+)_L(\d+)__run(\d+)__([a-z0-9-]+)__(b2|b4)(?:__([a-z_]+)__(\d+))?$', cid)
    if m:
        K, L, run, model, kind, analyst_safe, ai = m.groups()
        return int(K), 'dedup', f'L{L}', int(run), model, kind, analyst_safe, int(ai) if ai else None
    # Iter dedup eval schema: iter_dedup_K{N}__run{R}__{model}__b2|b4[__{analyst}__{ai}]
    m = re.match(r'iter_dedup_K(\d+)__run(\d+)__([a-z0-9-]+)__(b2|b4)(?:__([a-z_]+)__(\d+))?$', cid)
    if m:
        K, run, model, kind, analyst_safe, ai = m.groups()
        return int(K), 'iter_dedup', 'iter', int(run), model, kind, analyst_safe, int(ai) if ai else None
    # Iter consensus eval schema: iter_consensus_K{N}__run{R}__{model}__b2|b4[__{analyst}__{ai}]
    m = re.match(r'iter_consensus_K(\d+)__run(\d+)__([a-z0-9-]+)__(b2|b4)(?:__([a-z_]+)__(\d+))?$', cid)
    if m:
        K, run, model, kind, analyst_safe, ai = m.groups()
        return int(K), 'iter_consensus', 'iter', int(run), model, kind, analyst_safe, int(ai) if ai else None
    # Iter round eval (intermediate pool) schema: iter_round_eval__after_r{R}__run{N}__{model}__(b4 | b2__{analyst}__{ai})
    m = re.match(r'iter_round_eval__after_r(\d+)__run(\d+)__([a-z0-9-]+)__(b2|b4)(?:__([a-z_]+)__(\d+))?$', cid)
    if m:
        round_num, run, model, kind, analyst_safe, ai = m.groups()
        return 18, 'iter_round_eval', f'after_r{round_num}', int(run), model, kind, analyst_safe, int(ai) if ai else None
    # K=10 dedup 5-sim eval schema: k10_dedup_eval__{sim_label}_L3__run{N}__{model}__(b2|b4)[__{analyst}__{ai}]
    m = re.match(r'k10_dedup_eval__(s\d)_L(\d+)__run(\d+)__([a-z0-9-]+)__(b2|b4)(?:__([a-z_]+)__(\d+))?$', cid)
    if m:
        sim_label, L, run, model, kind, analyst_safe, ai = m.groups()
        return 10, 'k10_dedup_5sims', f'{sim_label}_L{L}', int(run), model, kind, analyst_safe, int(ai) if ai else None
    # sim_1 dedup variants schema: k10_sim1_dedup_d{D}__run{N}__{model}__(b2|b4)[__{analyst}__{ai}]
    m = re.match(r'k10_sim1_dedup_d(\d)__run(\d+)__([a-z0-9-]+)__(b2|b4)(?:__([a-z_]+)__(\d+))?$', cid)
    if m:
        d_run, run, model, kind, analyst_safe, ai = m.groups()
        return 10, 'k10_sim1_dedup_variants', f'd{d_run}', int(run), model, kind, analyst_safe, int(ai) if ai else None
    # K-curve eval schema
    m = re.match(r'(\d+)q_(v1|v5|auto)_([a-z0-9]+)__run(\d+)__([a-z0-9-]+)__(b2|b4)(?:__([a-z_]+)__(\d+))?$', cid)
    if m:
        K, src, label, run, model, kind, analyst_safe, ai = m.groups()
        return int(K), src, label, int(run), model, kind, analyst_safe, int(ai) if ai else None
    return None


def parse_batch_output(output_lines):
    """Group by (K,src,label,run,model) and write per-cell files."""
    by_group = defaultdict(lambda: {'b2_cells': [], 'b4': None})
    for line in output_lines:
        if not line.strip(): continue
        rec = json.loads(line)
        cid = rec['custom_id']
        parsed = parse_cid(cid)
        if not parsed:
            print(f"  WARN: unparseable cid {cid}"); continue
        K, src, label, run, model, kind, analyst_safe, ai = parsed
        resp = rec.get('response')
        if resp and resp.get('status_code') == 200:
            body = resp['body']
            content = body['choices'][0]['message']['content']
            try:
                payload = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON
                m = re.search(r'\{.*\}', content, re.DOTALL)
                payload = json.loads(m.group()) if m else None
            if payload is None:
                print(f"  WARN: JSON parse fail for {cid}"); continue
        else:
            err = rec.get('error') or (resp and resp.get('body'))
            print(f"  ERR {cid}: {str(err)[:200]}"); continue

        gkey = (K, src, label, run, model)
        if kind == 'b2':
            analyst = ANALYST_FROM_SAFE.get(analyst_safe, analyst_safe)
            cell = payload.copy()
            cell['analyst_name'] = analyst
            if analyst == 'robin farley':
                cell['robin_actual_index'] = ai
            by_group[gkey]['b2_cells'].append(cell)
        elif kind == 'b4':
            by_group[gkey]['b4'] = payload

    written = 0
    for gkey, data in by_group.items():
        K, src, label, run, model = gkey
        out = out_dir_for(K, src, label, run, model)
        os.makedirs(out, exist_ok=True)
        if data['b2_cells']:
            # Build b2_per_actual.json + b2_summary.json
            cells = data['b2_cells']
            n_eval = len(cells)
            n_bin = sum(1 for c in cells if c.get('binary_match'))
            n_strong = sum(1 for c in cells if c.get('match_score_0_to_4', 0) >= 4)
            scores = [c.get('match_score_0_to_4', 0) for c in cells]
            avg = sum(scores)/n_eval if n_eval else 0
            with open(f'{out}/b2_per_actual.json', 'w') as f:
                json.dump({'cells': cells}, f, indent=2)
            with open(f'{out}/b2_summary.json', 'w') as f:
                json.dump({'evaluated_count': n_eval, 'binary_match_count': n_bin,
                          'binary_match_rate': n_bin/n_eval if n_eval else 0,
                          'strong_match_count': n_strong,
                          'average_match_score_0_to_4': avg}, f, indent=2)
        if data['b4']:
            with open(f'{out}/b4.json', 'w') as f:
                json.dump(data['b4'], f, indent=2)
        written += 1
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tracker', required=True)
    args = ap.parse_args()
    tracker = json.load(open(args.tracker))
    client = OpenAI()
    batch = client.batches.retrieve(tracker['batch_id'])
    print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {tracker['description']}: {batch.status}  "
          f"completed={getattr(batch.request_counts,'completed',0)}/{getattr(batch.request_counts,'total',0)}  "
          f"failed={getattr(batch.request_counts,'failed',0)}")
    if batch.status in ('completed', 'expired', 'cancelled'):
        if batch.output_file_id:
            print(f"  Downloading output_file_id={batch.output_file_id}")
            content = client.files.content(batch.output_file_id).text
            outpath = args.tracker.replace('.json', '_output.jsonl')
            with open(outpath, 'w') as f: f.write(content)
            n_groups = parse_batch_output(content.splitlines())
            print(f"  Parsed → {n_groups} (setting, sim, run, model) groups written")
        if batch.error_file_id:
            print(f"  Downloading error_file_id={batch.error_file_id}")
            err_content = client.files.content(batch.error_file_id).text
            errpath = args.tracker.replace('.json', '_errors.jsonl')
            with open(errpath, 'w') as f: f.write(err_content)
            n_errs = sum(1 for line in err_content.splitlines() if line.strip())
            print(f"  Wrote {n_errs} errors to {errpath}")
        tracker['status'] = batch.status
        tracker['completed_at'] = batch.completed_at
        with open(args.tracker, 'w') as f:
            json.dump(tracker, f, indent=2)
    else:
        print(f"  Still in progress; will check again later")


if __name__ == '__main__':
    main()
