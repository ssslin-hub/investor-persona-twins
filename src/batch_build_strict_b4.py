"""Build OpenAI Batch API JSONL for STRICT B4-only evaluation of all auto/v1/v5 settings.

Uses prompts/b4_eval_strict.md (the conservative substitution-test rubric), emits ONE
B4 request per setting (no B2), single eval run, model gpt-5-mini by default.

custom_id schema (distinct `b4strict` kind so parse_strict_b4.py routes to <setting>/strict_b4/):
  <K>q_<source>_<label>__run1__<model>__b4strict

Settings enumerated by find_settings(): auto/v1/v5 × K{5,10,12,14,16,18,20} × seeds{s1..s5}
plus v1-K14 reruns. seq/v6/conv/base excluded by design.
"""
import argparse, json, os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from run_pipeline import load_text  # noqa: E402

PROMPTS = os.path.join(ROOT, 'prompts')
DATA_AUTO = os.path.join(ROOT, 'data_auto')
B4_STRICT_TPL = load_text(os.path.join(PROMPTS, 'b4_eval_strict.md'))

ANALYSTS = ['matthew boss', 'steven wieczynski', 'brandt montour', 'james hardiman',
            'lizzie dove', 'robin farley', 'vince ciepiel', 'sharon zackfia',
            'andrew didora', 'xian siew', 'kevin kopelman']

KS = [5, 10, 12, 14, 16, 18, 20]
SOURCES = ['v1', 'v5', 'auto']


def find_settings():
    """Return [(K, src, label, summary_path)] for all auto/v1/v5 parallel settings."""
    sims = []
    for K in KS:
        for src in SOURCES:
            # seed-1 (no suffix)
            p = f'{DATA_AUTO}/final_eval_{K}q_{src}/summary.json'
            if os.path.exists(p):
                sims.append((K, src, 's1', p))
            # seeds 2-5
            for L in ['s2', 's3', 's4', 's5']:
                p = f'{DATA_AUTO}/final_eval_{K}q_{src}_{L}/summary.json'
                if os.path.exists(p):
                    sims.append((K, src, L, p))
    # v1 K=14 reruns (extra sims beyond seed-1)
    for r in [2, 3, 4, 5]:
        p = f'{DATA_AUTO}/final_eval_14q_v1_rerun{r}/summary.json'
        if os.path.exists(p):
            sims.append((14, 'v1', f'rerun{r}', p))
    return sims


def safe(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower())


def build_b4_request(K, src, label, summary, actuals_by, model, run_i):
    pool = []
    for name in ANALYSTS:
        cell = summary['per_analyst'].get(name)
        if not cell:
            continue
        preds = (cell.get('predictions') or {}).get('predicted_questions', [])
        for i, p in enumerate(preds):
            pool.append({'candidate_id': f'{safe(name)}-pred-{i}',
                         'question': p.get('question_text', '')})
    actuals_flat = []
    for name in ANALYSTS:
        cell = summary['per_analyst'].get(name)
        if not cell:
            continue
        for ai, a in enumerate(actuals_by.get(name, [])):
            actuals_flat.append({'actual_id': f'{safe(name)}-actual-{ai}',
                                 'question': a.get('question', '')})
    prompt = (B4_STRICT_TPL
              .replace('{{PREDICTED_QUESTIONS_JSON}}', json.dumps(pool, indent=2))
              .replace('{{ACTUAL_QUESTIONS_JSON}}', json.dumps(actuals_flat, indent=2)))
    cid = f'{K}q_{src}_{label}__run{run_i}__{model}__b4strict'
    return {'custom_id': cid, 'method': 'POST', 'url': '/v1/chat/completions',
            'body': {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                     'response_format': {'type': 'json_object'}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='gpt-5-mini', choices=['gpt-5', 'gpt-5-mini'])
    ap.add_argument('--run', type=int, default=1)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    test = json.load(open(f'{DATA_AUTO}/test.json'))
    actuals_by = test['per_analyst_actual_questions']
    sims = find_settings()
    print(f"Found {len(sims)} settings to evaluate (strict B4, {args.model})")

    reqs = []
    for K, src, label, sp in sims:
        summary = json.load(open(sp))
        reqs.append(build_b4_request(K, src, label, summary, actuals_by, args.model, args.run))

    with open(args.out, 'w') as f:
        for r in reqs:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {len(reqs)} B4-strict requests to {args.out}")
    rate = 0.6 if args.model == 'gpt-5-mini' else 10
    print(f"Approx tokens-out: {len(reqs)*600} = ${len(reqs)*600*rate/1e6:.3f} (batch, excl input)")


if __name__ == '__main__':
    main()
