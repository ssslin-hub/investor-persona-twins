"""Poll single-call gpt-5 batch; when done, write <setting>/strict_b4_single_gpt5/b4.json
and a comparison report: single-call gpt-5 vs chunked gpt-5 (+ single mini, chunked mini).
"""
import json, os, re, sys
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data_auto'); REPORTS = os.path.join(ROOT, 'reports')
KS = [5,10,12,14,16,18,20]; SRC = ['v1','v5','auto']
CID = re.compile(r'^(\d+)q_(v1|v5|auto)_s1__single__([a-z0-9-]+)__b4single$')

def cov_of(payload):
    ac = payload.get('actual_coverage', [])
    return sum(1 for x in ac if (x.get('match_score_0_to_4') or 0) >= 3)/len(ac) if ac else None

def getcov(p):
    try: return json.load(open(p))['set_metrics']['coverage_rate']
    except Exception: return None

def f(x): return f"{x:.3f}" if isinstance(x,(int,float)) else "—"

def main():
    t = json.load(open(os.path.join(DATA,'batch','tracker_single_gpt5.json')))
    c = OpenAI(); b = c.batches.retrieve(t['batch_id'])
    print(f"batch {b.id}: {b.status} {b.request_counts.completed}/{b.request_counts.total} failed={b.request_counts.failed}")
    if b.status != 'completed':
        print("not done"); return 1
    for line in c.files.content(b.output_file_id).text.splitlines():
        if not line.strip(): continue
        rec = json.loads(line); m = CID.match(rec['custom_id'])
        if not m: continue
        K,src = int(m.group(1)), m.group(2)
        resp = rec.get('response')
        if not (resp and resp.get('status_code')==200): continue
        content = resp['body']['choices'][0]['message']['content']
        try: payload = json.loads(content)
        except json.JSONDecodeError:
            mm = re.search(r'\{.*\}', content, re.DOTALL); payload = json.loads(mm.group()) if mm else None
        if payload is None: continue
        od = os.path.join(DATA, f'final_eval_{K}q_{src}', 'strict_b4_single_gpt5'); os.makedirs(od, exist_ok=True)
        cov = cov_of(payload)
        json.dump({'K':K,'source':src,'model':'gpt-5','set_metrics':{'coverage_rate':cov},
                   'actual_coverage':payload.get('actual_coverage',[])}, open(os.path.join(od,'b4.json'),'w'), indent=2)
    # report
    L = ["# Chunk vs single-call under gpt-5 (strict, seed-1)\n",
         "Same judge (gpt-5), same strict rubric. **single** = one B4 call over full pool. "
         "**chunked** = ≤50/chunk, max-per-actual. Δ = chunked − single (the pure chunking effect).\n"]
    for src in SRC:
        L.append(f"\n## {src}\n")
        L.append("| K | single gpt-5 | chunked gpt-5 | Δ chunk−single | (single mini) (chunked mini) |")
        L.append("|---|---|---|---|---|")
        for K in KS:
            base = f"{DATA}/final_eval_{K}q_{src}"
            sg = getcov(f"{base}/strict_b4_single_gpt5/b4.json")
            cg = getcov(f"{base}/strict_b4_chunked/gpt_5/b4.json")
            sm = getcov(f"{base}/strict_b4/b4.json")
            cm = getcov(f"{base}/strict_b4_chunked/gpt_5_mini/b4.json")
            d = f"{cg-sg:+.3f}" if isinstance(sg,(int,float)) and isinstance(cg,(int,float)) else "—"
            L.append(f"| {K} | {f(sg)} | {f(cg)} | {d} | {f(sm)} / {f(cm)} |")
        L.append("")
    path = os.path.join(REPORTS,'chunk_vs_single_gpt5.md'); open(path,'w').write("\n".join(L)+"\n")
    print("Wrote", path)
    return 0

sys.exit(main())
