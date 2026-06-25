"""Generate an English report of the actual questions whose `covered` (score>=3)
status flips across the 5 mini B4 evaluation runs of a fixed setting, with the
full text of each actual question and every predicted question it matched.

Source: <setting>/variance_batch/gpt_5_mini/run_*/b4.json (lenient rubric, 5 runs).
Output: reports/eval_variance_flip_questions.md
"""
import json, glob, os, re, textwrap
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data_auto')
REPORTS = os.path.join(ROOT, 'reports')

SETTINGS = ['final_eval_14q_v5', 'final_eval_14q_auto', 'final_eval_14q_v1_rerun2',
            'final_eval_10q_v5', 'final_eval_20q_auto']


def clean(s):
    return ' '.join((s or '').split())


def actual_map():
    test = json.load(open(f'{DATA}/test.json'))['per_analyst_actual_questions']
    m = {}
    for name, lst in test.items():
        s = re.sub(r'[^a-z0-9]+', '_', name.lower())
        for ai, a in enumerate(lst):
            m[f'{s}-actual-{ai}'] = a.get('question', '')
    return m


def pred_map(dirn):
    sm = json.load(open(f'{DATA}/{dirn}/summary.json'))
    m = {}
    for name, c in sm['per_analyst'].items():
        s = re.sub(r'[^a-z0-9]+', '_', name.lower())
        for i, p in enumerate((c.get('predictions') or {}).get('predicted_questions', [])):
            m[f'{s}-pred-{i}'] = p.get('question_text', '')
    return m


def collect(dirn):
    runs = sorted(glob.glob(f'{DATA}/{dirn}/variance_batch/gpt_5_mini/run_*/b4.json'))
    peract = {}
    covs = []
    for ri, rp in enumerate(runs):
        b = json.load(open(rp))
        covs.append(b['set_metrics'].get('coverage_rate'))
        for ac in b.get('actual_coverage', []):
            peract.setdefault(ac['actual_id'], {})[ri] = (
                ac.get('match_score_0_to_4'), ac.get('best_predicted_candidate_id'))
    return runs, covs, peract


