"""K-curve report comparing coverage methods (seed-1, strict rubric):
  single-call mini (existing strict_b4/b4.json) vs chunked mini vs chunked gpt-5.
Writes reports/strict_b4_chunked_kcurve.md.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data_auto')
REPORTS = os.path.join(ROOT, 'reports')
KS = [5, 10, 12, 14, 16, 18, 20]
SOURCES = ['v1', 'v5', 'auto']


def load(path, key):
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path))['set_metrics'].get(key)
    except Exception:
        return None


def fmt(x):
    return f"{x:.3f}" if isinstance(x, (int, float)) else "—"


def main():
    lines = ["# Chunked strict B4 coverage — K-curve (seed-1, gpt-5-mini vs gpt-5)\n",
             "Strict rubric (`prompts/b4_eval_strict.md`). **single mini** = one B4 call over the full "
             "pool (existing `strict_b4/b4.json`). **chunked** = pool split into ≤50-candidate chunks, "
             "max match-score per actual across chunks (covered if ≥3). One run per config.\n",
             "All coverage = set-level over 12 actuals.\n"]
    for src in SOURCES:
        lines.append(f"\n## {src}\n")
        lines.append("| K | single mini cov | chunked mini cov | chunked gpt-5 cov | | chunked mini prec | chunked gpt-5 prec |")
        lines.append("|---|---|---|---|---|---|---|")
        for K in KS:
            base = f"{DATA}/final_eval_{K}q_{src}"
            sc = load(f"{base}/strict_b4/b4.json", 'coverage_rate')
            cm = load(f"{base}/strict_b4_chunked/gpt_5_mini/b4.json", 'coverage_rate')
            cg = load(f"{base}/strict_b4_chunked/gpt_5/b4.json", 'coverage_rate')
            pm = load(f"{base}/strict_b4_chunked/gpt_5_mini/b4.json", 'precision_rate')
            pg = load(f"{base}/strict_b4_chunked/gpt_5/b4.json", 'precision_rate')
            delta = ""
            if isinstance(cg, (int, float)) and isinstance(sc, (int, float)):
                delta = f"gpt5 vs single {cg - sc:+.3f}"
            lines.append(f"| {K} | {fmt(sc)} | {fmt(cm)} | {fmt(cg)} | {delta} | {fmt(pm)} | {fmt(pg)} |")
        lines.append("")

    # Takeaways
    lines.append("\n## Reading\n")
    lines.append("- **chunked mini > single mini** quantifies the chunking measurement lift (with mini's "
                 "leniency baked in — upper bound).")
    lines.append("- **chunked gpt-5** is the trustworthy number: chunk-retrieval + a reliable judge.")
    lines.append("- **chunked gpt-5 vs single mini** (Δ column) = the honest 'does chunking improve "
                 "coverage' answer; expected positive and widening with K (more candidates the single call "
                 "is blind to).")
    lines.append("- **chunked gpt-5 < chunked mini** = how much of the mini chunked number was inflation.\n")

    os.makedirs(REPORTS, exist_ok=True)
    path = os.path.join(REPORTS, 'strict_b4_chunked_kcurve.md')
    with open(path, 'w') as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {path}")


if __name__ == '__main__':
    main()
