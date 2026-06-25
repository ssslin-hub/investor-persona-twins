# B2 + B4 metrics on the auto-discovery pipeline (TEST = 2026-Q1)

## Headline

- Coarse hit rate (this pipeline): **0.700** (1 exact + 6 partial / 10)  _(reference: V1 baseline 0.500)_
- **B2 binary_match_rate** (per-analyst, score ≥ 3): **0.333** (3 / 9); avg match_score_0_to_4 = **1.778**
- **B4 coverage_rate** (set-level, score ≥ 3): **0.700** (7 / 10); **precision_rate** = **0.526** (10 / 19); avg_actual_best_score = **2.900**, avg_predicted_best_score = **2.316**

## Reference: investorPersona_2 (Node pipeline, different roster)

These numbers are from the published Node-pipeline outputs and are **not apples-to-apples** with the auto-pipeline here:
- Node B2 evaluator ran on 11 analysts (incl. 2 cold-start); auto here runs on 9 returning.
- Node B4 evaluator ran on 12 actual questions; auto here runs on 10 (cold-start excluded).

- Node B2: binary_match_rate = 0.273 (3 / 11); avg score = 1.455
- Node B4: coverage_rate = 0.667 (8 / 12); precision_rate = 0.667 (8 / 12); avg_actual_best = 2.917; avg_pred_best = 2.500

## B2 per-analyst breakdown (auto-pipeline)

| analyst | score 0-4 | binary | topic | trigger | form | granularity |
|---|---|---|---|---|---|---|
| matthew boss | 2 | · | partial | weak | weak | weak |
| steven wieczynski | 3 | ✓ | strong | strong | partial | partial |
| brandt montour | 2 | · | partial | weak | partial | weak |
| james hardiman | 0 | · | none | none | none | none |
| lizzie dove | 2 | · | partial | weak | weak | weak |
| robin farley | 3 | ✓ | strong | partial | partial | partial |
| vince ciepiel | 4 | ✓ | strong | strong | strong | strong |
| sharon zackfia | 0 | · | none | none | none | none |
| andrew didora | 0 | · | none | none | none | none |

## B4 actual-coverage breakdown (auto-pipeline)

| actual_id (analyst-idx) | covered | best predicted | score |
|---|---|---|---|
| matthew_boss-actual-0 | ✓ | lizzie_dove-pred-0 | 3 |
| steven_wieczynski-actual-0 | ✓ | steven_wieczynski-pred-0 | 4 |
| brandt_montour-actual-0 | ✓ | brandt_montour-pred-0 | 4 |
| james_hardiman-actual-0 | ✓ | andrew_didora-pred-0 | 4 |
| lizzie_dove-actual-0 | ✓ | james_hardiman-pred-1 | 3 |
| robin_farley-actual-0 | · | lizzie_dove-pred-0 | 1 |
| robin_farley-actual-1 | ✓ | steven_wieczynski-pred-1 | 3 |
| vince_ciepiel-actual-0 | ✓ | vince_ciepiel-pred-0 | 4 |
| sharon_zackfia-actual-0 | · | lizzie_dove-pred-1 | 2 |
| andrew_didora-actual-0 | · | lizzie_dove-pred-1 | 1 |

## B4 predicted-precision breakdown

| candidate_id | useful | best actual | score |
|---|---|---|---|
| matthew_boss-pred-0 | ✓ | brandt_montour-actual-0 | 3 |
| matthew_boss-pred-1 | · | None | 0 |
| steven_wieczynski-pred-0 | ✓ | steven_wieczynski-actual-0 | 4 |
| steven_wieczynski-pred-1 | · | robin_farley-actual-1 | 2 |
| steven_wieczynski-pred-2 | · | None | 0 |
| brandt_montour-pred-0 | ✓ | brandt_montour-actual-0 | 4 |
| brandt_montour-pred-1 | · | brandt_montour-actual-0 | 2 |
| james_hardiman-pred-0 | ✓ | james_hardiman-actual-0 | 3 |
| james_hardiman-pred-1 | · | lizzie_dove-actual-0 | 2 |
| lizzie_dove-pred-0 | ✓ | vince_ciepiel-actual-0 | 4 |
| lizzie_dove-pred-1 | · | sharon_zackfia-actual-0 | 2 |
| robin_farley-pred-0 | ✓ | robin_farley-actual-1 | 3 |
| robin_farley-pred-1 | · | robin_farley-actual-1 | 1 |
| vince_ciepiel-pred-0 | ✓ | vince_ciepiel-actual-0 | 4 |
| vince_ciepiel-pred-1 | ✓ | brandt_montour-actual-0 | 3 |
| sharon_zackfia-pred-0 | · | None | 0 |
| sharon_zackfia-pred-1 | ✓ | james_hardiman-actual-0 | 3 |
| andrew_didora-pred-0 | ✓ | brandt_montour-actual-0 | 4 |
| andrew_didora-pred-1 | · | None | 0 |

### Missed actual themes

- Construction/resumption status for Perfect Day Mexico (environmental pause) — factual operational update
- Fuel/hedging and whether itinerary changes or initiative deferrals are being made due to higher fuel
- At what capacity growth threshold would unit costs ex‑fuel re‑accelerate (inflation sensitivity)

### Overpredicted themes

- Highly granular pre‑booking penetration splits by age cohort and channel (app vs web)
- Explicit EPS cents-per-100bps bridge requests and exact cents-per-100bps pass-through calculations
- Detailed debt‑maturity refinancing mechanics and prepayment restriction queries
- Very granular onboard revenue reporting details (gross vs net allocations, AUR differentials) and AI/UX ROI metrics
- Specific buyback/share‑count/dilution assumptions embedded in guidance (not asked by actuals)

### Set-level summary (evaluator)

The predicted set covers the core actual themes around Mediterranean and West Coast Mexico booking disruption, booking‑curve visibility, and contributions from new hardware/Perfect Day to yield — 7 of 10 actual questions (70%) are covered with substantially similar predicted items. Predictions were strongest on regionally granular yield/booking questions and decomposition of new product contributions. Misses include operational/factual items (construction status), fuel/hedging and itinerary change questions, and macro sensitivity on unit‑cost thresholds. Precision is moderate: 10 of 19 predicted questions (≈52.6%) were deemed useful (score ≥3). To improve, include a few operational/fact‑check questions (construction/timing), explicit fuel/hedge questions, and avoid over‑allocating to very granular cohort/channel breakdowns that were not present in the holdouts.
