# Strict B4 rubric — gpt-5-mini, all auto/v1/v5 settings

Evaluator: **gpt-5-mini** + `prompts/b4_eval_strict.md` (substitution-test rubric), single run per setting. Coverage/precision shown as `mean [min, max]` over seeds (n = number of seed reruns). B4-only, set-level.

Settings evaluated: 93 (parsed `strict_b4/b4.json` files).


## v1

| K | n | strict cov | strict prec |
|---|---|---|---|
| 5 | 5 | 0.667 [0.500, 0.833] | 0.611 [0.473, 0.691] |
| 10 | 5 | 0.683 [0.583, 0.833] | 0.603 [0.073, 0.836] |
| 12 | 1 | 0.667 | 0.583 |
| 14 | 5 | 0.733 [0.667, 0.917] | 0.188 [0.052, 0.578] |
| 16 | 5 | 0.673 [0.500, 0.750] | 0.313 [0.035, 0.727] |
| 18 | 5 | 0.700 [0.583, 0.833] | 0.043 [0.036, 0.052] |
| 20 | 5 | 0.667 [0.500, 0.833] | 0.140 [0.032, 0.552] |

## v5

| K | n | strict cov | strict prec |
|---|---|---|---|
| 5 | 5 | 0.517 [0.333, 0.667] | 0.567 [0.473, 0.673] |
| 10 | 5 | 0.583 [0.500, 0.667] | 0.524 [0.064, 0.700] |
| 12 | 1 | 0.583 | 0.618 |
| 14 | 5 | 0.644 [0.385, 0.917] | 0.490 [0.033, 0.909] |
| 16 | 5 | 0.667 [0.583, 0.833] | 0.587 [0.040, 0.818] |
| 18 | 5 | 0.617 [0.417, 0.750] | 0.179 [0.026, 0.746] |
| 20 | 5 | 0.700 [0.500, 0.833] | 0.056 [0.037, 0.117] |

## auto

| K | n | strict cov | strict prec |
|---|---|---|---|
| 5 | 5 | 0.583 [0.500, 0.667] | 0.447 [0.145, 0.673] |
| 10 | 5 | 0.623 [0.500, 0.750] | 0.494 [0.055, 0.809] |
| 12 | 1 | 0.667 | 0.061 |
| 14 | 5 | 0.617 [0.417, 0.833] | 0.395 [0.041, 0.675] |
| 16 | 5 | 0.580 [0.400, 0.667] | 0.181 [0.034, 0.733] |
| 18 | 5 | 0.646 [0.538, 0.750] | 0.295 [0.036, 0.758] |
| 20 | 5 | 0.667 [0.583, 0.750] | 0.147 [0.033, 0.583] |

## Per-setting detail

