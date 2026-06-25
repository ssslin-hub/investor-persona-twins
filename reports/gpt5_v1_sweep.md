# gpt-5 v1 evaluator sweep — V1 K=1 / K=2-3 / K=10 vs Auto K=10 (Phase 9)

All numbers below use the **stable evaluator setting** identified in Phase 6/7/7b/8:
**gpt-5 + v1 `prompts/b2_eval.md` + no seed** for B2, and **gpt-5 + `prompts/b4_eval.md`** for B4. Single run per setting (Phase 6 already characterized 3-run variance ≈ 9/12 cell-agreement).

## Headline table

| Setting | K | Candidates | B2 binary ≥3 | B2 strong ≥4 | B2 avg | B4 cov ≥3 | B4 cov ≥4 | B4 prec ≥3 | B4 prec ≥4 | id-matched cov |
|---|---|---|---|---|---|---|---|---|---|---|
| **V1 K=1** | 1 | 11 | 3/12 = **0.250** | 0/12 | 1.33 | 7/12 = **0.583** | 2/12 | 9/11 = **0.818** | 2/11 = 0.182 | 2/12 = 0.167 |
| **V1 K=2-3** | 1.6 avg | 16 | 2/10 = **0.200** | 0/10 | 1.60 | 8/12 = **0.667** | 4/12 | 11/16 = **0.688** | 8/16 = 0.500 | 2/12 = 0.167 |
| **V1 K=10** | 10 | 110 | 5/12 = **0.417** | 0/12 | 2.25 | 9/12 = **0.750** | 3/12 | 53/110 = **0.482** | 5/110 = 0.045 | 6/12 = **0.500** |
| **Auto K=10** | 10 | 110 | 6/12 = **0.500** | 1/12 | 2.42 | 9/12 = **0.750** | 5/12 | 72/110 = **0.655** | 22/110 = **0.200** | 1/12 = 0.083 |

Notes:
- V1 K=2-3 cold-start (xian/kevin) have no V1 predictions on disk, so B2 evaluates only 10 cells (9 returning + Robin split into 2). All other rows evaluate the full 12 cells.
- Robin Farley's 2 actuals always split into 2 B2 cells; counts in the table treat them separately.
- B4 set-level coverage/precision use score ≥3 (binary_match) for the standard rate and ≥4 (very-close substitute) for the strong rate.
- Identity-matched coverage = the fraction of *covered* actuals whose best-predicted candidate comes from the **same** analyst's twin (not cross-borrowed).

## Reading the table

### Auto vs V1 at matched K=10
- **B2 binary 0.500 (Auto) vs 0.417 (V1) = +8 pp** — under the stable evaluator, the Auto-discovery loop's per-twin score-matching is moderately better, but the margin is **smaller than the Phase 1 +20 pp coarse-hit lift suggested**.
- **B2 strong (≥4) 1/12 vs 0/12** — Auto produces the only score-4 cell (xian siew); V1 K=10 has no near-substitute calls.
- **B4 coverage 0.750 vs 0.750** — set-level coverage **identical**; both pools' 110 candidates between them cover the same 9/12 actuals.
- **B4 precision 0.655 vs 0.482 = +17 pp** — Auto's 110 candidates are markedly more on-topic on average. **This is the cleanest Auto-vs-V1 win.**
- **B4 strong precision 0.200 vs 0.045 = +15 pp** — Auto produces 22 score-4 candidates in 110 vs V1's 5.
- **Identity-matched coverage**: V1 K=10 = 6/12 (0.500), Auto K=10 = 1/12 (0.083). **V1 routes the right question to the right twin more often.** Auto's set-level coverage relies more heavily on cross-twin borrowing. This is a real and surprising finding — see "Caveat" below.

### K as a confound (within V1)
| | K=1 | K=2-3 | K=10 |
|---|---|---|---|
| B2 binary | 0.250 | 0.200 | 0.417 |
| B4 coverage | 0.583 | 0.667 | 0.750 |
| B4 precision | 0.818 | 0.688 | 0.482 |
| id-matched | 0.167 | 0.167 | 0.500 |

