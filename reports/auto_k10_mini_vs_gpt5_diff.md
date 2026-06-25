# Auto K=10 — mini vs gpt-5 evaluator score diff

Same 110 predicted candidates and same 12 actuals; only the evaluator model differs.
Per-candidate B2 evaluation re-run with gpt-5 on all 110 candidates; mini run dates from Phase 5.

## Section A — Aggregate per-candidate B2 diff (110 candidates)

- Total candidates: **110**
- Mean per-candidate score gap (mini − gpt-5): **-0.109** (gpt-5 scores are slightly higher on average per candidate)
- Binary flips at the score≥3 threshold:
  - mini=True → gpt-5=False: **7** (gpt-5 demoted)
  - mini=False → gpt-5=True: **0** (gpt-5 promoted)

### Gap distribution (mini − gpt-5)

| gap | count | % |
|---|---|---|
| -2 | 4 | 3.6% |
| -1 | 22 | 20.0% |
| +0 | 67 | 60.9% |
| +1 | 16 | 14.5% |
| +2 | 1 | 0.9% |

**Reading**: 60.9% of candidates get the same score under both evaluators. 20.0% are scored 1 point higher by mini, 14.5% are scored 1 point higher by gpt-5. Disagreements ≥2 points are rare (4.5% combined).

### Shift matrix (rows = mini score, cols = gpt-5 score)

| mini\gpt-5 | 0 | 1 | 2 | 3 | 4 | total |
|---|---|---|---|---|---|---|
| **0** | 44 | 16 | 4 | 0 | 0 | 64 |
| **1** | 6 | 11 | 6 | 0 | 0 | 23 |
| **2** | 0 | 3 | 7 | 0 | 0 | 10 |
| **3** | 0 | 1 | 6 | 5 | 0 | 12 |
| **4** | 0 | 0 | 0 | 1 | 0 | 1 |

**Key cells**:
- Diagonal stability (same score): 67/110 = 61%
- mini=3 → gpt-5=2: **6** candidates demoted across the binary boundary
- mini=0 → gpt-5≥1: **20** candidates gpt-5 considers nontrivial that mini wrote off as 0

## Section B — Per-analyst summary

| Analyst | n cand | mini hits (≥3) | gpt-5 hits (≥3) | mini avg | gpt-5 avg | avg gap |
|---|---|---|---|---|---|---|
| andrew didora | 10 | 0 | 0 | 0.40 | 0.40 | +0.00 |
| brandt montour | 10 | 1 | 1 | 0.60 | 0.70 | -0.10 |
| james hardiman | 10 | 1 | 0 | 0.30 | 0.50 | -0.20 |
| kevin kopelman | 10 | 0 | 0 | 0.10 | 0.60 | -0.50 |
| lizzie dove | 10 | 2 | 1 | 0.90 | 0.70 | +0.20 |
| matthew boss | 10 | 0 | 0 | 1.00 | 1.00 | +0.00 |
| robin farley | 10 | 1 | 1 | 0.90 | 1.50 | -0.60 |
| sharon zackfia | 10 | 0 | 0 | 0.70 | 0.70 | +0.00 |
| steven wieczynski | 10 | 2 | 0 | 0.90 | 1.10 | -0.20 |
| vince ciepiel | 10 | 2 | 1 | 1.00 | 1.10 | -0.10 |
| xian siew | 10 | 4 | 2 | 1.50 | 1.20 | +0.30 |

## Section C — B4 per-actual diff (12 actuals)

Coverage flips between evaluators:
| actual_id | mini_cov | gpt5_cov | mini_score | gpt5_score | mini_best_cand | gpt5_best_cand | same_cand? |
|---|---|---|---|---|---|---|---|
| andrew_didora-actual-0 | False | True | 2 | 4 | `steven_wieczynski-pred-3` | `steven_wieczynski-pred-3` | ✓ |
| brandt_montour-actual-0 | True | True | 4 | 4 | `brandt_montour-pred-1` | `brandt_montour-pred-1` | ✓ |
| james_hardiman-actual-0 | True | True | 4 | 4 | `james_hardiman-pred-5` | `steven_wieczynski-pred-0` | ✗ |
| kevin_kopelman-actual-0 | True | False | 3 | 2 | `steven_wieczynski-pred-5` | `robin_farley-pred-6` | ✗ |
| lizzie_dove-actual-0 | True | True | 4 | 3 | `lizzie_dove-pred-5` | `andrew_didora-pred-8` | ✗ |
| matthew_boss-actual-0 | True | True | 4 | 3 | `matthew_boss-pred-1` | `sharon_zackfia-pred-8` | ✗ |
| robin_farley-actual-0 | False | False | 2 | 1 | `robin_farley-pred-8` | `robin_farley-pred-8` | ✓ |
| robin_farley-actual-1 | True | True | 4 | 3 | `robin_farley-pred-6` | `kevin_kopelman-pred-9` | ✗ |
| sharon_zackfia-actual-0 | True | False | 4 | 2 | `sharon_zackfia-pred-0` | `andrew_didora-pred-5` | ✗ |
| steven_wieczynski-actual-0 | True | True | 3 | 4 | `steven_wieczynski-pred-0` | `kevin_kopelman-pred-1` | ✗ |
| vince_ciepiel-actual-0 | True | True | 4 | 4 | `vince_ciepiel-pred-0` | `lizzie_dove-pred-0` | ✗ |
| xian_siew-actual-0 | True | True | 4 | 3 | `xian_siew-pred-6` | `vince_ciepiel-pred-9` | ✗ |

## Section D — B4 per-candidate precision diff

- Candidates common to both eval runs: **110**
- mini called useful: 91; gpt-5 called useful: 72; both useful: 68
- Useful-flips: mini=useful → gpt-5=not: **23**; mini=not → gpt-5=useful: **4**
