"""Aggregate strict-dedup traces into reports/dedup_strict_best_configs.md.

Reads <source-dir>/dedup_strict/trace.json for each configured source and emits a
per-round table (m, pool_size, drops, strict cov mean[min,max], strict prec mean[min,max])
with a takeaway about whether coverage held while precision/pool improved.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data_auto')
REPORTS = os.path.join(ROOT, 'reports')

SOURCES = [
    ('v1', 'final_eval_14q_v1', 14),
    ('v5', 'final_eval_20q_v5', 20),
    ('auto', 'final_eval_20q_auto', 20),
]


def fmt(mean, rng):
    if mean is None:
        return '—'
    return f"{mean:.3f} [{rng[0]:.3f}, {rng[1]:.3f}]" if rng else f"{mean:.3f}"


def main():
    lines = ["# Strict iterative dedup (\"deadout\") — best config per source\n",
             "Recursive-halving anchor dedup under the strict rubric (`prompts/b4_eval_strict.md`) for "
             "both the drop decision (gpt-5-mini ×3, majority ≥2/3) and the per-round evaluation "
             "(gpt-5-mini ×3, averaged). Round 0 = original pool (no drops). Coverage/precision are "
             "set-level over the 12-actual holdout.\n",
             "Configs chosen = highest strict coverage per source: v1 K=14, v5 K=20, auto K=20.\n"]

    for label, sdir, K in SOURCES:
        tpath = os.path.join(DATA, sdir, 'dedup_strict', 'trace.json')
        if not os.path.exists(tpath):
            lines.append(f"\n## {label} — `{sdir}` (K={K})\n\n_(trace not found yet)_\n")
            continue
        t = json.load(open(tpath))
        rounds = t['rounds']
        lines.append(f"\n## {label} — `{sdir}` (K={K})\n")
        lines.append(f"- Total dropped: {t['total_dropped']} / {K*11}; final pool kept: {t['total_kept']}.\n")
        lines.append("| round | m | pool size | drops this round | strict cov | strict prec |")
        lines.append("|---|---|---|---|---|---|")
        for r in rounds:
            lines.append(f"| {r['round']} | {r.get('m','-')} | {r['pool_size']} | "
                         f"{r.get('drops_this_round',0)} | "
                         f"{fmt(r.get('cov_mean'), r.get('cov_range'))} | "
                         f"{fmt(r.get('prec_mean'), r.get('prec_range'))} |")
        # takeaway
        r0, rl = rounds[0], rounds[-1]
        d_cov = rl['cov_mean'] - r0['cov_mean']
        d_prec = rl['prec_mean'] - r0['prec_mean']
        d_pool = rl['pool_size'] - r0['pool_size']
        lines.append("")
        lines.append(f"**Takeaway:** pool {r0['pool_size']}→{rl['pool_size']} ({d_pool:+d}), "
                     f"strict cov {r0['cov_mean']:.3f}→{rl['cov_mean']:.3f} ({d_cov:+.3f}), "
                     f"strict prec {r0['prec_mean']:.3f}→{rl['prec_mean']:.3f} ({d_prec:+.3f}). "
                     + ("Coverage held while precision improved — dedup worked." if d_cov >= -0.08 and d_prec > 0
                        else "Coverage dropped materially — flag." if d_cov < -0.08
                        else "Precision did not improve.") + "\n")

    os.makedirs(REPORTS, exist_ok=True)
    path = os.path.join(REPORTS, 'dedup_strict_best_configs.md')
    with open(path, 'w') as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {path}")


if __name__ == '__main__':
    main()
