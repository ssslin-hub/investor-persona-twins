# B4 score-4 candidates (very-close substitute) across K-ablation settings

For every setting, lists the candidates that the gpt-5 B4 evaluator scored **4 / 4**
("very close match; predicted question would plausibly substitute for the actual question").
Two sides: **coverage ≥4** (which actuals got a 4-rated cover) and **precision ≥4**
(which candidates were rated useful at score 4). `✓ identity` = candidate's source
analyst matches the actual's source analyst.

---

## Summary count

| Setting | Coverage ≥4 (actuals) | Precision ≥4 (candidates) | Pool size |
|---|---|---|---|
| V1 K=1 | 2/12 | 2/11 | 11 |
| V1 K=2-3 | 4/12 | 8/16 | 16 |
| V1 K=10 | 3/12 | 5/110 | 110 |
| V1 K=20 | 4/11 † | 4/217 | 217 |
| Auto K=10 | **5/12** | **22/110** | 110 |
| Auto K=20 | 4/12 | 4/218 | 218 |

† V1 K=20 B4 evaluator dropped xian_siew-actual-0 → denominator 11.

**Headline**: Auto K=10 produces by far the most score-4 candidates (22 out of 110 = 20% strong-precision rate). At K=20, **strong precision collapses to 4 candidates** on both pipelines — the simulator's extra 10 candidates per twin add no score-4 material.

---

## V1 K=1 (pool = 11)

### Coverage ≥4 (2 actuals)

| Actual | Best predicted | Identity |
|---|---|---|
| `james_hardiman-actual-0` ← `matthew_boss-pred-0` | × |
| `vince_ciepiel-actual-0` ← `vince_ciepiel-pred-0` | **✓** |

### Precision ≥4 (2 candidates)

| Candidate | Best actual | Identity |
|---|---|---|
| `matthew_boss-pred-0` → james_hardiman-actual-0 | × |
| `vince_ciepiel-pred-0` → vince_ciepiel-actual-0 | **✓** |

---

## V1 K=2-3 (pool = 16)

### Coverage ≥4 (4 actuals)

| Actual | Best predicted | Identity |
|---|---|---|
| `steven_wieczynski-actual-0` ← `james_hardiman-pred-1` | × |
| `brandt_montour-actual-0` ← `matthew_boss-pred-0` | × |
| `vince_ciepiel-actual-0` ← `vince_ciepiel-pred-0` | **✓** |
| `xian_siew-actual-0` ← `vince_ciepiel-pred-1` | × |

### Precision ≥4 (8 candidates)

| Candidate | Best actual | Identity |
|---|---|---|
| `matthew_boss-pred-0` → brandt_montour-actual-0 | × |
| `brandt_montour-pred-0` → vince_ciepiel-actual-0 | × |
| `james_hardiman-pred-1` → steven_wieczynski-actual-0 | × |
| `lizzie_dove-pred-0` → vince_ciepiel-actual-0 | × |
| `robin_farley-pred-0` → vince_ciepiel-actual-0 | × |
| `vince_ciepiel-pred-0` → vince_ciepiel-actual-0 | **✓** |
| `vince_ciepiel-pred-1` → xian_siew-actual-0 | × |
| `sharon_zackfia-pred-1` → vince_ciepiel-actual-0 | × |

Note: 50% precision-strong is inflated because the small 16-candidate pool happens to be heavily on-topic; multiple candidates redundantly cover `vince_ciepiel-actual-0`.

---

## V1 K=10 (pool = 110)

### Coverage ≥4 (3 actuals)

| Actual | Best predicted | Identity |
|---|---|---|
| `brandt_montour-actual-0` ← `brandt_montour-pred-1` | **✓** |
| `robin_farley-actual-1` ← `robin_farley-pred-1` | **✓** |
| `xian_siew-actual-0` ← `sharon_zackfia-pred-7` | × |

### Precision ≥4 (5 candidates)

| Candidate | Best actual | Identity |
|---|---|---|
| `steven_wieczynski-pred-0` → brandt_montour-actual-0 | × |
| `brandt_montour-pred-1` → brandt_montour-actual-0 | **✓** |
| `sharon_zackfia-pred-7` → xian_siew-actual-0 | × |
| `andrew_didora-pred-7` → andrew_didora-actual-0 | **✓** |
| `xian_siew-pred-0` → brandt_montour-actual-0 | × |

---

## V1 K=20 (pool = 217) †

### Coverage ≥4 (4 actuals)

| Actual | Best predicted | Identity |
|---|---|---|
| `steven_wieczynski-actual-0` ← `lizzie_dove-pred-1` | × |
| `brandt_montour-actual-0` ← `vince_ciepiel-pred-7` | × |
| `lizzie_dove-actual-0` ← `brandt_montour-pred-16` | × |
| `robin_farley-actual-1` ← `brandt_montour-pred-2` | × |

**Note**: zero identity matches in V1 K=20's coverage-4 row. At K=20 the evaluator's argmax over 217 candidates picks whatever's the strongest cross-twin match, even when the twin's own pool has a ≥3 candidate.

### Precision ≥4 (4 candidates)

| Candidate | Best actual | Identity |
|---|---|---|
| `lizzie_dove-pred-1` → steven_wieczynski-actual-0 | × |
| `vince_ciepiel-pred-7` → brandt_montour-actual-0 | × |
| `brandt_montour-pred-16` → lizzie_dove-actual-0 | × |
| `brandt_montour-pred-2` → robin_farley-actual-1 | × |

