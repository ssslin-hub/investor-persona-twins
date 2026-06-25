"""Build a strict-B4 batch that repeats the SAME setting N times to measure
evaluation (judge) variance — isolating it from seed/prediction variance.

For each chosen setting dir, emit N B4-strict requests (same predictions, same
actuals) with custom_id:  <dirtag>__run<i>__<model>__b4strictvar

Lets us see which actual questions cross the score>=3 (covered) threshold across runs.
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

# Default: highest seed-variance cells (one fixed seed each), spanning sources at K=14.
DEFAULT_SETTINGS = [
    'final_eval_14q_v5',
    'final_eval_14q_auto',
    'final_eval_14q_v1',
    'final_eval_10q_v1',
]


def safe(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower())


def build_request(dirname, summary, actuals_by, model, run_i):
    pool = []
    for name in ANALYSTS:
        cell = summary['per_analyst'].get(name)
        if not cell:
            continue
        for i, p in enumerate((cell.get('predictions') or {}).get('predicted_questions', [])):
            pool.append({'candidate_id': f'{safe(name)}-pred-{i}', 'question': p.get('question_text', '')})
    actuals_flat = []
    for name in ANALYSTS:
        cell = summary['per_analyst'].get(name)
        if not cell:
            continue
        for ai, a in enumerate(actuals_by.get(name, [])):
            actuals_flat.append({'actual_id': f'{safe(name)}-actual-{ai}', 'question': a.get('question', '')})
    prompt = (B4_STRICT_TPL
              .replace('{{PREDICTED_QUESTIONS_JSON}}', json.dumps(pool, indent=2))
              .replace('{{ACTUAL_QUESTIONS_JSON}}', json.dumps(actuals_flat, indent=2)))
    cid = f'{dirname}__run{run_i}__{model}__b4strictvar'
    return {'custom_id': cid, 'method': 'POST', 'url': '/v1/chat/completions',
            'body': {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                     'response_format': {'type': 'json_object'}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='gpt-5-mini')
    ap.add_argument('--runs', type=int, default=5)
    ap.add_argument('--settings', default=','.join(DEFAULT_SETTINGS))
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    test = json.load(open(f'{DATA_AUTO}/test.json'))
    actuals_by = test['per_analyst_actual_questions']
    dirs = [d.strip() for d in args.settings.split(',') if d.strip()]

    reqs = []
    for dirname in dirs:
        sp = f'{DATA_AUTO}/{dirname}/summary.json'
        summary = json.load(open(sp))
        for run_i in range(1, args.runs + 1):
            reqs.append(build_request(dirname, summary, actuals_by, args.model, run_i))

    with open(args.out, 'w') as f:
        for r in reqs:
            f.write(json.dumps(r) + '\n')
    print(f"Wrote {len(reqs)} requests ({len(dirs)} settings x {args.runs} runs) to {args.out}")


if __name__ == '__main__':
    main()
