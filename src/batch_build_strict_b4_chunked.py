"""Build OpenAI Batch jsonl for CHUNKED strict B4 coverage over seed-1 configs.

For each config (auto/v1/v5 x K), split the full candidate pool into <=chunk-size
chunks; for each model and each chunk emit one strict B4 request (chunk candidates +
all 12 actuals). Parser later aggregates max-score-per-actual across chunks.

custom_id: {K}q_{src}_s1__chunk{ci}__{model}__b4chunk
"""
import argparse, json, os, sys, re, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from run_pipeline import load_text  # noqa: E402

DATA_AUTO = os.path.join(ROOT, 'data_auto')
B4_STRICT_TPL = load_text(os.path.join(ROOT, 'prompts', 'b4_eval_strict.md'))
ANALYSTS = ['matthew boss', 'steven wieczynski', 'brandt montour', 'james hardiman',
            'lizzie dove', 'robin farley', 'vince ciepiel', 'sharon zackfia',
            'andrew didora', 'xian siew', 'kevin kopelman']
KS = [5, 10, 12, 14, 16, 18, 20]
SOURCES = ['v1', 'v5', 'auto']


def safe(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower())


def build_pool(summary):
    pool = []
    for name in ANALYSTS:
        cell = summary['per_analyst'].get(name)
        if not cell:
            continue
        for i, p in enumerate((cell.get('predictions') or {}).get('predicted_questions', [])):
            pool.append({'candidate_id': f'{safe(name)}-pred-{i}', 'question': p.get('question_text', '')})
    return pool


def build_actuals(actuals_by):
    out = []
    for name in ANALYSTS:
        for ai, a in enumerate(actuals_by.get(name, [])):
            out.append({'actual_id': f'{safe(name)}-actual-{ai}', 'question': a.get('question', '')})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--models', default='gpt-5-mini,gpt-5')
    ap.add_argument('--chunk-size', type=int, default=50)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(',') if m.strip()]

    actuals = build_actuals(json.load(open(f'{DATA_AUTO}/test.json'))['per_analyst_actual_questions'])
    reqs = []
    n_cfg = 0
    for K in KS:
        for src in SOURCES:
            sp = f'{DATA_AUTO}/final_eval_{K}q_{src}/summary.json'
            if not os.path.exists(sp):
                continue
            n_cfg += 1
            pool = build_pool(json.load(open(sp)))
            chunks = [pool[i:i + args.chunk_size] for i in range(0, len(pool), args.chunk_size)] or [[]]
            for model in models:
                for ci, ch in enumerate(chunks):
                    prompt = (B4_STRICT_TPL
                              .replace('{{PREDICTED_QUESTIONS_JSON}}', json.dumps(ch, indent=2))
                              .replace('{{ACTUAL_QUESTIONS_JSON}}', json.dumps(actuals, indent=2)))
                    cid = f'{K}q_{src}_s1__chunk{ci}__{model}__b4chunk'
                    reqs.append({'custom_id': cid, 'method': 'POST', 'url': '/v1/chat/completions',
                                 'body': {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                                          'response_format': {'type': 'json_object'}}})

    with open(args.out, 'w') as f:
        for r in reqs:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {len(reqs)} chunk requests ({n_cfg} configs x {len(models)} models) to {args.out}")
    from collections import Counter
    print("per-model:", dict(Counter(r['body']['model'] for r in reqs)))


if __name__ == '__main__':
    main()
