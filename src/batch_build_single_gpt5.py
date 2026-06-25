"""Single-call strict B4 (full pool, one request) with gpt-5, for the 21 seed-1 configs.
For comparison against chunked gpt-5 (isolating the chunking effect under a reliable judge).

custom_id: {K}q_{src}_s1__single__gpt-5__b4single
"""
import argparse, json, os, sys, re

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='gpt-5')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    actuals = []
    ab = json.load(open(f'{DATA_AUTO}/test.json'))['per_analyst_actual_questions']
    for name in ANALYSTS:
        for ai, a in enumerate(ab.get(name, [])):
            actuals.append({'actual_id': f'{safe(name)}-actual-{ai}', 'question': a.get('question', '')})
    reqs = []
    for K in KS:
        for src in SOURCES:
            sp = f'{DATA_AUTO}/final_eval_{K}q_{src}/summary.json'
            if not os.path.exists(sp):
                continue
            summary = json.load(open(sp))
            pool = []
            for name in ANALYSTS:
                for i, p in enumerate((summary['per_analyst'][name].get('predictions') or {}).get('predicted_questions', [])):
                    pool.append({'candidate_id': f'{safe(name)}-pred-{i}', 'question': p.get('question_text', '')})
            prompt = (B4_STRICT_TPL
                      .replace('{{PREDICTED_QUESTIONS_JSON}}', json.dumps(pool, indent=2))
                      .replace('{{ACTUAL_QUESTIONS_JSON}}', json.dumps(actuals, indent=2)))
            cid = f'{K}q_{src}_s1__single__{args.model}__b4single'
            reqs.append({'custom_id': cid, 'method': 'POST', 'url': '/v1/chat/completions',
                         'body': {'model': args.model, 'messages': [{'role': 'user', 'content': prompt}],
                                  'response_format': {'type': 'json_object'}}})
    with open(args.out, 'w') as f:
        for r in reqs:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {len(reqs)} single-call {args.model} requests to {args.out}")


if __name__ == '__main__':
    main()