| source | K | seed | strict cov | strict prec |
|---|---|---|---|---|
| auto | 5 | s1 | 0.583 | 0.636 |
| auto | 5 | s2 | 0.500 | 0.673 |
| auto | 5 | s3 | 0.583 | 0.145 |
| auto | 5 | s4 | 0.583 | 0.291 |
| auto | 5 | s5 | 0.667 | 0.491 |
| auto | 10 | s1 | 0.667 | 0.382 |
| auto | 10 | s2 | 0.583 | 0.636 |
| auto | 10 | s3 | 0.500 | 0.055 |
| auto | 10 | s4 | 0.750 | 0.809 |
| auto | 10 | s5 | 0.615 | 0.590 |
| auto | 12 | s1 | 0.667 | 0.061 |
| auto | 14 | s1 | 0.667 | 0.078 |
| auto | 14 | s2 | 0.833 | 0.675 |
| auto | 14 | s3 | 0.500 | 0.041 |
| auto | 14 | s4 | 0.417 | 0.556 |
| auto | 14 | s5 | 0.667 | 0.623 |
| auto | 16 | s1 | 0.500 | 0.034 |
| auto | 16 | s2 | 0.667 | 0.046 |
| auto | 16 | s3 | 0.400 | 0.733 |
| auto | 16 | s4 | 0.667 | 0.047 |
| auto | 16 | s5 | 0.667 | 0.047 |
| auto | 18 | s1 | 0.692 | 0.758 |
| auto | 18 | s2 | 0.583 | 0.600 |
| auto | 18 | s3 | 0.538 | 0.036 |
| auto | 18 | s4 | 0.750 | 0.041 |
| auto | 18 | s5 | 0.667 | 0.041 |
| auto | 20 | s1 | 0.667 | 0.036 |
| auto | 20 | s2 | 0.750 | 0.041 |
| auto | 20 | s3 | 0.583 | 0.033 |
| auto | 20 | s4 | 0.583 | 0.583 |
| auto | 20 | s5 | 0.750 | 0.042 |
| v1 | 5 | s1 | 0.583 | 0.473 |
| v1 | 5 | s2 | 0.750 | 0.618 |
| v1 | 5 | s3 | 0.667 | 0.655 |
| v1 | 5 | s4 | 0.500 | 0.691 |
| v1 | 5 | s5 | 0.833 | 0.618 |
| v1 | 10 | s1 | 0.667 | 0.073 |
| v1 | 10 | s2 | 0.667 | 0.682 |
| v1 | 10 | s3 | 0.583 | 0.717 |
| v1 | 10 | s4 | 0.667 | 0.709 |
| v1 | 10 | s5 | 0.833 | 0.836 |
| v1 | 12 | s1 | 0.667 | 0.583 |
| v1 | 14 | rerun2 | 0.667 | 0.052 |
| v1 | 14 | rerun3 | 0.917 | 0.059 |
| v1 | 14 | rerun4 | 0.667 | 0.192 |
| v1 | 14 | rerun5 | 0.667 | 0.578 |
| v1 | 14 | s1 | 0.750 | 0.058 |
| v1 | 16 | s1 | 0.750 | 0.707 |
| v1 | 16 | s2 | 0.615 | 0.727 |
| v1 | 16 | s3 | 0.500 | 0.035 |
| v1 | 16 | s4 | 0.750 | 0.051 |
| v1 | 16 | s5 | 0.750 | 0.047 |
| v1 | 18 | s1 | 0.667 | 0.042 |
| v1 | 18 | s2 | 0.750 | 0.042 |
| v1 | 18 | s3 | 0.583 | 0.036 |
| v1 | 18 | s4 | 0.833 | 0.052 |
| v1 | 18 | s5 | 0.667 | 0.042 |
| v1 | 20 | s1 | 0.583 | 0.032 |
| v1 | 20 | s2 | 0.583 | 0.032 |
| v1 | 20 | s3 | 0.833 | 0.042 |
| v1 | 20 | s4 | 0.833 | 0.041 |
| v1 | 20 | s5 | 0.500 | 0.552 |
| v5 | 5 | s1 | 0.500 | 0.527 |
| v5 | 5 | s2 | 0.500 | 0.673 |
| v5 | 5 | s3 | 0.667 | 0.655 |
| v5 | 5 | s4 | 0.333 | 0.473 |
| v5 | 5 | s5 | 0.583 | 0.509 |
| v5 | 10 | s1 | 0.500 | 0.618 |
| v5 | 10 | s2 | 0.667 | 0.661 |
| v5 | 10 | s3 | 0.583 | 0.578 |
| v5 | 10 | s4 | 0.583 | 0.064 |
| v5 | 10 | s5 | 0.583 | 0.700 |
| v5 | 12 | s1 | 0.583 | 0.618 |
| v5 | 14 | s1 | 0.385 | 0.033 |
| v5 | 14 | s2 | 0.917 | 0.072 |
| v5 | 14 | s3 | 0.667 | 0.800 |
| v5 | 14 | s4 | 0.667 | 0.909 |
| v5 | 14 | s5 | 0.583 | 0.636 |
| v5 | 16 | s1 | 0.667 | 0.763 |
| v5 | 16 | s2 | 0.583 | 0.540 |
| v5 | 16 | s3 | 0.667 | 0.773 |
| v5 | 16 | s4 | 0.583 | 0.040 |
| v5 | 16 | s5 | 0.833 | 0.818 |
| v5 | 18 | s1 | 0.667 | 0.042 |
| v5 | 18 | s2 | 0.417 | 0.026 |
| v5 | 18 | s3 | 0.583 | 0.746 |
| v5 | 18 | s4 | 0.750 | 0.047 |
| v5 | 18 | s5 | 0.667 | 0.036 |
| v5 | 20 | s1 | 0.500 | 0.117 |
| v5 | 20 | s2 | 0.750 | 0.041 |
| v5 | 20 | s3 | 0.667 | 0.037 |
| v5 | 20 | s4 | 0.750 | 0.041 |
| v5 | 20 | s5 | 0.833 | 0.045 |

## Verification

- **Provenance:** batch `batch_6a1fc031cf8081908a9d9095b2c3d32f` (93/93 completed, 0 failed).
  Builder `src/batch_build_strict_b4.py`; parser `src/parse_strict_b4.py` → `<setting>/strict_b4/b4.json`;
  aggregator `src/report_strict_b4.py`. Evaluator model gpt-5-mini, single run, rubric `prompts/b4_eval_strict.md`.
- **Sanity check (passed):** v5 K=10 strict cov over 5 seeds = [0.500, 0.667, 0.583, 0.583, 0.583],
  mean 0.583 — matches the previously reported strict-mini number in `strict_rubric_v5k10_comparison.md`
  (mini strict cov 0.583, range [0.50, 0.67]).
- **Invariant (strict cov ≤ lenient cov):** holds for 82/85 settings that have both strict and lenient
  mini B4. The 3 exceptions (`14q_v5_s2` 0.917, `16q_v5_s5` 0.833, `20q_v5_s5` 0.833) exceed the lenient
  5-run max by exactly one covered actual on a 12-actual denominator — attributable to single-run
  mini-judge noise, not a rubric inversion. Comparing the strict single run against the lenient 5-run
  mean, 11/85 sit above the mean, all within the lenient run-to-run range except those 3.
- **Scope:** parallel auto/v1/v5 K-curve only (K∈{5,10,12,14,16,18,20}, seeds s1–s5 + v1-K14 reruns).
  K=12 has seed-1 only (n=1). seq/v6/conv settings excluded.