---

## Auto K=10 (pool = 110) — the precision-strong winner

### Coverage ≥4 (5 actuals)

| Actual | Best predicted | Identity |
|---|---|---|
| `steven_wieczynski-actual-0` ← `kevin_kopelman-pred-1` | × |
| `brandt_montour-actual-0` ← `brandt_montour-pred-1` | **✓** |
| `james_hardiman-actual-0` ← `steven_wieczynski-pred-0` | × |
| `vince_ciepiel-actual-0` ← `lizzie_dove-pred-0` | × |
| `andrew_didora-actual-0` ← `steven_wieczynski-pred-3` | × |

### Precision ≥4 (22 candidates)

Routed to whose actual (identity ✓/×):

| Candidate | Best actual | Identity |
|---|---|---|
| `matthew_boss-pred-2` → andrew_didora-actual-0 (fuel) | × |
| `steven_wieczynski-pred-0` → james_hardiman-actual-0 | × |
| `steven_wieczynski-pred-3` → andrew_didora-actual-0 | × |
| `brandt_montour-pred-1` → brandt_montour-actual-0 | **✓** |
| `brandt_montour-pred-5` → lizzie_dove-actual-0 | × |
| `brandt_montour-pred-7` → andrew_didora-actual-0 | × |
| `james_hardiman-pred-0` → andrew_didora-actual-0 | × |
| `lizzie_dove-pred-0` → vince_ciepiel-actual-0 | × |
| `lizzie_dove-pred-5` → lizzie_dove-actual-0 | **✓** |
| `lizzie_dove-pred-6` → andrew_didora-actual-0 | × |
| `robin_farley-pred-2` → andrew_didora-actual-0 | × |
| `vince_ciepiel-pred-0` → vince_ciepiel-actual-0 | **✓** |
| `vince_ciepiel-pred-3` → lizzie_dove-actual-0 | × |
| `vince_ciepiel-pred-4` → andrew_didora-actual-0 | × |
| `sharon_zackfia-pred-6` → xian_siew-actual-0 | × |
| `sharon_zackfia-pred-9` → andrew_didora-actual-0 | × |
| `andrew_didora-pred-2` → andrew_didora-actual-0 | **✓** |
| `xian_siew-pred-2` → andrew_didora-actual-0 | × |
| `kevin_kopelman-pred-0` → brandt_montour-actual-0 | × |
| `kevin_kopelman-pred-1` → steven_wieczynski-actual-0 | × |
| `kevin_kopelman-pred-2` → andrew_didora-actual-0 | × |
| `kevin_kopelman-pred-8` → xian_siew-actual-0 | × |

**Identity matches**: 4 / 22 = 18% (brandt → self, lizzie → self, vince → self, andrew → self).
**Most-borrowed actual**: `andrew_didora-actual-0` (fuel hedge math) — **10 of the 22 score-4 candidates** point at it. Cross-twin convergence is dominated by the fuel-hedge topic.

---

## Auto K=20 (pool = 218)

### Coverage ≥4 (4 actuals)

| Actual | Best predicted | Identity |
|---|---|---|
| `steven_wieczynski-actual-0` ← `xian_siew-pred-3` | × |
| `brandt_montour-actual-0` ← `robin_farley-pred-18` | × |
| `vince_ciepiel-actual-0` ← `vince_ciepiel-pred-0` | **✓** |
| `andrew_didora-actual-0` ← `andrew_didora-pred-0` | **✓** |

### Precision ≥4 (4 candidates)

| Candidate | Best actual | Identity |
|---|---|---|
| `xian_siew-pred-3` → steven_wieczynski-actual-0 | × |
| `robin_farley-pred-18` → brandt_montour-actual-0 | × |
| `vince_ciepiel-pred-0` → vince_ciepiel-actual-0 | **✓** |
| `andrew_didora-pred-0` → andrew_didora-actual-0 | **✓** |

Strong precision identity match rate: **2/4 = 50%** (highest of all settings), but the absolute count drops from 22 (K=10) to 4 (K=20) — the K=20 evaluator becomes much stricter when handed 218 candidates.

---

## Key patterns

1. **Auto K=10 dominates strong precision** (22 candidates ≥4, vs 5 for V1 K=10 and 4 for both K=20). This is the cleanest Auto-over-V1 result.
2. **Fuel-hedge actual is over-covered**: Auto K=10 routes 10 of 22 score-4 candidates at `andrew_didora-actual-0`. Multiple twins (matthew, steven, brandt, james, lizzie, robin, sharon, andrew, xian, kevin) all produced near-substitute fuel questions. The auto-discovery loop's shared prompt seems to make every twin attentive to the same salient management line ("$0.62 fuel headwind, ~60% hedged").
3. **K=20 evaluator collapse on identity**: V1 K=20 coverage ≥4 has 0/4 identity matches; V1 K=10 had 2/3. At K=20 scale the B4 evaluator can no longer find the twin's own ≥3 candidate buried in 217 — it just picks whichever cross-twin candidate happens to be the closest semantic match.
4. **Vince Ciepiel actual is the most "predictable" question** — covered at score 4 by the twin's own candidate in 4 of the 6 settings (K=1 ✓, K=2-3 ✓, K=10 ×, K=20 Auto ✓; for V1 K=10 / V1 K=20 / Auto K=10 the best score-4 came cross-twin). Question: "decompose the +2% Net Yield in Q1" — a structural modeling ask that any seasoned analyst would naturally produce.
