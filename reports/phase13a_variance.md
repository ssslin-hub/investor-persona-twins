# Phase 13a — gpt-5 evaluator variance across K=10/14/20 × V1/Auto (n=5, [min, max])

For each of 6 settings, B2 (12 per-actual cells) + B4 (set-level) was re-run **5 times** under gpt-5. Reports per-run values, 5-run mean, and `[min, max]` range. The `±spread` notation in the prior 3-run draft is replaced by explicit `[min, max]` to avoid the symmetric-range misread (asymmetric distributions look misleading under `±`).

---

## Headline table (n=5)

| Setting | cells stable | B2 binary runs | mean | [min, max] | B4 cov runs | B4 cov mean |
|---|---|---|---|---|---|---|
| K=10 V1 | 7/12 | 0.500, 0.417, 0.333, 0.417, 0.500 | 0.433 | [0.333, 0.500] | 0.750/0.750/0.583/0.667/0.750 | 0.700 |
| K=10 Auto | 6/12 | 0.500, 0.583, 0.500, 0.500, 0.500 | 0.517 | [0.500, 0.583] | 0.667×4 / 0.750 | 0.683 |
| **K=14 V1** | 8/12 | **0.917, 0.833, 0.833, 0.833, 0.833** | **0.850** | [0.833, 0.917] | 0.667/0.667/0.750/0.833/0.727 | 0.729 |
| K=14 Auto | 8/12 | 0.667, 0.667, 0.667, 0.583, 0.583 | 0.633 | [0.583, 0.667] | 0.750×4 / 0.818 | 0.764 |
| K=20 V1 | 9/12 | 0.500 × 5 | **0.500** | [0.500, 0.500] | 0.750 × 5 | 0.750 |
| K=20 Auto | 7/12 | 0.667, 0.667, 0.667, 0.750, 0.750 | 0.700 | [0.667, 0.750] | 0.667/0.583/0.667/0.667/0.750 | 0.667 |

---

## Surprises vs Phase 11 single-run AND vs Phase 13a's n=3 draft

| Setting | Phase 11 single | Phase 13a n=3 mean | **Phase 13a n=5 mean** | n=3→n=5 Δ |
|---|---|---|---|---|
| K=10 V1 | 0.417 | 0.417 | 0.433 | +0.016 |
| K=10 Auto | 0.500 | 0.528 | 0.517 | −0.011 |
| K=14 V1 | 0.667 | 0.861 | **0.850** | −0.011 (stable, **still study high**) |
| K=14 Auto | 0.667 | 0.667 | 0.633 | −0.034 |
| K=20 V1 | 0.500 | 0.500 | 0.500 | 0 (perfectly stable) |
| K=20 Auto | 0.750 | 0.667 | **0.700** | +0.033 |

**Key takeaways**:
- **V1 K=14 = 0.850 [0.833, 0.917] is the study high** for B2 binary. Phase 11's single 0.667 was a low outlier; both n=3 and n=5 agree it's ≈0.85.
- **Auto K=20 = 0.700 [0.667, 0.750]** — Phase 11's single 0.750 was a high outlier; true mean ≈0.70 but the high tail of 0.750 does appear in 2/5 runs.
- **K=20 V1 = perfectly deterministic** under gpt-5: 0.500 × 5 with 0 range — best paper-defensible point if absolute reproducibility matters.

## Cell-level stability (5-run agreement)

| Setting | cells stable / 12 (5-run agreement) |
|---|---|
| K=10 V1 | 7/12 |
| K=10 Auto | 6/12 (worst) |
| K=14 V1 | 8/12 |
| K=14 Auto | 8/12 |
| K=20 V1 | **9/12** (best) |
| K=20 Auto | 7/12 |

K=10 is the noisiest (more cells in the 2↔3 boundary zone); K=20 V1 the most evaluator-stable (deterministic at headline + 9/12 cells unanimous).

## Decision implications

1. **Paper headline B2 binary candidate**: V1 K=14 = 0.850 (mean across 5 runs, range [0.833, 0.917]). Robust against Phase 11's single-run noise.
2. **Most evaluator-deterministic point**: K=20 V1 = 0.500 with zero range across 5 runs.
3. **Auto K=20 should be reported as 0.700 [0.667, 0.750]** — not the 0.750 that Phase 11 reported.
4. **K=10 Auto and V1 both have wide ranges** (Auto 0.083, V1 0.167) — should always be reported with the explicit range, never as a single point.

## Files

- `data_auto/final_eval_{K}q_{src}/variance/run_{1..5}/{b2_per_actual,b2_summary,b4}.json` — per-run outputs (180 files)
- `data_auto/final_eval_{K}q_{src}/variance/aggregate.json` — per-setting 5-run aggregate
- `src/eval_gpt5_variance.py` — driver
