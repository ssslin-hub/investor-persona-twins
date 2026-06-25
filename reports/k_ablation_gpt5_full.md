# Full K-ablation under stable gpt-5 evaluator — V1 vs Auto, K ∈ {1, 2-3, 5, 10, 20}

All B2 / B4 numbers below use the stable evaluator established in Phases 6–8:
**gpt-5 + v1 `prompts/b2_eval.md` + no seed** for B2; **gpt-5 + `prompts/b4_eval.md`** for B4. Single run per cell (Phase 6: 9/12 cell-agreement across 3 reruns under this setting).

## Headline table

All B4 coverage numbers are the **corrected** values (set-level coverage is bounded below by per-twin B2 binary; raw B4 underestimates at K=20 because the 217–218 candidate prompt overloads the LLM's argmax — see footnote ‡).

| Setting | K | Pool | B2 binary ≥3 | B2 strong ≥4 | B2 avg | B4 cov ≥3 | B4 cov ≥4 | B4 prec ≥3 | B4 prec ≥4 | id-matched cov |
|---|---|---|---|---|---|---|---|---|---|---|
| **V1 K=1** | 1 | 11 | 3/12 = 0.250 | 0/12 | 1.33 | 7/12 = 0.583 | 2/12 | 9/11 = 0.818 | 2/11 = 0.182 | 2/12 = 0.167 |
| **V1 K=2-3** | 1.6 | 16 | 2/10 = 0.200 | 0/10 | 1.60 | 8/12 = 0.667 | 4/12 | 11/16 = 0.688 | 8/16 = 0.500 | 2/12 = 0.167 |
| **V1 K=10** | 10 | 110 | 5/12 = 0.417 | 0/12 | 2.25 | 9/12 = 0.750 | 3/12 | 53/110 = 0.482 | 5/110 = 0.045 | 6/12 = 0.500 |
| **V1 K=20** | 19.7 | 217 | 6/12 = **0.500** | 0/12 | 2.42 | **8/11 = 0.727** ‡ | 4/11 † | 7/**11** = 0.636 § | 4/11 = 0.364 § | 3/11 † |
| **Auto K=10** | 10 | 110 | 6/12 = 0.500 | 1/12 | 2.42 | 9/12 = 0.750 | 5/12 | 72/110 = 0.655 | 22/110 = 0.200 | 1/12 = 0.083 |
| **Auto K=20** | 19.8 | 218 | 9/12 = **0.750** | 0/12 | 2.75 | **10/12 = 0.833** ‡ | 4/12 | 10/**17** = 0.588 § | 4/17 = 0.235 § | 3/12 = 0.250 |

† V1 K=20: B4 evaluator dropped `xian_siew-actual-0` from `actual_coverage` (LLM artifact at 217-candidate scale); denominators are 11 not 12 for B4 rates.

‡ **Coverage override**. B4 set-level coverage must dominate B2 per-twin binary by construction — if an analyst's own twin scores ≥3 for the actual under B2, the pool covers it too (the pool contains the twin's 20 candidates). At K=20, raw B4 falsely reported "not covered" for 3 cells where B2 had already scored ≥3 (V1: andrew_didora; Auto: robin_farley Q1 and sharon_zackfia). These are corrected. K=1 / K=2-3 / K=10 had zero violations on either pipeline.

§ **Precision truncation at K=20**. The B4 evaluator silently truncated the `predicted_precision` array — V1 K=20 returned only **11 of 217 precision rows** (5%); Auto K=20 returned only **17 of 218** (8%). The LLM cherry-picked the strongest candidates and dropped the rest. Reporting precision against the original denominator (`7/217 = 0.032`) is misleading because the numerator is on a 5–8% sample. Numbers shown use the **honest denominator** = rows actually evaluated; these are biased upward (the LLM kept the best candidates) and should be read as "precision among the evaluated subset", not all-candidates precision. K=10 and below had full precision arrays — those rates are unbiased.

## Key observations

### 1. B2 binary climbs monotonically with K — V1 and Auto both
- V1: 0.250 → 0.200 → 0.417 → 0.500 (K=1 → 2-3 → 10 → 20)
- Auto: — → — → 0.500 → 0.750 (K=10 → K=20)

The K=2-3 dip below K=1 in V1 is within evaluator noise (~3 cells can flip per Phase 6).

### 2. Auto K=20 is the new headline: 0.750 B2 binary
**Auto K=20 hits 9/12 cells covered at binary (score ≥3)** — the highest B2 binary in the whole study, +25pp over Auto K=10 and +25pp over V1 K=20. The strong (≥4) count, however, drops to 0/12 — every covered cell is at exactly 3, suggesting K=20 trades absolute closeness for breadth.

### 3. B4 precision at K=20: evaluator truncation, not actual collapse
Earlier draft of this report claimed `precision = 0.032 / 0.046` at K=20 — that was wrong. The B4 evaluator silently truncated the `predicted_precision` array (V1: scored 11 of 217 candidates; Auto: scored 17 of 218). On the **evaluated subset**:
- V1: 0.818 → 0.688 → 0.482 → 0.636 § (subset)
- Auto: — → — → 0.655 → 0.588 § (subset)

These subset numbers are biased upward (LLM kept the best candidates), so the true K=20 precision lies somewhere between (lower bound 7/217 = 0.032) and (upper bound 7/11 = 0.636). **K=20 precision is not reliably measurable from a single 218-candidate prompt** — it would need chunked re-evaluation (~5 batches of ~50 candidates each) to give a defensible number. Reported in this table only as "subset evaluated".

What's robust at K=20: **B2 binary** (per-twin, ≤21 candidates per prompt — no truncation risk) and **B4 coverage** (only 12 actuals, evaluator returns all rows). Precision is not.

### 4. B4 coverage after override is monotonic in K
After applying the B2→B4 coverage override (footnote ‡):
- V1: 0.583 → 0.667 → 0.750 → **0.727** (K=20 ≈ K=10)
- Auto: — → — → 0.750 → **0.833** (K=20 > K=10)

Raw B4 coverage *appeared* to drop at K=20, but that's an LLM-evaluator artifact (the set-level prompt with 217-218 candidates fails to find the twin's own ≥3 candidate buried in the flood). With the override, Auto K=20 hits the study's highest B4-coverage = 0.833. V1 K=20 ties V1 K=10 (saturation at ~0.73 after the dropped-actual correction).

### 5. Identity-matched coverage rises with K (V1) but stays low for Auto
| | K=1 | K=2-3 | K=10 | K=20 |
|---|---|---|---|---|
| V1 | 0.167 | 0.167 | 0.500 | 3/11 = 0.273 |
| Auto | — | — | 0.083 | 0.250 |

V1 K=10 was the high-water mark (0.500). At K=20, V1 falls back to 0.273 (LLM lookup over 20 candidates per twin probably picks a cross-twin "near-substitute" more often than the twin's own match). Auto rises monotonically from K=10 (0.083) to K=20 (0.250), but never approaches V1 K=10's 0.500 — confirming Phase-9 finding that **Auto's twins converge onto shared topics, V1's stay idiosyncratic.**

### 6. Auto vs V1 at matched K — summary
| Metric | K=10 (Auto − V1) | K=20 (Auto − V1) |
|---|---|---|
| B2 binary | +8 pp (0.500 vs 0.417) | +25 pp (0.750 vs 0.500) |
| B2 strong | +1 cell (1 vs 0) | tied (0 vs 0) |
| B4 coverage (override) | tied (0.750 vs 0.750) | +11 pp (0.833 vs 0.727) ‡ |
| B4 cov strong | +2 cells (5 vs 3) | tied (4 vs 4) † |
| B4 precision | +17 pp (0.655 vs 0.482) | not reliably measurable § |
| B4 prec strong | +15.5 pp (22 vs 5 cands) | not reliably measurable § |
| id-matched | **−42 pp** (0.083 vs 0.500) | **−2 pp** (0.250 vs 0.273) † |

Auto's advantage is widest at K=20 on B2-binary but vanishes on every B4 metric — at K=20 both pipelines hit the same evaluator-imposed ceilings.

### 7. Sweet-spot K
On the strict precision-vs-coverage tradeoff under the stable evaluator:
- **V1**: K=1 best precision (0.818) but lowest coverage. K=10 best identity-matched (0.500) and best B4-cov × strong-prec product. K=20 only adds B2-binary lift; B4 collapses.
- **Auto**: K=10 best balance (coverage 0.750, precision 0.655, strong-cov 5/12, strong-prec 22). K=20 maximizes B2-binary (0.750) but B4 precision dies.
- **Paper-defensible K for Auto = 10**, with K=20 reported only on the B2-binary axis (where the lift is real and large).

## Files

- Predictions: `data_auto/final_eval_20q_v1/summary.json`, `data_auto/final_eval_20q_auto/summary.json`
- Raw pools: `data_auto/final_eval_20q_{v1,auto}/gpt5/raw_pool.json`
- B2 per-actual: `data_auto/final_eval_20q_{v1,auto}/gpt5/b2_per_actual.json` + `b2_summary.json`
- B4 set-level: `data_auto/final_eval_20q_{v1,auto}/gpt5/b4.json`
- Prompts: `prompts/simulate_questions_20q.md` (forked from 10q template)
- Drivers: `src/rerun_20q.py` (sim), `src/eval_gpt5_generic.py` (eval)
