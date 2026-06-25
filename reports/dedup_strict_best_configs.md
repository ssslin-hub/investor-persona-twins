# Strict iterative dedup ("deadout") — best config per source

Recursive-halving anchor dedup under the strict rubric (`prompts/b4_eval_strict.md`) for both the drop decision (gpt-5-mini ×3, majority ≥2/3) and the per-round evaluation (gpt-5-mini ×3, averaged). Round 0 = original pool (no drops). Coverage/precision are set-level over the 12-actual holdout.

Configs chosen = highest strict coverage per source: v1 K=14, v5 K=20, auto K=20.


## v1 — `final_eval_14q_v1` (K=14)

- Total dropped: 4 / 154; final pool kept: 150.

| round | m | pool size | drops this round | strict cov | strict prec |
|---|---|---|---|---|---|
| 0 | 14 | 154 | 0 | 0.806 [0.750, 0.833] | 0.530 [0.481, 0.558] |
| 1 | 14 | 150 | 4 | 0.861 [0.833, 0.917] | 0.542 [0.487, 0.607] |

**Takeaway:** pool 154→150 (-4), strict cov 0.806→0.861 (+0.056), strict prec 0.530→0.542 (+0.012). Coverage held while precision improved — dedup worked.


## v5 — `final_eval_20q_v5` (K=20)

- Total dropped: 22 / 220; final pool kept: 192.

| round | m | pool size | drops this round | strict cov | strict prec |
|---|---|---|---|---|---|
| 0 | 20 | 214 | 0 | 0.889 [0.833, 0.917] | 0.461 [0.393, 0.523] |
| 1 | 20 | 195 | 19 | 0.861 [0.833, 0.917] | 0.438 [0.354, 0.482] |
| 2 | 10 | 192 | 3 | 0.833 [0.833, 0.833] | 0.458 [0.370, 0.536] |

**Takeaway:** pool 214→192 (-22), strict cov 0.889→0.833 (-0.056), strict prec 0.461→0.458 (-0.003). Precision did not improve.


## auto — `final_eval_20q_auto` (K=20)

- Total dropped: 19 / 220; final pool kept: 199.

| round | m | pool size | drops this round | strict cov | strict prec |
|---|---|---|---|---|---|
| 0 | 20 | 218 | 0 | 0.917 [0.917, 0.917] | 0.446 [0.427, 0.459] |
| 1 | 20 | 201 | 17 | 0.861 [0.833, 0.917] | 0.566 [0.547, 0.577] |
| 2 | 10 | 199 | 2 | 0.861 [0.833, 0.917] | 0.513 [0.452, 0.558] |

**Takeaway:** pool 218→199 (-19), strict cov 0.917→0.861 (-0.056), strict prec 0.446→0.513 (+0.066). Coverage held while precision improved — dedup worked.

