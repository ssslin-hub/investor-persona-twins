# Phase 17 — v5 K=10 baseline (n=5 runs each, [min, max] notation)

3 persona sources (v5, V1, Auto) × 2 evaluator models (gpt-5, gpt-5-mini) × **5 runs each** = 30 total eval passes. Reports `mean [min, max]` across 5 runs to avoid the symmetric-range misread that `mean ± spread` causes.

**Note**: this supersedes the earlier n=3 version. The `±` notation in the prior report was misleading because the empirical range is asymmetric around the mean (`±X` implied `[mean−X, mean+X]` but actual was `[min, max]` with mean offset from center).

---

## Headline table (n=5)

| Persona | Eval | B2 binary | B2 strong | B2 avg | B4 cov | B4 prec |
|---|---|---|---|---|---|---|
| **v5** | gpt-5 | **0.550** [0.500, 0.583] | 1.0 [1.0, 1.0] | 2.55 [2.50, 2.67] | **0.750** [0.667, 0.833] | 0.509 [0.418, 0.591] |
| **v5** | gpt-5-mini | 0.667 [0.583, 0.750] | 2.6 [1.0, 4.0] | 2.75 [2.58, 3.00] | 0.817 [0.750, 0.917] | 0.675 [0.109, 0.873] |
| **V1** | gpt-5 | 0.400 [0.333, 0.500] | 0.4 [0.0, 1.0] | 2.30 [2.17, 2.50] | 0.667 [0.583, 0.833] | 0.611 [0.545, 0.691] |
| **V1** | gpt-5-mini | 0.683 [0.500, 0.750] | 2.4 [0.0, 4.0] | 2.63 [2.42, 3.00] | 0.817 [0.667, 0.917] | 0.785 [0.700, 0.917] |
| **Auto** | gpt-5 | 0.500 [0.417, 0.583] | 0.8 [0.0, 1.0] | 2.50 [2.42, 2.58] | 0.711 [0.636, 0.750] | 0.529 [0.445, 0.645] |
| **Auto** | gpt-5-mini | 0.767 [0.750, 0.833] | 4.0 [3.0, 5.0] | 3.00 [2.92, 3.17] | 0.783 [0.750, 0.833] | 0.595 [0.082, 0.809] |

---

## Decision rule outcome (user-locked from Phase 17 plan)

| Comparison | n=5 numbers | Outcome |
|---|---|---|
| v5 vs V1 on gpt-5 B2 binary | 0.550 vs 0.400 = **+15pp** | **v5 BEATS V1** (was +11pp at n=3 → bigger gap with more data) |
| v5 vs Auto on gpt-5 B2 binary | 0.550 vs 0.500 = **+5pp** | **v5 BEATS Auto** (was tied at n=3 → v5 now slightly ahead) |
| v5 vs V1 on gpt-5-mini B2 binary | 0.667 vs 0.683 = **−2pp** | v5 ≈ V1 on mini |
| v5 vs Auto on gpt-5-mini B2 binary | 0.667 vs 0.767 = **−10pp** | v5 < Auto on mini |

**Verdict (unchanged from n=3, strengthened by more data)**: v5 personas effective on their own under the canonical gpt-5 evaluator. With n=5 the v5 vs Auto comparison tilts in v5's favor (was tied, now +5pp).

## Key changes vs n=3 report

| Metric | n=3 ± (old) | n=5 [min, max] (new) | Δ mean |
|---|---|---|---|
| v5 gpt-5 B2 binary | 0.528 ± 0.083 | 0.550 [0.500, 0.583] | +0.022 (v5 actually slightly better than n=3 suggested) |
| V1 gpt-5 B2 binary | 0.417 ± 0.167 | 0.400 [0.333, 0.500] | −0.017 |
| Auto gpt-5 B2 binary | 0.528 ± 0.167 | 0.500 [0.417, 0.583] | −0.028 |
| V1 gpt-5 spread | 0.167 (range) | 0.167 (range still) | wide variance is real |
| Auto gpt-5 spread | 0.167 (range) | 0.167 (range still) | wide variance is real |
| **v5 gpt-5 spread** | **0.083 (range)** | **0.083 (range)** | **v5 stays the tightest** |

Going from n=3 to n=5 didn't move means by more than 0.03 — the 3-run estimates were already within their own noise. **v5 has tightest variance (0.083 spread); V1 and Auto have ~2× the spread (0.167).** This is the key paper-defensible finding: v5 is more consistent across reruns than V1 or Auto.

## Secondary findings (still hold under n=5)

1. **v5 leads B4 cov on gpt-5** (0.750 vs V1 0.667 vs Auto 0.711). v5's richer recurring_concerns spec gives broader topic coverage even though simulator doesn't explicitly use queue_behavior / cross_analyst_reactivity.

2. **gpt-5 vs mini bias**: mini gives systematically higher B2 binary (~+0.15 lift) across all settings. Use gpt-5 as canonical for paper; mini for cheap iteration only.

3. **mini's B4 prec is very high variance**: v5/mini = [0.109, 0.873] — 0.764 range. Mini's set-level B4 is unstable at this scale. Stick with gpt-5 for B4 prec reporting.

4. **V1 leads id-matched coverage** on gpt-5 (3.7 avg, vs v5 2.0 and Auto 2.7). v5 inherits Auto-style "twins converge on shared topics" rather than V1's persona-discriminated routing.

## Files

- `data_auto/phase17_aggregate.json` — full n=5 aggregate
- `data_auto/final_eval_10q_{v5,v1,auto}/v5_compare/{gpt-5,gpt-5-mini}/run_{1..5}/{b2_per_actual,b2_summary,b4}.json` — 30 per-run outputs
- `data_auto/final_eval_10q_{v5,v1,auto}/v5_compare/{gpt-5,gpt-5-mini}/aggregate.json` — 6 per-setting-per-model aggregates
- `src/rerun_v5_k10.py`, `src/eval_v5_compare.py` — drivers (N_RUNS=5)
