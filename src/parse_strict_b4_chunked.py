"""Poll the chunked strict B4 batch; when complete, aggregate chunks per (config,model)
into max-score-per-actual coverage + concatenated precision, writing
<setting>/strict_b4_chunked/<model_safe>/b4.json.

custom_id: {K}q_{src}_s1__chunk{ci}__{model}__b4chunk
"""
import argparse, json, os, re, sys
from collections import defaultdict
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_AUTO = os.path.join(ROOT, 'data_auto')
CID_RE = re.compile(r'^(\d+)q_(v1|v5|auto)_s1__chunk(\d+)__([a-z0-9-]+)__b4chunk$')
N_ACTUAL = 12


def parse(lines):
    # group[(K,src,model)] = list of b4 payloads
    groups = defaultdict(list)
    errors = []
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        m = CID_RE.match(rec['custom_id'])
        if not m:
            errors.append(('cid', rec['custom_id'])); continue
        K, src, ci, model = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
        resp = rec.get('response')
        if not (resp and resp.get('status_code') == 200):
            errors.append(('http', rec['custom_id'])); continue
        content = resp['body']['choices'][0]['message']['content']
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            mm = re.search(r'\{.*\}', content, re.DOTALL)
            if not mm:
                errors.append(('json', rec['custom_id'])); continue
            payload = json.loads(mm.group())
        groups[(K, src, model)].append(payload)

    written = 0
    for (K, src, model), payloads in groups.items():
        best = {}      # actual_id -> (max_score, candidate)
        prec_rows = []
        for b4 in payloads:
            for x in b4.get('actual_coverage', []):
                aid = x.get('actual_id'); s = x.get('match_score_0_to_4') or 0
                if aid is None:
                    continue
                if aid not in best or s > best[aid][0]:
                    best[aid] = (s, x.get('best_predicted_candidate_id'))
            prec_rows += b4.get('predicted_precision', [])
        n_act = len(best) or N_ACTUAL
        cov = sum(1 for s, _ in best.values() if s >= 3) / n_act
        useful = sum(1 for r in prec_rows if (r.get('match_score_0_to_4') or 0) >= 3)
        prec = useful / len(prec_rows) if prec_rows else 0.0
        out = {
            'K': K, 'source': src, 'model': model, 'n_chunks': len(payloads),
            'set_metrics': {'coverage_rate': cov, 'precision_rate': prec,
                            'coverage_count': sum(1 for s, _ in best.values() if s >= 3),
                            'useful_prediction_count': useful, 'predicted_question_count': len(prec_rows)},
            'actual_best': {a: {'score': s, 'candidate': c} for a, (s, c) in best.items()},
        }
        model_safe = model.replace('-', '_')
        out_dir = os.path.join(DATA_AUTO, f'final_eval_{K}q_{src}', 'strict_b4_chunked', model_safe)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'b4.json'), 'w') as f:
            json.dump(out, f, indent=2)
        written += 1
    return written, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tracker', required=True)
    args = ap.parse_args()
    tracker = json.load(open(args.tracker))
    client = OpenAI()
    b = client.batches.retrieve(tracker['batch_id'])
    print(f"batch {b.id}: status={b.status} ({b.request_counts.completed}/{b.request_counts.total}, failed={b.request_counts.failed})")
    if b.status != 'completed':
        print("Not complete yet; re-run later.")
        return 1
    lines = client.files.content(b.output_file_id).text.splitlines()
    written, errors = parse(lines)
    print(f"Wrote {written} strict_b4_chunked/<model>/b4.json files")
    for k, c in errors[:20]:
        print(f"  err {k}: {c}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
