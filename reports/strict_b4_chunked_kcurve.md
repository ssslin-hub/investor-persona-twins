# Chunked strict B4 coverage — K-curve (seed-1, gpt-5-mini vs gpt-5)

Strict rubric (`prompts/b4_eval_strict.md`). **single mini** = one B4 call over the full pool (existing `strict_b4/b4.json`). **chunked** = pool split into ≤50-candidate chunks, max match-score per actual across chunks (covered if ≥3). One run per config.

All coverage = set-level over 12 actuals.


## v1

| K | single mini cov | chunked mini cov | chunked gpt-5 cov | | chunked mini prec | chunked gpt-5 prec |
|---|---|---|---|---|---|---|
| 5 | 0.583 | 0.583 | 0.750 | gpt5 vs single +0.167 | 0.527 | 0.509 |
| 10 | 0.667 | 0.833 | 0.667 | gpt5 vs single +0.000 | 0.618 | 0.427 |
| 12 | 0.667 | 0.750 | 0.750 | gpt5 vs single +0.083 | 0.508 | 0.348 |
| 14 | 0.750 | 0.750 | 0.833 | gpt5 vs single +0.083 | 0.487 | 0.474 |
| 16 | 0.750 | 0.846 | 0.750 | gpt5 vs single +0.000 | 0.500 | 0.314 |
| 18 | 0.667 | 0.917 | 0.833 | gpt5 vs single +0.167 | 0.532 | 0.372 |
| 20 | 0.583 | 0.833 | 0.750 | gpt5 vs single +0.167 | 0.415 | 0.258 |


## v5

| K | single mini cov | chunked mini cov | chunked gpt-5 cov | | chunked mini prec | chunked gpt-5 prec |
|---|---|---|---|---|---|---|
| 5 | 0.500 | 0.667 | 0.417 | gpt5 vs single -0.083 | 0.709 | 0.491 |
| 10 | 0.500 | 0.750 | 0.750 | gpt5 vs single +0.250 | 0.509 | 0.427 |
| 12 | 0.583 | 0.917 | 0.667 | gpt5 vs single +0.083 | 0.557 | 0.389 |
| 14 | 0.385 | 0.833 | 0.833 | gpt5 vs single +0.449 | 0.569 | 0.444 |
| 16 | 0.667 | 0.750 | 0.833 | gpt5 vs single +0.167 | 0.428 | 0.335 |
| 18 | 0.667 | 0.833 | 0.833 | gpt5 vs single +0.167 | 0.464 | 0.370 |
| 20 | 0.500 | 0.833 | 0.667 | gpt5 vs single +0.167 | 0.472 | 0.294 |


## auto

| K | single mini cov | chunked mini cov | chunked gpt-5 cov | | chunked mini prec | chunked gpt-5 prec |
|---|---|---|---|---|---|---|
| 5 | 0.583 | 0.750 | 0.500 | gpt5 vs single -0.083 | 0.618 | 0.436 |
| 10 | 0.667 | 0.833 | 0.750 | gpt5 vs single +0.083 | 0.673 | 0.555 |
| 12 | 0.667 | 0.833 | 0.667 | gpt5 vs single +0.000 | 0.538 | 0.371 |
| 14 | 0.667 | 0.917 | 0.833 | gpt5 vs single +0.167 | 0.444 | 0.405 |
| 16 | 0.500 | 0.833 | 0.667 | gpt5 vs single +0.167 | 0.468 | 0.306 |
| 18 | 0.692 | 1.000 | 0.583 | gpt5 vs single -0.109 | 0.454 | 0.314 |
| 20 | 0.667 | 1.000 | 0.833 | gpt5 vs single +0.167 | 0.535 | 0.294 |


## Reading

- **chunked mini > single mini** quantifies the chunking measurement lift (with mini's leniency baked in — upper bound).
- **chunked gpt-5** is the trustworthy number: chunk-retrieval + a reliable judge.
- **chunked gpt-5 vs single mini** (Δ column) = the honest 'does chunking improve coverage' answer; expected positive and widening with K (more candidates the single call is blind to).
- **chunked gpt-5 < chunked mini** = how much of the mini chunked number was inflation.

