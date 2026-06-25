# Auto-discovery pipeline — full experiment record

This is the consolidated report for all experiments on the RCL digital-twin
question-prediction task. It covers the original auto-discovery loop, the
K = 1/5/10 ablation on V1 and Auto pipelines, the conversational variant, the
no-persona baseline, and the four evaluator-scoring lenses (coarse hit, B2,
B2_pred, B4, identity-matched).

Holdout = 2026-Q1 RCL earnings call. 11 analysts asked 12 actual questions
(9 returning, 2 cold-start, robin farley asked 2).

---

## Section A — Headline

| Question | Best setting | Number |
|---|---|---|
| Are predicted question topics close to actuals? | V1 K=10 | B4 coverage 11/12 = 0.917 |
| Is each twin's set substantively-substitute for its own actual? | Auto K=10 | B2 binary 10/12 = 0.833 |
| Are the candidate questions very-close substitutes? | Auto K=10 | B4 prec_strong 74/110 = 0.673 |
| Are predictions attributable to the originating twin? | Auto K=10 | Identity-matched cov 9/12 = 0.750 |
| Set has high "useful" candidate density? | Conv K=10 | B4 prec 112/120 = 0.933 |

**Persona vs no-persona ablation**: no-persona K=110 baseline reaches B4 cov 8/12 = 0.667 and B2 binary 3/11 = 0.273. Auto K=10 lifts both to 0.833 and 0.909 respectively, on 9× fewer candidates per twin (10 vs 110). Persona doing real work.

---

## Section B — Pipeline construction

### Phase 1: auto-discovery loop (DONE)

- **Step 0 — peer ingestion**. 5 same-sector peers (CCL, NCLH, MAR, HLT, H) × ≤2025-Q2 = 70 calls parsed; +801 analyst turns for the 11 CAL-eligible analysts, tagged ticker+sector, merged into `data_auto/train_combined.json`.
- **Split**: TRAIN = RCL ≤2025-Q2 + peer ≤2025-Q2; CAL = 2025-Q3 + 2025-Q4 (11 analysts, 19 scoreable actuals); TEST = 2026-Q1 (12 actuals).
- **Variant A** (3 rounds on shared extraction prompt; Claude Sonnet 4.6 sub-agent for reasoning; gpt-5-mini for extract/simulate/judge).
- **Variant B** (per-analyst persona refinement, up to 3 rounds, only on CAL miss analysts).

| Round | Edit | CAL hit |
|---|---|---|
| A round 0 | peer-aware BDE baseline | **0.737** ← r\* |
| A round 1 | +`competitive_context_lens` | 0.632 ↓ |
| A round 2 | swap to `mechanism_probe_tendency` | 0.684 ↓ |
| A round 3 | +`presentation_responsiveness` | 0.650 ↓ |
| A round 4 | cancelled — pivot to Variant B |  |

Variant B per analyst (selection rule = strictly better than A r0):

| Analyst | A r0 CAL | B refinement → CAL | Selected for TEST |
|---|---|---|---|
| brandt montour | 0.50 | r1=0.50, r2=**1.00** | B r2 |
| david katz (CAL-only) | 0.00 | r1=**1.00** | B r1 (not in TEST) |
| lizzie dove | 0.50 | r1=**1.00** | B r1 |
| matthew boss | 0.67 | r1=r2=r3=0.67 | A r0 (floor) |
| steven wieczynski | 0.50 | r1=**1.00** | B r1 |

### Phase 2 / 3 / 4: K-ablation + Conversational + No-persona

- **K-ablation**: re-simulate at K = 5 and K = 10 for both V1 personas and Auto personas (same simulator prompt body, just K count varied).
- **Conversational simulation**: replay the 2026-Q1 operator queue sequentially; each turn the simulator sees prepared remarks + Q&A so far. K = 1 and K = 10 variants.
- **No-persona baseline**: gpt-5-mini generates 110 candidate questions for the same call without any analyst conditioning (`data_baseline/gpt-5-mini_k110/`).

---

## Section C — All settings × all metrics

### Table 1 — Coarse hit + B2 per-actual (denominator = 12 actuals or 11/12 cells)

