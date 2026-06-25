# Phase 13b — within-twin top-3 pairwise B2 similarity (quantitative)

Each twin's top-3 was extracted from each of 6 settings (`parallel_K{10,14,20}_{v1,auto}`). For every pair of settings (15 per twin), pairwise B2 was computed in both directions (top-3 of A as candidates, top-1 of B as anchor; then swap). Score is mean of the 2 directions, 0-4 scale. **High score = top-3 across settings converge on similar question; low score = top-3 differs across settings.**

This is the quantitative anchor for the Phase 13b qualitative report.

---

## Headline table (sorted by mean similarity)

| Analyst | History | Mean | Min | Max | Spread | Top-3 V1↔Auto verdict |
|---|---|---|---|---|---|---|
| lizzie dove | 34 | **3.73** | 2 | 4 | 2 | very stable across all 6 settings |
| vince ciepiel | 89 | 3.50 | 3 | 4 | 1 | tight (yield+demand+new hardware locked) |
| brandt montour | 186 | 3.37 | 2 | 4 | 2 | stable (Med booking-curve persistent) |
| matthew boss | 76 | 3.03 | 2 | 4 | 2 | mid; V1 keeps Trifecta, Auto drops it |
| robin farley | 230 | 2.90 | 2 | 4 | 2 | mid; pricing/yield + Med across settings |
| steven wieczynski | 139 | 2.83 | 2 | 4 | 2 | mid; booking visibility shared, but mix vs costs varies |
| xian siew | 0 | 2.77 | 2 | 4 | 2 | (cold-start, generic) |
| kevin kopelman | 0 | 2.73 | 0 | 4 | 4 | (cold-start, generic; one 0 outlier) |
| sharon zackfia | 9 | 2.60 | 0 | 4 | 4 | V1 (passenger/loyalty) ≠ Auto (AI/pre-booking) — major split |
| james hardiman | 80 | 2.50 | 0 | 4 | 4 | V1 (ROIC/Perfecta) ≠ Auto (fuel→ROIC drift) — major split |
| andrew didora | 3 | **1.53** | 0 | 4 | 4 | V1 (bond financing) ≠ Auto (fuel hedging) — totally different topics |

## Key patterns

### 1. Mean similarity ≠ history length
Same conclusion as Phase 15: history depth does not drive top-3 stability across settings. lizzie (history 34) is #1; andrew (history 3) is #11. brandt (186) and robin (230) are mid-table because their V1 and Auto personas pin them to *slightly* different sub-topics — both yield/demand themes, but the LLM picks different sub-angles.

### 2. V1-vs-Auto persona divergence is the biggest source of variation
The 4 lowest-mean analysts (sharon, james, andrew, kevin) all show **0 in their min column** — at least one pair of (V1 setting × Auto setting) scored 0 in B2. Diagnosis:
- **andrew (1.53 mean, spread 4)**: V1 personas push him onto bond financing (capital_structure / cost_of_financing); Auto personas pin him to fuel hedging. Two completely different topics → V1↔Auto pairs get 0-1 scores.
- **sharon (2.60, spread 4)**: V1 = passenger/source-market mix + loyalty; Auto = pre-booking penetration + AI/digital. Different topics → 0 scores in cross-source pairs.
- **james (2.50, spread 4)**: V1 = Perfecta/ROIC + CapEx; Auto = fuel→ROIC→yield (drifts). Some V1↔Auto pairs score 0.
- **kevin (cold-start)**: high spread driven by one outlier pair, not systematic.

### 3. Cross-K stability within same source is high
For brandt (matrix shown in raw output), V1↔V1 pairs are mostly 4 (K10_v1 vs K14_v1 = 4, K14_v1 vs K20_v1 = 4) and Auto↔Auto pairs similarly stable. The lower mean comes from V1↔Auto cross-source pairs scoring 2-3. **Within a persona source, K=10/14/20 produce essentially the same top-3 — confirming Phase 11 finding that K is not the top-3 driver.**

### 4. Cold-start (xian, kevin) have mid-range stability
Despite having no history, both score 2.77 / 2.73 (mid-pack). Because they use the SAME fallback persona under both V1 and Auto, their top-3 converges on the generic Med/yield/fuel triple regardless of source. No V1-vs-Auto divergence to drag them down.

## Synthesis with Phase 13b qualitative

The qualitative report classified all 11 twins as **persona-pinned** (9) or **mixed** (2). The quantitative pairwise scores split them differently:

| Quantitative bucket | Cutoff | Twins | Qualitative class |
|---|---|---|---|
| Very tight (≥3.3) | mean ≥ 3.3 | lizzie, vince, brandt | persona-pinned (3) |
| Tight (3.0-3.3) | 3.0-3.3 | matthew | persona-pinned (1) |
| Moderate (2.7-3.0) | 2.7-3.0 | robin, steven, xian, kevin | persona-pinned (4) |
| Loose (<2.7) | <2.7 | sharon, james, andrew | mixed (2) + persona-pinned (andrew) |

**The two reports agree on the extremes**: lizzie/vince/brandt are most stable; sharon/james/andrew are most variable. The disagreement on andrew (qualitative said "persona-pinned, just to different topics for V1 vs Auto") is resolved by the quantitative score (1.53) which captures exactly that — V1 and Auto pin to different topics, so cross-source similarity is bad.

## Recommendation

If we want a single number per twin summarizing "how much do K-axis + persona-source axis change my top-3?", **use the mean pairwise B2 from this report**. It correctly identifies:
- Stable twins (≥3.0): lizzie, vince, brandt, matthew — these analysts' personas are convergent enough that K and V1/Auto don't shift the predicted top-3 much
- Unstable twins (<2.0): andrew — V1 and Auto are pointing at entirely different topics for him; need to decide which is canonical

## Files

- `data_auto/top_picks/within_twin_pairwise.json` — full 11 × 6 × 6 score matrix per analyst
- `data_auto/top_picks/pairwise_logs/` — 330 B2 prompts/responses
- `src/top3_similarity.py` — driver
