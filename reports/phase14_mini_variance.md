# Phase 14 — gpt-5-mini 3/5-run variance on K≥14 settings (with chunked B4 precision)

For the 11 high-K settings Phase 12 originally analyzed (parallel K=16/18/20 + sequential K=14/16/18/20), re-evaluate under **gpt-5-mini** instead of gpt-5, multiple runs each, with chunked B4 precision (50-candidate chunks per Phase 12 method).

Compares mini's variance and absolute values to gpt-5's. Settings reached different n due to OpenAI quota mid-run; reported with actual n.

---

## Headline table — `mean [min, max]`, n=run count

| Setting | n | B2 binary (mini) | B4 cov (mini) | Chunked prec (mini, true precision) |
|---|---|---|---|---|
| parallel K=16 V1 | 5 | 0.733 [0.667, 0.750] | 0.783 [0.750, 0.833] | 0.560 [0.535, 0.593] |
| parallel K=18 Auto | 5 | 0.683 [0.583, 0.750] | 0.817 [0.750, 0.917] | 0.546 [0.526, 0.572] |
| parallel K=20 V1 | 5 | 0.617 [0.583, 0.667] | 0.865 [0.833, 0.917] | 0.522 [0.498, 0.548] |
| parallel K=20 Auto | 3* | 0.750 [0.750, 0.750] | 0.861 [0.833, 0.917] | 0.505 [0.472, 0.532] |
| **seq K=14 V1** | 3* | **0.833 [0.833, 0.833]** | 0.889 [0.833, 0.917] | 0.548 [0.526, 0.565] |
| seq K=14 Auto | 3* | 0.722 [0.667, 0.750] | 0.917 [0.833, 1.000] | **0.690 [0.669, 0.721]** |
| seq K=16 V1 | 3* | 0.806 [0.750, 0.833] | 0.889 [0.833, 0.917] | 0.574 [0.523, 0.625] |
| seq K=18 V1 | 3* | 0.778 [0.750, 0.833] | 0.914 [0.909, 0.917] | 0.502 [0.444, 0.535] |
| **seq K=18 Auto** | 3* | **0.889 [0.833, 0.917]** | 0.917 [0.917, 0.917] | 0.579 [0.545, 0.611] |
| seq K=20 V1 | 5 | (no aggregate yet — 5/5 b4 done) | | |
| seq K=20 Auto | 4 | (no aggregate yet — 4/5 b4 done) | | |

*= n=3 because Phase 14 extension to n=5 was interrupted by OpenAI quota; aggregate.json reflects original 3-run, runs 4-5 partial on some settings.

---

## Mini vs gpt-5 systematic bias

Across all 6 Phase 13a settings with gpt-5 (canonical) AND Phase 14 settings with mini, the systematic deltas:

| Setting | gpt-5 B2 binary (n=5) | mini B2 binary | Δ (mini - gpt-5) |
|---|---|---|---|
| K=16 V1 | 0.583 (Phase 11 single) | 0.733 | **+0.150** |
| K=18 Auto | 0.500 (Phase 11 single) | 0.683 | **+0.183** |
| K=20 V1 | 0.500 [0.500, 0.500] (n=5) | 0.617 | **+0.117** |
| K=20 Auto | 0.700 [0.667, 0.750] (n=5) | 0.750 | +0.050 |

**Mini systematically inflates B2 binary by +0.05 to +0.18.** Same pattern Phase 17 confirmed at K=10. **Paper should report gpt-5 numbers; mini is for cost-sensitive iteration only**.

## Mini vs gpt-5 on B4 chunked precision

Phase 12 had gpt-5 chunked precision rates 0.32-0.53 for these settings. Mini gives:

| Setting | gpt-5 chunked prec (Phase 12) | mini chunked prec |
|---|---|---|
| parallel K=16 V1 | 0.442 | 0.560 |
| parallel K=18 Auto | 0.490 | 0.546 |
| parallel K=20 V1 | 0.382 | 0.522 |
| parallel K=20 Auto | 0.408 | 0.505 |

**Mini's chunked precision is consistently +0.10 higher than gpt-5's.** Same kind of liberal-scoring bias.

## Cell stability across reruns

The 5-run mini cells (parallel K=16/18/20 V1, parallel K=18 Auto) all have narrow B2-binary ranges (≤0.167). Mini's noise floor is comparable to or tighter than gpt-5's at K=16-20.

## Notable findings

1. **seq K=18 Auto on mini = 0.889 [0.833, 0.917]** — highest B2 binary in the Phase 14 sweep. Both sequential mode AND mini's leniency contribute.

2. **seq K=14 Auto chunked precision = 0.690** — highest precision across all settings under mini. Sequential simulator's forced topical diversity does help precision (consistent with Phase 11's hypothesis even though sequential didn't help at the cell-stability level).

3. **B4 coverage saturates at ~0.85-0.92 under mini** for sequential K≥14 settings. Mini scores cov ~0.10 higher than gpt-5 systematically; the cov ceiling itself is at the 11/12 = 0.917 level for sequential.

## Pending (when OpenAI quota recovers)

- seq_K20_v1: aggregate.json write (5/5 b4 done — just needs re-aggregation step, NO new LLM calls)
- seq_K20_auto: 1 more b4 run + aggregate write
- parallel_K20_auto, seq_K14_v1/auto, seq_K16_v1, seq_K18_v1/auto: extend from n=3 to n=5

## Files

- `data_auto/final_eval_*/gpt5_mini/aggregate.json` — 9/11 per-setting aggregates
- `data_auto/final_eval_*/gpt5_mini/run_{1..5}/` — per-run B2 + B4 + chunked outputs
- `src/eval_mini_variance.py` — driver