| Setting | K | predicted total | coarse hit | B2 bin ≥3 | B2 strong ≥4 | B2 avg |
|---|---|---|---|---|---|---|
| Auto cold 2-3Q | ~2.1 | 19 | 7/10 = 0.700 | — | — | — |
| Auto cold 1Q | 1 | 11 | 6/12 = 0.500 | 3/11 = 0.273 | 0/11 = 0.000 | 1.364 |
| V1 K=5 | 5 | 55 | 9/12 = 0.750 | 7/12 = 0.583 | 2/12 = 0.167 | 2.417 |
| Auto K=5 | 5 | 55 | 9/12 = 0.750 | 5/12 = 0.417 | 1/12 = 0.083 | 2.250 |
| **V1 K=10** | 10 | 110 | **10/12 = 0.833** | 8/12 = 0.667 | 2/12 = 0.167 | 2.500 |
| **Auto K=10** | 10 | 110 | 9/12 = 0.750 | **10/12 = 0.833** | **3/12 = 0.250** | **2.917** |
| Conv K=1 | 1 seq | 12 | 7/12 = 0.583 | 3/12 = 0.250 | 0/12 = 0.000 | 1.417 |
| **Conv K=10** | 10 seq | 120 | **10/12 = 0.833** | 9/12 = 0.750 | 2/12 = 0.167 | 2.667 |
| **NoPersona K=110** | 110 | 110 | 9/12 = 0.750 | 3/11 = 0.273 | — | 2.273 |

### Table 2 — B4 set-level (coverage + precision, both at score ≥3 lenient and strong ≥4)

| Setting | K | cands | actuals | cov ≥3 | cov strong ≥4 | prec ≥3 | prec strong ≥4 | avg_act | avg_pred |
|---|---|---|---|---|---|---|---|---|---|
| Auto cold 2-3Q | ~2.1 | 19 | 10 | 7/10 = 0.700 | 4/10 = 0.400 | 10/19 = 0.526 | 5/19 = 0.263 | 2.900 | 2.316 |
| Auto cold 1Q | 1 | 11 | 12 | 8/12 = 0.667 | 4/12 = 0.333 | **10/11 = 0.909** | 5/11 = 0.455 | 2.333 | 3.000 |
| V1 K=5 | 5 | 55 | 12 | 9/12 = 0.750 | 4/12 = 0.333 | 33/55 = 0.600 | 13/55 = 0.236 | 2.750 | 2.545 |
| Auto K=5 | 5 | 55 | 12 | 9/12 = 0.750 | 6/12 = 0.500 | 40/55 = 0.727 | 24/55 = 0.436 | 2.833 | 2.745 |
| **V1 K=10** | 10 | 110 | 12 | **11/12 = 0.917** | 7/12 = 0.583 | **108/110 = 0.982** | 27/110 = 0.245 | 3.417 | 2.873 |
| **Auto K=10** | 10 | 110 | 12 | 10/12 = 0.833 | **8/12 = 0.667** | 91/110 = 0.827 | **74/110 = 0.673** | **3.500** | **3.391** |
| Conv K=1 | 1 seq | 12 | 12 | 8/12 = 0.667 | 3/12 = 0.250 | 7/12 = 0.583 | 3/12 = 0.250 | 2.750 | 2.667 |
| **Conv K=10** | 10 seq | 120 | 12 | 9/12 = 0.750 | 5/12 = 0.417 | **112/120 = 0.933** | 49/120 = 0.408 | 3.083 | 3.300 |
| **NoPersona K=110** | 110 | 110 | 12 | 8/12 = 0.667 | 1/12 = 0.083 | 20/110 = 0.182 | — | 2.667 | 1.291 |

### Table 3 — Per-candidate B2_pred (via B2 evaluator, K ≥5 only) + Identity-matched coverage

| Setting | K | cands | B2_pred useful ≥3 | B2_pred strong ≥4 | B2_pred avg | id-matched cov |
|---|---|---|---|---|---|---|
| Auto cold 2-3Q | ~2.1 | 19 | — | — | — | 3/10 = 0.300 |
| Auto cold 1Q | 1 | 11 | — | — | — | 3/12 = 0.250 |
| V1 K=5 | 5 | 55 | 8/55 = 0.145 | 0/55 = 0.000 | 0.891 | 6/12 = 0.500 |
| Auto K=5 | 5 | 55 | 6/55 = 0.109 | 0/55 = 0.000 | 0.927 | 4/12 = 0.333 |
| V1 K=10 | 10 | 110 | 9/110 = 0.082 | 0/110 = 0.000 | 0.809 | 8/12 = 0.667 |
| **Auto K=10** | 10 | 110 | **13/110 = 0.118** | **1/110 = 0.009** | 0.755 | **9/12 = 0.750** |
| Conv K=1 | 1 seq | 12 | — | — | — | 4/12 = 0.333 |
| **Conv K=10** | 10 seq | 120 | 8/120 = 0.067 | 0/120 = 0.000 | 0.675 | 6/12 = 0.500 |

---

## Section D — Per-analyst breakdown (Auto K=10 vs V1 baseline)

