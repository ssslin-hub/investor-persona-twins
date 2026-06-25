"""Poll the strict-B4 batch tracker; when complete, download output and write each
setting's result to <setting>/strict_b4/b4.json (non-clobbering — does NOT touch the
lenient variance_batch/.../b4.json files).

custom_id schema: <K>q_<src>_<label>__run<N>__<model>__b4strict
Idempotent: safe to re-run.
"""
import argparse, json, os, re, sys
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_AUTO = os.path.join(ROOT, 'data_auto')

CID_RE = re.compile(r'^(\d+)q_(v1|v5|auto)_([a-z0-9]+)__run(\d+)__([a-z0-9-]+)__b4strict$')


def setting_dir(K, src, label):
    """Map (K, src, label) back to the on-disk final_eval_* directory."""
    if label == 's1':
        return f'{DATA_AUTO}/final_eval_{K}q_{src}'
    # s2..s5, rerun2..rerun5
    return f'{DATA_AUTO}/final_eval_{K}q_{src}_{label}'


def parse_output(lines):
    written, errors = 0, []
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        cid = rec['custom_id']
        m = CID_RE.match(cid)
        if not m:
            errors.append(('unparseable_cid', cid)); continue
        K, src, label = int(m.group(1)), m.group(2), m.group(3)
        resp = rec.get('response')
        if not (resp and resp.get('status_code') == 200):
            errors.append(('http_error', cid)); continue
        content = resp['body']['choices'][0]['message']['content']
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            mm = re.search(r'\{.*\}', content, re.DOTALL)
            if not mm:
                errors.append(('json_parse_fail', cid)); continue
            payload = json.loads(mm.group())
        out_dir = os.path.join(setting_dir(K, src, label), 'strict_b4')
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
          f"(completed={batch.request_counts.completed}/{batch.request_counts.total}, "
          f"failed={batch.request_counts.failed})")
    if batch.status != 'completed':
        print("Not complete yet; re-run later.")
        return 1
    out_file_id = batch.output_file_id
    if not out_file_id:
        print("No output file; check error_file_id.")
        return 1
    content = client.files.content(out_file_id).text
    lines = content.splitlines()
    written, errors = parse_output(lines)
    print(f"Wrote {written} strict_b4/b4.json files")
    if errors:
        print(f"{len(errors)} problems:")
        for kind, cid in errors[:20]:
            print(f"  {kind}: {cid}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
