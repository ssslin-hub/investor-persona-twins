"""Build OpenAI Batch API JSONL input for all eval requests.

For each (setting, sim_label, eval_model, eval_run): build 12 B2 cell requests
+ 1 B4 set request, all with unique custom_id so we can route responses back
to the right per-cell file when downloading.

custom_id schema:
  <K>q_<source>_<label>__run<run>__<model>__b2__<analyst_safe>__<actual_idx>
  <K>q_<source>_<label>__run<run>__<model>__b4
"""
import argparse, json, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from run_pipeline import load_text

PROMPTS = os.path.join(ROOT, 'prompts')
DATA_AUTO = os.path.join(ROOT, 'data_auto')
B2_TPL = load_text(os.path.join(PROMPTS, 'b2_eval.md'))
B4_TPL = load_text(os.path.join(PROMPTS, 'b4_eval.md'))

ANALYSTS = ['matthew boss','steven wieczynski','brandt montour','james hardiman','lizzie dove','robin farley','vince ciepiel','sharon zackfia','andrew didora','xian siew','kevin kopelman']

# Settings: (K, source, [labels])
# K=14: v1 has rerun2-5 (4 existing sims with summary.json) + label s2-s5 new
# v5: K=14 has v5_curve+s2-s5; other K have s2-s5 new
# auto: all K need s2-s5 new

def find_existing_sims():
    """Return list of (K, source, sim_id, summary_path) tuples for all sims to evaluate."""
    sims = []
    # K=14 V1: 4 reruns
    for r in [2,3,4,5]:
        p = f'{DATA_AUTO}/final_eval_14q_v1_rerun{r}/summary.json'
        if os.path.exists(p): sims.append((14, 'v1', f'rerun{r}', p))
    # K=14 v5: 1 v5_curve (treated as s1) + 4 new s2-s5
    p = f'{DATA_AUTO}/final_eval_14q_v5/summary.json'
    if os.path.exists(p): sims.append((14, 'v5', 's1', p))
    for L in ['s2','s3','s4','s5']:
        p = f'{DATA_AUTO}/final_eval_14q_v5_{L}/summary.json'
        if os.path.exists(p): sims.append((14, 'v5', L, p))
    # K=14 auto: existing single + 4 new
    p = f'{DATA_AUTO}/final_eval_14q_auto/summary.json'
    if os.path.exists(p): sims.append((14, 'auto', 's1', p))
    for L in ['s2','s3','s4','s5']:
        p = f'{DATA_AUTO}/final_eval_14q_auto_{L}/summary.json'
        if os.path.exists(p): sims.append((14, 'auto', L, p))
    # Other K: existing (s1) + 4 new for each source
    for K in [5, 10, 16, 18, 20]:
        for src in ['v1', 'v5', 'auto']:
            p = f'{DATA_AUTO}/final_eval_{K}q_{src}/summary.json'
            if os.path.exists(p): sims.append((K, src, 's1', p))
            for L in ['s2','s3','s4','s5']:
                p = f'{DATA_AUTO}/final_eval_{K}q_{src}_{L}/summary.json'
                if os.path.exists(p): sims.append((K, src, L, p))
    return sims


def safe(s): return re.sub(r'[^a-z0-9]+', '_', s.lower())


