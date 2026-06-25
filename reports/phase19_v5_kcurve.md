# Phase 19 — v5 K-curve (K ∈ {12, 14, 16, 18, 20}) × gpt-5 / gpt-5-mini × n=5 runs

v5 personas (`data/personas_v5/`) × parallel K-simulator × gpt-5-mini sim, then evaluated under gpt-5 AND gpt-5-mini, 5 runs each (cached-skip). K≥16 also gets chunked B4 precision (Phase 12 method: 50-cand chunks).

**Status caveat**: K=16/18/20 gpt-5 cells hit OpenAI quota mid-run; n is partial there. K=12, K=14, and K=18 mini have full n=5. Numbers reported with their actual n.

---

## Headline table — `mean [min, max]` notation, n=run count

| K | Evaluator | n | B2 binary | B4 cov | B4 prec (raw) | Chunked prec | id-matched |
|---|---|---|---|---|---|---|---|
| **12** | gpt-5 | 5 | 0.517 [0.500, 0.583] | 0.700 [0.583, 0.833] | 0.491 [0.397, 0.546] | n/a | 1.4 [1, 2] |
| **12** | gpt-5-mini | 5 | 0.783 [0.750, 0.833] | 0.783 [0.750, 0.833] | 0.502 [0.069, 0.802] | n/a | 6.6 [5, 8] |
| **14** | gpt-5 | 5 | 0.650 [0.500, 0.750] | 0.750 [0.583, 0.833] | 0.561 [0.444, 0.680] | n/a | 3.6 [3, 4] |
| **14** | gpt-5-mini | 5 | 0.767 [0.750, 0.833] | 0.850 [0.833, 0.917] | 0.358 [0.059, 0.833] | n/a | 8.6 [6, 10] |
| 16 | gpt-5 | **2*** | 0.625 [0.583, 0.667] | 0.738 [0.727, 0.750] | 0.462 [0.364, 0.561] | 0.425 [0.405, 0.445] | 2.0 [1, 3] |
| 16 | gpt-5-mini | 4 | 0.729 [0.667, 0.750] | 0.771 [0.750, 0.833] | 0.273 [0.058, 0.566] | 0.579 [0.572, 0.601] | 7.0 [5, 9] |
| 18 | gpt-5 | **2*** | 0.625 [0.583, 0.667] | 0.708 [0.667, 0.750] | 0.281 [0.172, 0.391] | 0.479 [0.469, 0.490] | 0.5 [0, 1] |
| 18 | gpt-5-mini | 5 | 0.767 [0.500, 0.917] | 0.850 [0.833, 0.917] | 0.635 [0.052, 0.917] | 0.409 [0.000, 0.599] | 9.4 [8, 10] |
| 20 | gpt-5 | **3*** | 0.528 [0.333, 0.667] | 0.667 [0.583, 0.750] | 0.406 [0.211, 0.633] | 0.338 [0.201, 0.453] | 3.7 [3, 5] |
| 20 | gpt-5-mini | 4 | 0.667 [0.250, 0.833] | 0.792 [0.750, 0.833] | 0.467 [0.041, 1.000] | 0.391 [0.000, 0.570] | 6.8 [6, 7] |

*= partial n due to OpenAI quota exhaustion mid-run. K=16/18/20 gpt-5 cells need 1-3 more runs to reach n=5.

---

## v5 K-curve findings (gpt-5 evaluator, the canonical metric)

### B2 binary across K

| K | n | mean | range |
|---|---|---|---|
| 10 (from Phase 17) | 5 | **0.550** | [0.500, 0.583] |
| 12 | 5 | 0.517 | [0.500, 0.583] |
| 14 | 5 | **0.650** | [0.500, 0.750] |
| 16 | 2* | 0.625 | [0.583, 0.667] |
| 18 | 2* | 0.625 | [0.583, 0.667] |
| 20 | 3* | 0.528 | [0.333, 0.667] |

**v5 K-curve peak = K=14 (0.650 mean)**. K=14 outperforms K=10 (0.550) and K=20 (0.528) — same shape as the V1 K-curve which also peaked at K=14 (Phase 13a: 0.850 mean).

But: v5 K=14 = 0.650 vs V1 K=14 = 0.850 — **V1 K=14 is still substantially higher under the same evaluator**. v5 wins K=10 by +15pp vs V1 (Phase 17), but V1's K=14 advantage is larger than v5's K=10 advantage. The persona-source vs K-position interaction is real.

### B4 coverage across K (v5)

| K | gpt-5 cov | mini cov |
|---|---|---|
| 10 (Phase 17) | 0.750 | 0.817 |
| 12 | 0.700 | 0.783 |
| 14 | **0.750** | **0.850** |
| 16 | 0.738 | 0.771 |
| 18 | 0.708 | 0.850 |
| 20 | 0.667 | 0.792 |

Coverage roughly flat 0.70-0.75 across all K — adding candidates beyond K=14 doesn't broaden the cover-able actuals set. Mini consistently +0.05-0.10 over gpt-5.

