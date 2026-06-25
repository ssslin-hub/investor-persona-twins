"""Aggregate all <setting>/strict_b4/b4.json into a K-curve table per persona source.

Walks final_eval_* dirs, reads strict_b4/b4.json set_metrics, groups by (source, K)
across seeds → mean[min,max] of coverage_rate and precision_rate.
Writes reports/all_settings_strict_b4_mini.md.
"""
import json, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_AUTO = os.path.join(ROOT, 'data_auto')
REPORTS = os.path.join(ROOT, 'reports')

DIR_RE = re.compile(r'^final_eval_(\d+)q_(v1|v5|auto)(?:_(s\d|rerun\d))?$')


def collect():
    rows = []  # (src, K, label, cov, prec)
    for d in sorted(os.listdir(DATA_AUTO)):
        m = DIR_RE.match(d)
        if not m:
            continue
        K, src, label = int(m.group(1)), m.group(2), (m.group(3) or 's1')
        p = os.path.join(DATA_AUTO, d, 'strict_b4', 'b4.json')
        if not os.path.exists(p):
            continue
        sm = json.load(open(p)).get('set_metrics', {})
        rows.append((src, K, label, sm.get('coverage_rate'), sm.get('precision_rate')))
    return rows


def stat(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    mn, mx, mean = min(vals), max(vals), sum(vals) / len(vals)
    return f"{mean:.3f} [{mn:.3f}, {mx:.3f}]" if len(vals) > 1 else f"{mean:.3f}"


def main():
    rows = collect()
    by = defaultdict(lambda: {'cov': [], 'prec': []})
    for src, K, label, cov, prec in rows:
        by[(src, K)]['cov'].append(cov)
        by[(src, K)]['prec'].append(prec)

    os.makedirs(REPORTS, exist_ok=True)
    out = os.path.join(REPORTS, 'all_settings_strict_b4_mini.md')
    lines = []
    lines.append("# Strict B4 rubric — gpt-5-mini, all auto/v1/v5 settings\n")
    lines.append("Evaluator: **gpt-5-mini** + `prompts/b4_eval_strict.md` (substitution-test rubric), "
                 "single run per setting. Coverage/precision shown as `mean [min, max]` over seeds "
                 "(n = number of seed reruns). B4-only, set-level.\n")
    lines.append(f"Settings evaluated: {len(rows)} (parsed `strict_b4/b4.json` files).\n")

    Ks = sorted({K for _, K in by})
    for src in ['v1', 'v5', 'auto']:
        present = [(K) for (s, K) in by if s == src]
        if not present:
            continue
        lines.append(f"\n## {src}\n")
        lines.append("| K | n | strict cov | strict prec |")
        lines.append("|---|---|---|---|")
        for K in Ks:
            if (src, K) not in by:
                continue
            cov = by[(src, K)]['cov']
            prec = by[(src, K)]['prec']
            n = len([c for c in cov if c is not None])
            lines.append(f"| {K} | {n} | {stat(cov)} | {stat(prec)} |")

    # Flat per-setting appendix
    lines.append("\n## Per-setting detail\n")
    lines.append("| source | K | seed | strict cov | strict prec |")
    lines.append("|---|---|---|---|---|")
    for src, K, label, cov, prec in sorted(rows):
        cs = f"{cov:.3f}" if cov is not None else "—"
        ps = f"{prec:.3f}" if prec is not None else "—"
        lines.append(f"| {src} | {K} | {label} | {cs} | {ps} |")

    with open(out, 'w') as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {out} ({len(rows)} settings)")

    # Quick sanity print
    v5k10 = [r for r in rows if r[0] == 'v5' and r[1] == 10]
    if v5k10:
        covs = [r[3] for r in v5k10 if r[3] is not None]
        print(f"Sanity v5 K=10 strict cov: {covs} (expect ~0.50-0.67)")


if __name__ == '__main__':
    main()