- B4 coverage climbs monotonically with K (0.58 → 0.67 → 0.75), as expected — more candidates = higher chance any actual is covered by something in the pool.
- B4 precision falls monotonically (0.82 → 0.69 → 0.48) — also expected; with K=10 the simulator is forced to generate filler beyond its 1-2 most-confident picks.
- **B2 binary is non-monotonic** (0.25 → 0.20 → 0.42). K=10's lift is real (more candidates per cell = higher chance one of them matches the actual); K=2-3's *dip* below K=1 is small and likely within evaluator noise (Phase 6: 9/12 cell agreement → up to 3 cells can flip across runs).
- Identity-matched coverage triples at K=10 (0.17 → 0.50). This is the most surprising row: at K=10 the V1 pipeline *does* route correctly to the right twin; at K=1/K=2-3 it does not. Likely mechanism: V1's K=2-3 prompt was tuned for "predict the 1-2 most likely questions" which encourages each twin to grab the most salient topic of the moment (often shared across twins), whereas K=10 forces topic diversity within each twin and so each twin keeps its own niche.

### Caveat on identity-matched coverage
The Auto K=10 identity-matched = 1/12 (only brandt) vs V1 K=10 = 6/12 is the **inverse** of the relationship Auto wins on every other metric. Two possible explanations:
1. **Auto's twins converge.** The auto-discovery loop's Variant A shared-prompt edits encourage all twins to look at the same management signals (Med disruption, fuel hedge, Trifecta), so the gpt-5 evaluator picks "the best matching candidate from any twin" — and that happens to come from a non-original twin much more often. V1 twins remain more idiosyncratic, so when V1 covers an actual it usually comes from the right twin.
2. **Evaluator artifact.** With 110 candidates close to each other in semantic space (all on the same call's topics), the LLM's argmax over candidates is unstable — small wording differences flip which candidate it tags as "best-predicted". Phase 6 showed 7/12 cells flipped on trigger_alignment across reruns even when the top score was stable; the same instability could be flipping `best_predicted_candidate_id` here.

Suggested follow-up (not in this phase): re-run the B4 evaluator 3× on Auto K=10 to see whether identity-matched coverage is stable at 1/12 or whether it averages to a higher number with high variance.

## Raw candidate pools

Each setting's full predicted question pool is exported to:
- `data_auto/final_eval_1q_v1/gpt5/raw_pool.json` (11 candidates)
- `data_auto/final_eval_v1_default/gpt5/raw_pool.json` (16 candidates)
- `data_auto/final_eval_10q_v1/gpt5/raw_pool.json` (110 candidates)
- `data_auto/final_eval_10q_auto/b4_gpt5/` — Auto K=10 pool was dumped in Phase 8 (110 candidates).

## Per-cell B2 outputs (V1 K=10 detail, since it's the headline comparison row)

| analyst | score 0-4 | binary | reasoning summary (truncated) |
|---|---|---|---|
| matthew boss | 3 | ✓ | (in b2_per_actual.json) |
| steven wieczynski | 2 | · | |
| brandt montour | 3 | ✓ | |
| james hardiman | 3 | ✓ | |
| lizzie dove | 2 | · | |
| robin farley Q0 | 2 | · | |
| robin farley Q1 | 2 | · | |
| vince ciepiel | 3 | ✓ | |
| sharon zackfia | 1 | · | |
| andrew didora | 3 | ✓ | |
| xian siew | 2 | · | |
| kevin kopelman | 1 | · | |

## Files

- `src/rerun_1q_v1.py` — generates V1 K=1 predictions
- `src/wrap_v1_default.py` — wraps V1 K=2-3 raw predictions into summary.json shape
- `src/eval_gpt5_generic.py` — generic gpt-5 B2+B4+pool driver
- Per-setting outputs:
  - `data_auto/final_eval_1q_v1/{summary.json, gpt5/{raw_pool,b2_per_actual,b2_summary,b4}.json}`
  - `data_auto/final_eval_v1_default/{summary.json, gpt5/{...}.json}`
  - `data_auto/final_eval_10q_v1/{summary.json, gpt5/{...}.json}`
  - `data_auto/final_eval_10q_auto/gpt5/{b2_per_actual,b2_summary}.json` + `b4_gpt5/b4.json` (Phase 8)
