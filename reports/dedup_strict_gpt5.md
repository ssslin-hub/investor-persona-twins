# Dedup under the reliable metric — chunked + strict + gpt-5 (drop & eval)

Per-round dedup with **gpt-5** for both the per-analyst drop decision and the chunked strict evaluation (1 run/round). Compared against the earlier chunked-**mini** dedup (`dedup_strict/`), whose coverage was inflated. Round 0 = un-deduped pool.


## v1 — `final_eval_14q_v1` (K=14)

- gpt-5 total dropped: 0/154; final kept: 154.

| round | m | pool | drops | **gpt-5 cov** | gpt-5 prec | (mini cov, old) |
|---|---|---|---|---|---|---|
| 0 | 14 | 154 | 0 | 0.833 | 0.435 | 0.806 |
| 1 | 14 | 154 | 0 | 0.750 | 0.390 | 0.861 |

**Takeaway (gpt-5):** pool 154→154 (+0), cov 0.833→0.750 (-0.083), prec 0.435→0.390 (-0.045). no candidates dropped — dedup is a no-op; the cov/prec change is single-run eval noise (same pool).


## v5 — `final_eval_20q_v5` (K=20)

- gpt-5 total dropped: 14/220; final kept: 200.

| round | m | pool | drops | **gpt-5 cov** | gpt-5 prec | (mini cov, old) |
|---|---|---|---|---|---|---|
| 0 | 20 | 214 | 0 | 0.750 | 0.313 | 0.889 |
| 1 | 20 | 200 | 14 | 0.833 | 0.315 | 0.861 |
| 2 | 10 | 200 | 0 | 0.750 | 0.360 | 0.833 |

**Takeaway (gpt-5):** pool 214→200 (-14), cov 0.750→0.750 (+0.000), prec 0.313→0.360 (+0.047). coverage held, precision improved — dedup helps.


## auto — `final_eval_20q_auto` (K=20)

- gpt-5 total dropped: 12/220; final kept: 206.

| round | m | pool | drops | **gpt-5 cov** | gpt-5 prec | (mini cov, old) |
|---|---|---|---|---|---|---|
| 0 | 20 | 218 | 0 | 0.833 | 0.339 | 0.917 |
| 1 | 20 | 206 | 12 | 0.917 | 0.383 | 0.861 |
| 2 | 10 | 206 | 0 | 0.833 | 0.325 | 0.861 |

**Takeaway (gpt-5):** pool 218→206 (-12), cov 0.833→0.833 (+0.000), prec 0.339→0.325 (-0.014). coverage held but precision did not improve — dedup ~neutral (within single-run noise).


## Note
- The old `dedup_strict/` coverage (mini) was inflated by chunk⊗mini leniency (see `FINAL_chunking_conjecture.md`); the gpt-5 column here is the trustworthy metric.