def build_b2_requests(K, src, label, summary, actuals_by, model):
    """One B2 request per (analyst, actual) cell. For robin split into 2 cells."""
    reqs = []
    for name in ANALYSTS:
        cell = summary['per_analyst'].get(name)
        if not cell: continue
        preds = (cell.get('predictions') or {}).get('predicted_questions', [])
        actuals = actuals_by.get(name, [])
        if not preds or not actuals: continue
        # For robin: 2 actuals → 2 cells; else: 1 cell with all actuals
        if name == 'robin farley':
            for ai, a in enumerate(actuals):
                sim_block = {'analyst_name': name, 'predicted_questions': preds}
                actuals_b2 = [{'tuple_id': f'{name}-actual-{ai}', 'analyst_name': name, 'call': a.get('call'), 'question': a.get('question')}]
                prompt = B2_TPL.replace('{{SIMULATION_JSON}}', json.dumps(sim_block, indent=2)).replace('{{ACTUAL_QUESTIONS_JSON}}', json.dumps(actuals_b2, indent=2))
                cid = f'{K}q_{src}_{label}__{model}__b2__{safe(name)}__{ai}'
                reqs.append({'custom_id': cid, 'method': 'POST', 'url': '/v1/chat/completions',
                             'body': {'model': model, 'messages': [{'role':'user','content':prompt}], 'response_format':{'type':'json_object'}}})
        else:
            sim_block = {'analyst_name': name, 'predicted_questions': preds}
            actuals_b2 = [{'tuple_id': f'{name}-actual-{i}', 'analyst_name': name, 'call': a.get('call'), 'question': a.get('question')} for i, a in enumerate(actuals)]
            prompt = B2_TPL.replace('{{SIMULATION_JSON}}', json.dumps(sim_block, indent=2)).replace('{{ACTUAL_QUESTIONS_JSON}}', json.dumps(actuals_b2, indent=2))
            cid = f'{K}q_{src}_{label}__{model}__b2__{safe(name)}__0'
            reqs.append({'custom_id': cid, 'method': 'POST', 'url': '/v1/chat/completions',
                         'body': {'model': model, 'messages': [{'role':'user','content':prompt}], 'response_format':{'type':'json_object'}}})
    return reqs


def build_b4_request(K, src, label, summary, actuals_by, model):
    """One B4 request per setting × sim × eval-run."""
    pool = []
    for name in ANALYSTS:
        cell = summary['per_analyst'].get(name)
        if not cell: continue
        preds = (cell.get('predictions') or {}).get('predicted_questions', [])
        for i, p in enumerate(preds):
            pool.append({'candidate_id': f'{safe(name)}-pred-{i}', 'question': p.get('question_text','')})
    actuals_flat = []
    for name in ANALYSTS:
        cell = summary['per_analyst'].get(name)
        if not cell: continue
        actuals = actuals_by.get(name, [])
        for ai, a in enumerate(actuals):
            actuals_flat.append({'actual_id': f'{safe(name)}-actual-{ai}', 'question': a.get('question','')})
    prompt = B4_TPL.replace('{{PREDICTED_QUESTIONS_JSON}}', json.dumps(pool, indent=2)).replace('{{ACTUAL_QUESTIONS_JSON}}', json.dumps(actuals_flat, indent=2))
    cid = f'{K}q_{src}_{label}__{model}__b4'
    return {'custom_id': cid, 'method': 'POST', 'url': '/v1/chat/completions',
            'body': {'model': model, 'messages': [{'role':'user','content':prompt}], 'response_format':{'type':'json_object'}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True, choices=['gpt-5', 'gpt-5-mini'])
    ap.add_argument('--n-runs', type=int, required=True)
    ap.add_argument('--start-run', type=int, default=1, help='First run index to generate (default 1)')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    test = json.load(open(f'{DATA_AUTO}/test.json'))
    actuals_by = test['per_analyst_actual_questions']
    sims = find_existing_sims()
    print(f"Found {len(sims)} sims to evaluate")

    all_requests = []
    for K, src, label, sp in sims:
        summary = json.load(open(sp))
        for run_i in range(args.start_run, args.start_run + args.n_runs):
            # Tag run_i into custom_id by appending __runN
            for r in build_b2_requests(K, src, label, summary, actuals_by, args.model):
                r['custom_id'] = r['custom_id'].replace(f'__{args.model}__', f'__run{run_i}__{args.model}__')
                all_requests.append(r)
            b4r = build_b4_request(K, src, label, summary, actuals_by, args.model)
            b4r['custom_id'] = b4r['custom_id'].replace(f'__{args.model}__', f'__run{run_i}__{args.model}__')
            all_requests.append(b4r)

    with open(args.out, 'w') as f:
        for r in all_requests:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {len(all_requests)} requests to {args.out}")
    print(f"Approx tokens-out: {len(all_requests) * 600} = ${len(all_requests)*600*(0.6 if args.model=='gpt-5-mini' else 10)/1e6:.2f} batch-discount excl input")


if __name__ == '__main__':
    main()
