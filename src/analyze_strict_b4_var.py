"""Poll the strict-B4 5x-repeat batch; when complete, for each fixed setting collect
the 5 per-actual scores and surface the actual questions that FLIP across the
covered (score>=3) threshold across the 5 evaluation runs.

custom_id: <dirname>__run<i>__<model>__b4strictvar
Writes reports/strict_b4_eval_variance.md
"""
import argparse, json, os, re, sys
from collections import defaultdict
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_AUTO = os.path.join(ROOT, 'data_auto')
REPORTS = os.path.join(ROOT, 'reports')

CID_RE = re.compile(r'^(final_eval_[a-z0-9_]+)__run(\d+)__([a-z0-9-]+)__b4strictvar$')


def actual_text_map():
    """actual_id -> question text, from test.json."""
    test = json.load(open(f'{DATA_AUTO}/test.json'))
    ab = test['per_analyst_actual_questions']
    m = {}
    for name, lst in ab.items():
        safe = re.sub(r'[^a-z0-9]+', '_', name.lower())
        for ai, a in enumerate(lst):
            m[f'{safe}-actual-{ai}'] = a.get('question', '')
    return m


def pred_text_map(dirname):
    """candidate_id -> predicted question text, from a setting's summary.json."""
    summary = json.load(open(f'{DATA_AUTO}/{dirname}/summary.json'))
    m = {}
    for name, cell in summary['per_analyst'].items():
        safe = re.sub(r'[^a-z0-9]+', '_', name.lower())
        for i, p in enumerate((cell.get('predictions') or {}).get('predicted_questions', [])):
            m[f'{safe}-pred-{i}'] = p.get('question_text', '')
    return m


def collect_runs(lines):
    """dirname -> run -> payload."""
    by = defaultdict(dict)
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        m = CID_RE.match(rec['custom_id'])
        if not m:
            continue
        dirname, run = m.group(1), int(m.group(2))
        resp = rec.get('response')
        if not (resp and resp.get('status_code') == 200):
            continue
        content = resp['body']['choices'][0]['message']['content']
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            mm = re.search(r'\{.*\}', content, re.DOTALL)
            if not mm:
                continue
            payload = json.loads(mm.group())
        by[dirname][run] = payload
    return by


def truncate(s, n=160):
    s = ' '.join(s.split())
    return s if len(s) <= n else s[:n] + '…'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tracker', required=True)
    args = ap.parse_args()
    tracker = json.load(open(args.tracker))
    client = OpenAI()
    batch = client.batches.retrieve(tracker['batch_id'])
    print(f"batch {batch.id}: status={batch.status} "
          f"({batch.request_counts.completed}/{batch.request_counts.total} done, "
          f"{batch.request_counts.failed} failed)")
    if batch.status != 'completed':
        print("Not complete yet; re-run later.")
        return 1
    lines = client.files.content(batch.output_file_id).text.splitlines()
    by = collect_runs(lines)
    amap = actual_text_map()

    out = [
        "# Strict B4 — evaluation (judge) variance on fixed settings\n",
        "Evaluator gpt-5-mini + `prompts/b4_eval_strict.md`, run **5× on the SAME predictions** "
        "per setting (predictions fixed; only judge stochasticity varies). For each actual question "
        "we list the 5 per-run scores (0–4) and mark whether `covered` (score≥3) **flips** across runs.\n",
        f"Batch `{batch.id}`. Settings: {', '.join(sorted(by))}.\n",
    ]

    for dirname in sorted(by):
        runs = by[dirname]
        run_ids = sorted(runs)
        covs = [runs[r]['set_metrics'].get('coverage_rate') for r in run_ids]
        out.append(f"\n## {dirname}\n")
        out.append(f"Coverage per run: {['%.3f' % c for c in covs]} → "
                   f"mean {sum(covs)/len(covs):.3f}, spread {max(covs)-min(covs):.3f}\n")
        # actual_id -> [scores per run]
        scores = defaultdict(dict)
        matched = defaultdict(dict)
        for r in run_ids:
            for ac in runs[r].get('actual_coverage', []):
                scores[ac['actual_id']][r] = ac.get('match_score_0_to_4')
                matched[ac['actual_id']][r] = ac.get('best_predicted_candidate_id')
        flips = []
        stable = 0
        for aid, sc in scores.items():
            vals = [sc.get(r) for r in run_ids if sc.get(r) is not None]
            if not vals:
                continue
            covered_flags = [v >= 3 for v in vals]
            if any(covered_flags) and not all(covered_flags):
                flips.append((aid, vals))
            else:
                stable += 1
        out.append(f"**{len(flips)} of {len(scores)} actual questions flip** the covered threshold "
                   f"across the 5 runs ({stable} stable).\n")
        pmap = pred_text_map(dirname)
        for aid, vals in sorted(flips, key=lambda x: -(max(x[1]) - min(x[1]))):
            out.append(f"\n### `{aid}` — scores {vals} (min {min(vals)}, max {max(vals)})")
            out.append(f"\n**ACTUAL:** {truncate(amap.get(aid, '?'), 220)}\n")
            # show the candidate it matched in the run(s) where it was covered
            cand_ids = {matched[aid].get(r) for r in run_ids if (scores[aid].get(r) or 0) >= 3}
            cand_ids = {c for c in cand_ids if c}
            for c in list(cand_ids)[:2]:
                out.append(f"**matched pred (`{c}`):** {truncate(pmap.get(c, '?'), 220)}\n")

    os.makedirs(REPORTS, exist_ok=True)
    path = os.path.join(REPORTS, 'strict_b4_eval_variance.md')
    with open(path, 'w') as f:
        f.write("\n".join(out) + "\n")
    print(f"Wrote {path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