def main():
    amap = actual_map()
    lines = []
    lines.append("# Evaluation-variance analysis: which questions flip the coverage threshold\n")
    lines.append("**Setup.** For a fixed setting (predictions held constant), the set-level B4 "
                 "evaluator (gpt-5-mini + `prompts/b4_eval.md`) was run 5 times. Only the judge's "
                 "stochasticity differs between runs. An actual question is a *flip* when its "
                 "`covered` status (match score >= 3) is true in some runs and false in others. "
                 "Scores are 0-4 per the rubric; covered = score >= 3.\n")
    lines.append("**Why this matters.** Set coverage is computed over a 12-actual denominator, so "
                 "each flipped question moves coverage by ~0.083. The run-to-run swing in coverage "
                 "is driven almost entirely by a small number of borderline questions, not by "
                 "uniform noise across all 12.\n")

    summary_rows = []
    for dirn in SETTINGS:
        runs, covs, peract = collect(dirn)
        if not runs:
            continue
        pmap = pred_map(dirn)
        flips = []
        for aid, sc in peract.items():
            vals = [sc[r][0] for r in sorted(sc)]
            flags = [v >= 3 for v in vals]
            if any(flags) and not all(flags):
                flips.append((aid, sc, vals))
        flips.sort(key=lambda x: -(max(x[2]) - min(x[2])))
        summary_rows.append((dirn, covs, len(flips), len(peract),
                             [f.split('-actual')[0] for f, _, _ in flips]))

        lines.append(f"\n---\n\n## Setting: `{dirn}`\n")
        lines.append(f"- Persona source / K: derived from the directory name.")
        lines.append(f"- Coverage per run: {['%.3f' % c for c in covs]} "
                     f"(mean {sum(covs)/len(covs):.3f}, spread {max(covs)-min(covs):.3f}).")
        lines.append(f"- Flipping questions: **{len(flips)} of {len(peract)}**.\n")

        for aid, sc, vals in flips:
            lines.append(f"\n### `{aid}` — scores {vals} (min {min(vals)}, max {max(vals)})\n")
            lines.append("**Actual question.**\n")
            lines.append("> " + clean(amap.get(aid, '?')) + "\n")
            # group matched candidates
            cand_runs = defaultdict(list)
            for r in sorted(sc):
                s, cid = sc[r]
                cand_runs[cid].append((r + 1, s))
            lines.append("**Best-matched predicted question(s) across runs.**\n")
            for cid, rs in cand_runs.items():
                tag = ', '.join(f'run{r}={s}' for r, s in rs)
                covered = 'covered (>=3)' if any(s >= 3 for _, s in rs) else 'not covered'
                lines.append(f"- `{cid}` — {tag} → {covered}\n")
                lines.append("  > " + clean(pmap.get(cid, '?')) + "\n")

    # Model comparison section (gpt-5 vs gpt-5-mini) on the borderline questions
    THREE = ['sharon_zackfia-actual-0', 'andrew_didora-actual-0', 'kevin_kopelman-actual-0']
    lines += model_compare_section('final_eval_14q_v5', THREE, amap)
    # Strict-rubric comparison (rendered only when strict_b4_var data is on disk)
    lines += strict_model_compare_section('final_eval_14q_v5', THREE, amap)

    lines.append("\n**gpt-5 vs gpt-5-mini takeaways (same predictions, same rubric).**\n")
    lines.append("- gpt-5 is more self-consistent per question: on `andrew_didora-actual-0` it "
                 "scores a flat 3 in four of five runs (covered 4/5) where mini swings 4/2/4/2/2 "
                 "(covered 2/5). gpt-5 settles on \"covers the hedging part = 3\" instead of "
                 "oscillating between 4 and 2.")
    lines.append("- gpt-5 is more conservative at the boundary: on `sharon_zackfia-actual-0` it "
                 "never marks covered (0/5; max 2), correctly reflecting that no prediction matches "
                 "the itinerary/deferral ask, whereas mini's run-3 spike to 4 (matching an unrelated "
                 "yield question) is a clear judge error. On `kevin_kopelman-actual-0` gpt-5 covers "
                 "only 1/5 vs mini 3/5.")
    lines.append("- Coverage spread is similar (0.250 both) but for different reasons: mini's comes "
                 "from per-question score spikes (including errors); gpt-5's from a steadier spread "
                 "of near-threshold 2s and 3s. Mean coverage is close (gpt-5 0.717 vs mini 0.767), "
                 "but gpt-5's covered counts are lower on the genuinely weak matches — i.e. gpt-5 is "
                 "the stricter, more reliable judge on these borderline items even under the lenient "
                 "rubric.\n")

    # Cross-setting summary (auto-generated over all SETTINGS)
    lines.append("\n---\n\n## Summary across settings\n")
    lines.append("| Setting | mini coverage per run | spread | flips / 12 | flip analysts |")
    lines.append("|---|---|---|---|---|")
    for dirn, covs, nflip, ntot, fanalysts in summary_rows:
        cov_str = ', '.join('%.3f' % c for c in covs)
        spread = max(covs) - min(covs)
        who = ', '.join(fanalysts) if fanalysts else '—'
        lines.append(f"| `{dirn}` | {cov_str} | {spread:.3f} | {nflip}/{ntot} | {who} |")
    lines.append("")
    lines.append("With a 12-actual denominator, each flipped question moves coverage by ~0.083, so "
                 "the observed per-run spreads correspond to roughly 1-3 borderline questions "
                 "changing their covered status. The flips concentrate on the same structural "
                 "boundary cases — a thematically adjacent prediction that does not fully match the "
                 "actual's ask — rather than uniform noise across all questions. Reporting coverage "
                 "as a multi-run mean [min, max] (not a single run) is therefore necessary, and "
                 "gpt-5 is the steadier judge for the canonical number (see the model-comparison "
                 "section above).\n")
    lines.append("## Provenance\n")
    lines.append("- Source: `<setting>/variance_batch/{gpt_5,gpt_5_mini}/run_*/b4.json` (5 runs each; "
                 "lenient rubric `prompts/b4_eval.md`). Per-question scores and matched candidate ids "
                 "from `actual_coverage[]`; actual text from `data_auto/test.json`; predicted text "
                 "from `<setting>/summary.json`.")
    lines.append("- Generator: `src/report_flip_questions.py` (settings in `SETTINGS`; gpt-5 vs "
                 "gpt-5-mini comparison on `final_eval_14q_v5`).\n")

    os.makedirs(REPORTS, exist_ok=True)
    path = os.path.join(REPORTS, 'eval_variance_flip_questions.md')
    with open(path, 'w') as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {path}")


def _runs_scores(dirn, model, targets, subdir='variance_batch'):
    """model dir under <subdir> -> {aid: [(score, cand) per run]} + cov list."""
    runs = sorted(glob.glob(f'{DATA}/{dirn}/{subdir}/{model}/run_*/b4.json'))
    peract = {a: [] for a in targets}
    covs = []
    for rp in runs:
        b = json.load(open(rp))
        covs.append(b['set_metrics'].get('coverage_rate'))
        idx = {ac['actual_id']: ac for ac in b.get('actual_coverage', [])}
        for a in targets:
            ac = idx.get(a)
            peract[a].append((ac.get('match_score_0_to_4'), ac.get('best_predicted_candidate_id'))
                             if ac else (None, None))
    return covs, peract