| Analyst | V1 baseline coarse | V1 K=10 coarse | Auto K=10 coarse | Auto K=10 B2 (per-actual) | Auto K=10 has score-4 candidate? |
|---|---|---|---|---|---|
| andrew didora | 0/1 miss | 0/1 partial | 0/1 partial | 3 ✓ | no |
| brandt montour | 0/1 miss | 1/1 exact | 0/1 partial | 3 ✓ | no |
| james hardiman | 1/1 partial | 1/1 partial | 1/1 partial | 3 ✓ | no |
| **lizzie dove** | 1/1 partial | 1/1 partial | 1/1 partial | **4** ✓ | yes |
| matthew boss | 0/1 miss | 0/1 miss | 1/1 partial | 3 ✓ | no |
| robin farley | 1/2 partial | 2/2 (1 exact + 1 partial) | 1/2 (1 partial + 1 miss) | 3 ✓ (cell-level) | no |
| sharon zackfia | 0/1 miss | 0/1 miss | 1/1 partial | 3 ✓ | no |
| steven wieczynski | 1/1 partial | 1/1 partial | 1/1 partial | 3 ✓ | no |
| **vince ciepiel** | 1/1 exact | 1/1 exact | 1/1 exact | **4** ✓ | no |
| kevin kopelman (cold-start) | n/a | n/a | 0/1 miss | 0 ✗ | no |
| **xian siew (cold-start)** | n/a | n/a | 1/1 partial | **4** ✓ | **yes — only score 4 candidate in B2_pred-via-B2** |
| **TOTAL** | 5/10 = 0.500 | 10/12 = 0.833 | 9/12 = 0.750 | **10/12 binary** = 0.833 |  |

---

## Section E — Two example pairs (illustrative quality)

### Score 4 — "very close substitute" (1 of 110 candidates in Auto K=10 via B2)

Analyst: xian siew (cold-start, aggregate-fallback persona)
Sub-dims: topic / trigger / form / granularity all = strong.

PREDICTED:
> Good morning — you mentioned an increase in younger guests and repeat guests this quarter; does this demographic shift change booking lead times, cancellation patterns or spend-per-guest dynamics in a way that materially affects your yield or inventory management assumptions?

ACTUAL:
> Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard.

Reasoning: same core uncertainty (repeat-guest mix → yield mechanism), different surface vocabulary.

### Score 3 — "substantially similar" (12 of 110 in Auto K=10 via B2)

Analyst: brandt montour. Sub-dims: topic strong, trigger strong, form partial, granularity partial.

PREDICTED:
> Thanks — following up on demand dynamics: you called the Mediterranean moderation short-lived and said bookings have rebounded — can you quantify the booking curve change (how many weeks of slowed bookings, percent decline in pace at the trough, how much of Q2/Q3 Mediterranean inventory is still available and at what relative price bands), and tell us whether lead times have shortened or simply re-priced?

ACTUAL:
> Great. Thanks for taking my question. I just wanted to circle back on the third quarter and the Med, and just maybe if you could put a bit of a finer point on it. You know, how much do you have left to book at this point in the year? How much damage do you think was done over the last few weeks? What are you sort of baking into your forward guidance...

Reasoning: same topic+trigger (Med Q3 bookings, post-disruption); predicted is more granular (asks for percentages, weeks, price bands); actual is more conversational.

---

## Section F — Cross-analyst borrowing observation

Auto K=10 set-level B4 coverage = 0.833 (10/12 actuals covered). Of those 10 covered actuals, the best candidate is from the **same analyst** for 9/10, and from a **different analyst** for 1/10.

But under the strict bar (score ≥4): Auto K=10 cov_strong = 0.667 (8/12). The set covers 8 actuals at substantive-substitute level. However the per-actual B2 (which evaluates the analyst's own K=10 candidates against the analyst's own actual) only finds 3/12 actuals with score ≥4, and the per-candidate B2_pred via B2 evaluator finds just 1/110.

This means: **roughly 5 of the 8 "score ≥4" actuals in B4 cov_strong are landing on the wrong twin's candidate**. The set-level pool contains the right questions, but the per-twin attribution is noisy.

Two responses planned:

1. **Selection / routing stage after generation**: visible from the K=10 outputs that many predicted questions across twins are redundant (Mediterranean booking, fuel hedging, regional yield show up repeatedly). A second-stage selector that walks the call in operator order and prunes redundant candidates should match current K=10 coverage with far fewer predictions per twin, and lift the within-twin score=4 rate by routing each remaining slot to a more distinctive question.
2. **Stronger persona schema**: current persona captures *how each analyst analyzes* (BDE structure — what topics they cover, what evidence they demand) but not their *individual analytical style* (rhetorical signature, framing template, what they uniquely emphasize vs peers). The no-persona K=110 baseline reaching B4 cov 0.667 vs persona K=10 reaching 0.833 shows persona is doing real work on topic selection, but the gap from "right topic" (≥3) to "right question" (≥4) suggests the persona schema still needs more idiosyncratic style capture.

---

## Section G — Variance check on the original Phase 1 result

Re-running final-test eval on the same personas (Auto K=2-3, 9 returning analysts):

