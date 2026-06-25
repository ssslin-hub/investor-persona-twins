"""Poll a strict-B4 variance batch (cid `<dir>__run<i>__<model>__b4strictvar`) and, when
complete, persist each run to <setting>/strict_b4_var/<model_safe>/run_<N>/b4.json.

Run it on each tracker separately (gpt-5 batch, mini batch). Idempotent.
"""
import argparse, json, os, re, sys
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_AUTO = os.path.join(ROOT, 'data_auto')

CID_RE = re.compile(r'^(final_eval_[a-z0-9_]+)__run(\d+)__([a-z0-9-]+)__b4strictvar$')


def parse_output(lines):
    written, errors = 0, []
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        m = CID_RE.match(rec['custom_id'])
        if not m:
            errors.append(('unparseable', rec['custom_id'])); continue
        dirname, run, model = m.group(1), int(m.group(2)), m.group(3)
        resp = rec.get('response')
        if not (resp and resp.get('status_code') == 200):
            errors.append(('http_error', rec['custom_id'])); continue
        content = resp['body']['choices'][0]['message']['content']
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            mm = re.search(r'\{.*\}', content, re.DOTALL)
            if not mm:
                errors.append(('json_fail', rec['custom_id'])); continue
            payload = json.loads(mm.group())
        model_safe = model.replace('-', '_')
        out_dir = os.path.join(DATA_AUTO, dirname, 'strict_b4_var', model_safe, f'run_{run}')
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'b4.json'), 'w') as f:
            json.dump(payload, f, indent=2)
        written += 1
    return written, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tracker', required=True)
    args = ap.parse_args()
    tracker = json.load(open(args.tracker))
    client = OpenAI()
    batch = client.batches.retrieve(tracker['batch_id'])
    print(f"batch {batch.id}: status={batch.status} "
          f"({batch.request_counts.completed}/{batch.request_counts.total}, "
          f"failed={batch.request_counts.failed})")
    if batch.status != 'completed':
        print("Not complete yet; re-run later.")
        return 1
    lines = client.files.content(batch.output_file_id).text.splitlines()
    written, errors = parse_output(lines)
    print(f"Wrote {written} strict_b4_var/.../b4.json files")
    for kind, cid in errors[:20]:
        print(f"  {kind}: {cid}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