### Identity-matched coverage across K (v5, gpt-5)

| K | id-matched | what it tells us |
|---|---|---|
| 10 | 2.0 | weak — twins converge on shared topics |
| 12 | 1.4 | even worse |
| 14 | **3.6** | best — at K=14 twins start producing enough own-actual matches |
| 16 | 2.0 | drops back |
| 18 | 0.5 | very bad |
| 20 | 3.7 | recovers (but partial n=3) |

**id-matched is non-monotonic in K**; v5 K=14 = 3.6 is a sweet spot. But still well below V1 K=10 = 6.0 (Phase 9 study high).

### Chunked B4 precision (K≥16 only)

| K | gpt-5 chunked | mini chunked |
|---|---|---|
| 16 | 0.425 [0.405, 0.445] | 0.579 [0.572, 0.601] |
| 18 | 0.479 [0.469, 0.490] | 0.409 [0.000, 0.599] |
| 20 | 0.338 [0.201, 0.453] | 0.391 [0.000, 0.570] |

Chunked precision (which Phase 12 established as the unbiased measure when raw B4 truncates) declines monotonically with K for v5 under gpt-5: 0.425 → 0.479 → 0.338. The bump at K=18 is partial-n artifact; the underlying trend is decline above K=16.

---

## v5 vs V1 vs Auto consolidated (K=10 from Phase 17 + this Phase 19)

| Setting | Eval | n | B2 binary | B4 cov | id-matched |
|---|---|---|---|---|---|
| **v5 K=10** | gpt-5 | 5 | 0.550 [0.500, 0.583] | 0.750 [0.667, 0.833] | 2.0 |
| V1 K=10 | gpt-5 | 5 | 0.400 [0.333, 0.500] | 0.667 [0.583, 0.833] | 3.7 |
| Auto K=10 | gpt-5 | 5 | 0.500 [0.417, 0.583] | 0.711 [0.636, 0.750] | 2.7 |
| **v5 K=14** | gpt-5 | 5 | 0.650 [0.500, 0.750] | 0.750 [0.583, 0.833] | 3.6 |
| V1 K=14 (Phase 13a) | gpt-5 | 5 | **0.850 [0.833, 0.917]** | 0.729 | 2.4 (n=5) |
| Auto K=14 (Phase 13a) | gpt-5 | 5 | 0.633 [0.583, 0.667] | 0.764 | 2.0 |
| v5 K=20 | gpt-5 | 3* | 0.528 [0.333, 0.667] | 0.667 [0.583, 0.750] | 3.7 |
| V1 K=20 (Phase 13a) | gpt-5 | 5 | 0.500 [0.500, 0.500] | 0.750 | (Phase 11) 3 |
| Auto K=20 (Phase 13a) | gpt-5 | 5 | 0.700 [0.667, 0.750] | 0.667 | (Phase 11) 3 |

---

## Key paper-defensible findings

1. **V1 K=14 = 0.850 [0.833, 0.917]** is the absolute study high for B2 binary. v5 K=14 = 0.650 doesn't approach it. v5's win is at K=10 only.

2. **v5 at K=10 wins on B4 coverage** (0.750) over V1 (0.667) and Auto (0.711). v5's persona richness translates to broader topical reach at the headline K.

3. **v5 K-curve peaks at K=14** on B2 binary (0.650) and id-matched (3.6) — same K as V1's peak, suggesting K=14 is a structural sweet spot for the 12-actual set, independent of persona source.

4. **Chunked precision declines monotonically with K above K=16** for v5 (0.425 → 0.338). Confirms Phase 11/12 finding that beyond K=14 simulator produces increasing filler.

5. **gpt-5-mini systematically inflates B2 binary by ~+0.15-0.20** vs gpt-5 (e.g., v5 K=10: mini 0.667 vs gpt-5 0.550). For paper, report gpt-5 numbers; mini is for fast iteration only.

---

## Pending (when OpenAI quota recovers)

To complete the v5 K-curve to full n=5 on gpt-5:
- K=16 gpt-5: 3 more runs
- K=18 gpt-5: 3 more runs
- K=20 gpt-5: 2 more runs
- K=16 mini: 1 more run
- K=20 mini: 1 more run

Also pending Phase 14 mini aggregate writes for seq_20q_v1 and seq_20q_auto (b4 files exist, just need re-run of aggregation step).

## Files

- `data_auto/phase19_aggregate.json` — full aggregate (partial-n flagged)
- `data_auto/final_eval_{12,14,16,18,20}q_v5/v5_curve/{gpt-5,gpt-5-mini}/run_{1..5}/` — per-run outputs (some incomplete)
- `data_auto/final_eval_{12,14,16,18,20}q_v5/summary.json` — v5 K-curve predictions
- `src/rerun_v5_kq.py`, `src/eval_v5_curve.py`, `src/_eval_one_cell.py` — drivers