def model_compare_section(dirn, targets, amap):
    pmap = pred_map(dirn)
    g5_cov, g5 = _runs_scores(dirn, 'gpt_5', targets)
    mn_cov, mn = _runs_scores(dirn, 'gpt_5_mini', targets)
    out = ["\n---\n", f"## Model comparison on the borderline questions — gpt-5 vs gpt-5-mini "
           f"(`{dirn}`, lenient B4, 5 runs each)\n",
           "Same predictions, same rubric (`prompts/b4_eval.md`); only the evaluator model differs. "
           "Coverage = score >= 3.\n",
           f"- gpt-5 coverage per run: {['%.3f' % c for c in g5_cov]} "
           f"(mean {sum(g5_cov)/len(g5_cov):.3f}, spread {max(g5_cov)-min(g5_cov):.3f}).",
           f"- gpt-5-mini coverage per run: {['%.3f' % c for c in mn_cov]} "
           f"(mean {sum(mn_cov)/len(mn_cov):.3f}, spread {max(mn_cov)-min(mn_cov):.3f}).\n"]
    out.append("| actual | gpt-5 scores | gpt-5 covered? | gpt-5-mini scores | mini covered? |")
    out.append("|---|---|---|---|---|")
    for a in targets:
        gv = [s for s, _ in g5[a]]
        mv = [s for s, _ in mn[a]]
        gc = sum(1 for s in gv if s is not None and s >= 3)
        mc = sum(1 for s in mv if s is not None and s >= 3)
        out.append(f"| `{a}` | {gv} | {gc}/5 | {mv} | {mc}/5 |")
    out.append("")
    # per-question detail: which prediction each model matched, run by run
    for a in targets:
        out.append(f"\n### `{a}`\n")
        out.append("**Actual.**\n")
        out.append("> " + clean(amap.get(a, '?')) + "\n")
        for model, data in (('gpt-5', g5), ('gpt-5-mini', mn)):
            out.append(f"**{model} — per run (score → best-matched prediction):**\n")
            seen = {}
            for ri, (s, cid) in enumerate(data[a], 1):
                cov = '✓' if (s is not None and s >= 3) else '✗'
                out.append(f"- run{ri}: score {s} {cov} → `{cid}`")
                if cid and cid not in seen:
                    seen[cid] = True
            for cid in seen:
                out.append(f"\n  > `{cid}`: " + clean(pmap.get(cid, '?')) + "\n")
        out.append("")
    return out


def strict_model_compare_section(dirn, targets, amap):
    """gpt-5 vs gpt-5-mini under the STRICT rubric, reading <setting>/strict_b4_var/."""
    g5_cov, g5 = _runs_scores(dirn, 'gpt_5', targets, subdir='strict_b4_var')
    mn_cov, mn = _runs_scores(dirn, 'gpt_5_mini', targets, subdir='strict_b4_var')
    if not g5_cov and not mn_cov:
        return []  # strict data not yet on disk
    pmap = pred_map(dirn)
    ng, nm = len(g5_cov), len(mn_cov)
    out = ["\n---\n", f"## Strict rubric — gpt-5 vs gpt-5-mini on the borderline questions "
           f"(`{dirn}`, `prompts/b4_eval_strict.md`)\n",
           f"Same predicted pool as the lenient analysis above (same `summary.json`); only the rubric "
           f"(strict) and evaluator model differ. gpt-5 n={ng}, gpt-5-mini n={nm}. Coverage = score >= 3.\n",
           "**Predicted-pool source for the three target analysts:** `sharon_zackfia` = v5, "
           "`andrew_didora` = v5, `kevin_kopelman` = auto-fallback (v5 generation fell back to auto "
           "for this analyst). The pool is identical across models and matches the K=14 flip table.\n"]
    if g5_cov:
        out.append(f"- gpt-5 strict coverage per run: {['%.3f' % c for c in g5_cov]} "
                   f"(mean {sum(g5_cov)/len(g5_cov):.3f}).")
    if mn_cov:
        out.append(f"- gpt-5-mini strict coverage per run: {['%.3f' % c for c in mn_cov]} "
                   f"(mean {sum(mn_cov)/len(mn_cov):.3f}).\n")
    out.append("| actual | gpt-5 strict scores | covered | gpt-5-mini strict scores | covered |")
    out.append("|---|---|---|---|---|")
    for a in targets:
        gv = [s for s, _ in g5[a]]
        mv = [s for s, _ in mn[a]]
        gc = sum(1 for s in gv if s is not None and s >= 3)
        mc = sum(1 for s in mv if s is not None and s >= 3)
        out.append(f"| `{a}` | {gv} | {gc}/{ng} | {mv} | {mc}/{nm} |")
    out.append("")
    for a in targets:
        out.append(f"\n### `{a}` (strict)\n")
        out.append("**Actual.**\n")
        out.append("> " + clean(amap.get(a, '?')) + "\n")
        for model, data, n in (('gpt-5', g5, ng), ('gpt-5-mini', mn, nm)):
            if not n:
                continue
            out.append(f"**{model} strict — per run (score → best-matched prediction):**\n")
            seen = {}
            for ri, (s, cid) in enumerate(data[a], 1):
                cov = '✓' if (s is not None and s >= 3) else '✗'
                out.append(f"- run{ri}: score {s} {cov} → `{cid}`")
                if cid and cid not in seen:
                    seen[cid] = True
            for cid in seen:
                out.append(f"\n  > `{cid}`: " + clean(pmap.get(cid, '?')) + "\n")
        out.append("")
    return out


if __name__ == '__main__':
    main()
