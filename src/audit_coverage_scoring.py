"""Audit B4 coverage scoring: for each actual, show the matched predicted question +
score under (a) single-call strict and (b) chunked strict (max-over-chunks), so a
human can judge whether the scores are reasonable.

Usage: python3 src/audit_coverage_scoring.py --source-dir final_eval_20q_v5 --chunk-size 50
Writes reports/coverage_scoring_audit_<source>.md
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_client import call_llm, parse_json_strict
from run_pipeline import load_text

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data_auto')
STRICT = load_text(os.path.join(ROOT, 'prompts', 'b4_eval_strict.md'))
ANALYSTS = ['matthew boss', 'steven wieczynski', 'brandt montour', 'james hardiman',
            'lizzie dove', 'robin farley', 'vince ciepiel', 'sharon zackfia',
            'andrew didora', 'xian siew', 'kevin kopelman']


def safe(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower())


def clean(s, n=240):
    s = ' '.join((s or '').split())
    return s if len(s) <= n else s[:n] + '…'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-dir', required=True)
    ap.add_argument('--chunk-size', type=int, default=50)
    args = ap.parse_args()

    sdir = os.path.join(DATA, args.source_dir)
    summary = json.load(open(os.path.join(sdir, 'summary.json')))
    actuals_by = json.load(open(f'{DATA}/test.json'))['per_analyst_actual_questions']

    # candidate id -> text
    ctext = {}
    cands = []
    for name in ANALYSTS:
        for i, p in enumerate((summary['per_analyst'][name].get('predictions') or {}).get('predicted_questions', [])):
            cid = f'{safe(name)}-pred-{i}'
            ctext[cid] = p.get('question_text', '')
            cands.append({'candidate_id': cid, 'question': p.get('question_text', '')})
    actuals = []
    atext = {}
    for name in ANALYSTS:
        for ai, a in enumerate(actuals_by.get(name, [])):
            aid = f'{safe(name)}-actual-{ai}'
            atext[aid] = a.get('question', '')
            actuals.append({'actual_id': aid, 'question': a.get('question', '')})

    # (a) single-call: reuse existing strict_b4/b4.json if present, else compute
    sc_path = os.path.join(sdir, 'strict_b4', 'b4.json')
    if os.path.exists(sc_path):
        sc = json.load(open(sc_path))
    else:
        prompt = STRICT.replace('{{PREDICTED_QUESTIONS_JSON}}', json.dumps(cands, indent=2)) \
                       .replace('{{ACTUAL_QUESTIONS_JSON}}', json.dumps(actuals, indent=2))
        sc = parse_json_strict(call_llm(prompt, expect_json=True, model='gpt-5-mini'))
    single = {x['actual_id']: (x.get('match_score_0_to_4'), x.get('best_predicted_candidate_id'))
              for x in sc.get('actual_coverage', [])}

    # (b) chunked: per actual, max-scoring chunk's candidate
    chunks = [cands[i:i + args.chunk_size] for i in range(0, len(cands), args.chunk_size)]
    chunked = {a['actual_id']: (0, None) for a in actuals}
    for ci, ch in enumerate(chunks):
        prompt = STRICT.replace('{{PREDICTED_QUESTIONS_JSON}}', json.dumps(ch, indent=2)) \
                       .replace('{{ACTUAL_QUESTIONS_JSON}}', json.dumps(actuals, indent=2))
        b4 = parse_json_strict(call_llm(prompt, expect_json=True, model='gpt-5-mini'))
        for x in b4.get('actual_coverage', []):
            aid = x.get('actual_id'); s = x.get('match_score_0_to_4') or 0
            if aid in chunked and s > chunked[aid][0]:
                chunked[aid] = (s, x.get('best_predicted_candidate_id'))

    # Report
    out = [f"# Coverage scoring audit — `{args.source_dir}`\n",
           "Per actual: matched predicted question + score under single-call strict vs chunked "
           "strict (max over chunks). Both gpt-5-mini, `b4_eval_strict.md`. covered = score >= 3.\n"]
    sc_cov = sum(1 for s, _ in single.values() if (s or 0) >= 3) / len(single)
    ch_cov = sum(1 for s, _ in chunked.values() if (s or 0) >= 3) / len(chunked)
    out.append(f"**Single-call coverage = {sc_cov:.3f}; chunked coverage = {ch_cov:.3f}.**\n")
    out.append("| actual | single score | chunked score | inflated? |")
    out.append("|---|---|---|---|")
    for aid in atext:
        ss = single.get(aid, (None, None))[0]
        cs = chunked.get(aid, (0, None))[0]
        flag = "⚠️ yes" if (cs or 0) >= 3 and (ss or 0) < 3 else ""
        out.append(f"| `{aid}` | {ss} | {cs} | {flag} |")
    out.append("")
    for aid, at in atext.items():
        ss, sc_cand = single.get(aid, (None, None))
        cs, ch_cand = chunked.get(aid, (0, None))
        out.append(f"\n### `{aid}` — single={ss}, chunked={cs}"
                   + ("  ⚠️ INFLATED" if (cs or 0) >= 3 and (ss or 0) < 3 else ""))
        out.append("\n**ACTUAL:** " + clean(at) + "\n")
        out.append(f"- single-call match (`{sc_cand}`, score {ss}): " + clean(ctext.get(sc_cand, '—')) + "\n")
        out.append(f"- chunked match (`{ch_cand}`, score {cs}): " + clean(ctext.get(ch_cand, '—')) + "\n")

    path = os.path.join(ROOT, 'reports', f'coverage_scoring_audit_{args.source_dir.replace("final_eval_", "")}.md')
    with open(path, 'w') as f:
        f.write("\n".join(out) + "\n")
    print(f"Wrote {path}")
    print(f"single cov={sc_cov:.3f}  chunked cov={ch_cov:.3f}")


if __name__ == '__main__':
    main()