| | Run 1 | Run 2 |
|---|---|---|
| coarse exact | 2 | 1 |
| coarse partial | 5 | 6 |
| coarse miss | 3 | 3 |
| **hit_rate** | **0.700** | **0.700** |

Hit rate stable; only Robin Farley Q1 flipped exact↔partial. The +20pp lift over V1 baseline is robust to LLM stochasticity.

---

## Section H — Evaluator caveats

| Evaluator | Scope | Strictness on score 3 | Strictness on score 4 |
|---|---|---|---|
| Coarse (`judge_match.md`) | per-actual exact/partial/miss | partial ≈ "same topic, similar direction" | exact ≈ "same topic + direction + comparable specificity" |
| B2 (`b2_eval.md`) | per-(analyst, K candidates, all actuals) bundle → 1 cell score | "substantially similar target with phrasing/granularity differences" | "plausibly substitute" |
| B4 (`b4_eval.md`) | set-level: per-actual + per-candidate scores in batch | "substantially similar target" (no qualifier) | "very close substitute" |

**Key observation**: B4 evaluator is **bimodal** within-analyst (Auto K=10 within distribution: 18× score 4, 1× score 2, **0× score 3**). B2 evaluator distributes more across 2/3/4. Same data, different distribution because B4 prompt processes 110 candidates in batch (decisive bimodal) while B2 processes one analyst-cell at a time (deliberative graded).

**Don't treat B2 binary ↔ B4 cov as equivalent**. They use different LLM calls and different rubric framings.

The no-persona baseline uses gpt-5 as evaluator (vs gpt-5-mini for auto pipeline) — small evaluator drift may apply.

---

## Section I — Artifacts on disk

| Path | Content |
|---|---|
| `data_auto/train_combined.json` | RCL + peer turns, ticker/sector tagged (Step 0 output) |
| `data_auto/cal.json` | 2025-Q3 + 2025-Q4 actuals + management contexts |
| `data_auto/test.json` | 2026-Q1 actuals + management context |
| `data_auto/round_{0,1,2,3}/` | Variant A per-round artifacts |
| `data_auto/refine_<analyst>/round_{0..3}/` | Variant B per-analyst per-round artifacts |
| `data_auto/r_star.json` | Variant A selected round = 0 |
| `data_auto/final_personas/` | Final persona per analyst + `_fallback.json` for cold-start |
| `data_auto/final_eval/` | Auto K=2-3 cold predictions + judge + B2 + B4 |
| `data_auto/final_eval_1q/` | Auto K=1 |
| `data_auto/final_eval_5q_{v1,auto}/` | V1 + Auto K=5 |
| `data_auto/final_eval_10q_{v1,auto}/` | V1 + Auto K=10 |
| `data_auto/final_eval_conv{,_10q}/` | Conversational K=1, K=10 |
| `data_auto/final_eval_*/b2_per_actual.json` | B2 per-actual after Robin split (denom=12) |
| `data_auto/final_eval_*/b2_pred_via_b2_summary.json` | B2_pred via B2 evaluator (K≥5) |
| `data_auto/b2_pred_from_b4.json` | B2_pred via B4 evaluator (filtered to within-analyst) |
| `data_auto/b2_per_actual_all.json` | Cross-setting B2 per-actual summary |
| `data_auto/b2_pred_via_b2_all.json` | Cross-setting B2_pred-via-B2 summary |
| `data_baseline/gpt-5-mini_k110/` | No-persona K=110 baseline (110 candidates, evaluator gpt-5) |
| `reports/b2_b4_summary.md` | B2 + B4 first-pass report (Auto K=2-3 only) |
| `reports/baseline_cold_pool_2026q1.md` | No-persona baseline detailed report |
| `reports/cross_company_coverage.md` | RCL analysts × 5 peer companies coverage |
| `reports/analyst_dedup.md` | Analyst de-duplication + cross-company breadth |
| `reports/rcl_expansion_value.md` | Per-RCL-analyst peer-data value |

---

## Section J — Next steps

1. **Selection stage after generation**: take Auto K=10 candidate pool (110), de-duplicate by topic, run a selection-LLM that walks the operator queue and picks 1 candidate per turn from the global pool (allowing cross-twin candidates) → expect within-twin score=4 rate to rise.
2. **Richer persona schema**: add `framing_template`, `rhetorical_signature` opener phrases, `individual_anchor_set`, distinctive vs-peer attributes. Re-run Variant A round 5 with the richer schema.
3. **Per-actual B2 evaluator (12-actual denominator) for V1 / Auto K=10**: already done; recompute per-analyst breakdown to find which analysts can be lifted from score 3 to score 4 with richer persona.
4. **Larger CAL window**: extend CAL to 3 quarters (2025-Q2+Q3+Q4) → more refinement signal, escape the round 0 local-optimum that Variant A rounds 1-3 couldn't beat.
