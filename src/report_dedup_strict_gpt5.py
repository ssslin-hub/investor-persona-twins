"""Report the gpt-5 dedup (dedup_strict_gpt5) per round, side-by-side with the old
chunked-mini dedup (dedup_strict). Writes reports/dedup_strict_gpt5.md.
"""
import json, os
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
DATA=os.path.join(ROOT,'data_auto'); REPORTS=os.path.join(ROOT,'reports')
CONFIGS=[('v1','final_eval_14q_v1',14),('v5','final_eval_20q_v5',20),('auto','final_eval_20q_auto',20)]
def load(p):
    try: return json.load(open(p))
    except Exception: return None
def fmt(m,r):
    if m is None: return '—'
    return f"{m:.3f} [{r[0]:.3f},{r[1]:.3f}]" if r and r[0]!=r[1] else f"{m:.3f}"
L=["# Dedup under the reliable metric — chunked + strict + gpt-5 (drop & eval)\n",
   "Per-round dedup with **gpt-5** for both the per-analyst drop decision and the chunked strict "
   "evaluation (1 run/round). Compared against the earlier chunked-**mini** dedup (`dedup_strict/`), "
   "whose coverage was inflated. Round 0 = un-deduped pool.\n"]
for label,sdir,K in CONFIGS:
    g=load(f"{DATA}/{sdir}/dedup_strict_gpt5/trace.json")
    mi=load(f"{DATA}/{sdir}/dedup_strict/trace.json")
    L.append(f"\n## {label} — `{sdir}` (K={K})\n")
    if not g:
        L.append("_(gpt-5 trace not found yet)_\n"); continue
    mini_cov={r['round']:r['cov_mean'] for r in mi['rounds']} if mi else {}
    L.append(f"- gpt-5 total dropped: {g['total_dropped']}/{K*11}; final kept: {g['total_kept']}.\n")
    L.append("| round | m | pool | drops | **gpt-5 cov** | gpt-5 prec | (mini cov, old) |")
    L.append("|---|---|---|---|---|---|---|")
    for r in g['rounds']:
        mc=mini_cov.get(r['round'])
        L.append(f"| {r['round']} | {r.get('m','-')} | {r['pool_size']} | {r.get('drops_this_round',0)} "
                 f"| {fmt(r.get('cov_mean'),r.get('cov_range'))} | {fmt(r.get('prec_mean'),r.get('prec_range'))} "
                 f"| {mc:.3f} |" if mc is not None else
                 f"| {r['round']} | {r.get('m','-')} | {r['pool_size']} | {r.get('drops_this_round',0)} "
                 f"| {fmt(r.get('cov_mean'),r.get('cov_range'))} | {fmt(r.get('prec_mean'),r.get('prec_range'))} | — |")
    r0,rl=g['rounds'][0],g['rounds'][-1]
    dcov=rl['cov_mean']-r0['cov_mean']; dprec=rl['prec_mean']-r0['prec_mean']; dpool=rl['pool_size']-r0['pool_size']
    if dpool==0:
        verdict="no candidates dropped — dedup is a no-op; the cov/prec change is single-run eval noise (same pool)"
    elif dcov>=-0.08 and dprec>0:
        verdict="coverage held, precision improved — dedup helps"
    elif dcov<-0.08:
        verdict="coverage dropped materially — dedup hurts"
    else:
        verdict="coverage held but precision did not improve — dedup ~neutral (within single-run noise)"
    L.append(f"\n**Takeaway (gpt-5):** pool {r0['pool_size']}→{rl['pool_size']} ({dpool:+d}), "
             f"cov {r0['cov_mean']:.3f}→{rl['cov_mean']:.3f} ({dcov:+.3f}), "
             f"prec {r0['prec_mean']:.3f}→{rl['prec_mean']:.3f} ({dprec:+.3f}). {verdict}.\n")
L.append("\n## Note\n- The old `dedup_strict/` coverage (mini) was inflated by chunk⊗mini leniency "
         "(see `FINAL_chunking_conjecture.md`); the gpt-5 column here is the trustworthy metric.")
os.makedirs(REPORTS,exist_ok=True)
open(os.path.join(REPORTS,'dedup_strict_gpt5.md'),'w').write("\n".join(L)+"\n")
print("Wrote reports/dedup_strict_gpt5.md")
