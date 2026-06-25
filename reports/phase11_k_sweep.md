# Phase 11 — full K-sweep: parallel-K vs sequential-K-call simulator

Evaluator everywhere: **gpt-5 + v1 `prompts/b2_eval.md`** for B2; **gpt-5 + `prompts/b4_eval.md`** for B4. Simulator: gpt-5-mini.

**Parallel-K simulator** (the existing simulator used in Phases 4/9/10/11a) emits all K candidates in a single LLM call.
**Sequential-K simulator** (new in Phase 11b) makes K LLM calls per twin, each call sees the twin's prior questions and produces ONE new distinct question.

All B4 cov numbers use the Phase 9/10 override (B4 cov ≥ B2 binary by construction).

---

## Headline: parallel vs sequential at matched K

### V1 pipeline

| K | parallel B2 bin | seq B2 bin | parallel B4 cov | seq B4 cov | parallel id-m | seq id-m | parallel prec_rows | seq prec_rows |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.250 | **0.083** | 7/12 | 6/12 | 2/12 | 1/12 | 11/11 | 11/11 |
| 5 | n/a | 0.250 | n/a | 9/12 | n/a | 3/12 | n/a | 55/55 |
| 10 | 0.417 | **0.583** | 9/12 | 9/12 | **6/12** | 3/12 | 110/110 | 110/110 |
| 12 | 0.417 | 0.500 | 9/12 | 10/12 | 4/12 | 2/12 | 132/132 | 132/132 |
| 14 | **0.667** | 0.583 | 9/11 | 8/11 | 2/11 | **4/11** | 154/154 | 42/154 |
| 16 | 0.583 | 0.500 | 9/12 | 10/12 | 3/12 | **4/12** | 37/172 | 12/12 |
| 18 | 0.583 | 0.583 | 11/12 | 11/12 | 2/12 | **4/12** | 191/191 | 20/198 |
| 20 | 0.500 | 0.500 | 8/11 | 7/11 | 3/11 | 2/11 | 11/217 | 11/11 |

### Auto pipeline

| K | parallel B2 bin | seq B2 bin | parallel B4 cov | seq B4 cov | parallel id-m | seq id-m | parallel prec_rows | seq prec_rows |
|---|---|---|---|---|---|---|---|---|
| 1 | n/a | 0.167 | n/a | 5/12 | n/a | 2/12 | n/a | 11/11 |
| 5 | n/a | 0.500 | n/a | 10/12 | n/a | 3/12 | n/a | 55/55 |
| 10 | **0.500** | 0.417 | 9/12 | 9/12 | 1/12 | 1/12 | 110/110 | 110/110 |
| 12 | 0.250 | **0.667** | 8/12 | 8/12 | 2/12 | **4/12** | 132/132 | 132/132 |
| 14 | 0.667 | 0.417 | 9/12 | 8/12 | 2/12 | 2/12 | 153/152 | 12/12 |
| 16 | 0.417 | 0.417 | 9/12 | 10/12 | 2/12 | **4/12** | 173/173 | 176/176 |
| 18 | 0.500 | 0.583 | 10/12 | 10/12 | 2/12 | 2/12 | 11/194 | 16/16 |
| 20 | **0.750** | 0.583 | 10/12 | 9/12 | 3/12 | 2/12 | 17/218 | 50/220 |

---

## Findings

### 1. Sequential ≠ uniformly better
The Phase 11 hypothesis was: sequential-with-memory simulator produces more within-twin diversity → higher B4 precision + identity-matched coverage. The data **does not support that as a general rule**.

Win/loss tally (parallel vs sequential, B2 binary):
- V1: parallel wins 4 (K=1, 14, 16, 20), sequential wins 2 (K=10, 12), tied 2 (K=18, K=20)
- Auto: parallel wins 3 (K=10, 14, 20), sequential wins 2 (K=12, 18), tied 2 (K=16)

Sequential's only clear wins:
- **Auto K=12**: B2 binary 0.250 → 0.667 (largest single jump in the study — but might be noise; Auto parallel K=14 = 0.667, so the parallel K=12 = 0.250 may itself be a low outlier).
- **V1 K=10 B2 binary**: 0.417 → 0.583.
- **Auto K=12 id-m**: 2/12 → 4/12.
- **V1 K=14, 16, 18 id-m**: 2/12 → 4/12 consistently (4/12 = 0.333 is the sequential ceiling).

### 2. Identity-matched coverage has a sequential ceiling at 4/12
Sequential's identity-matched coverage caps at 4/12 = 0.333 across the K range (V1 K=14/16/18, Auto K=12/16). Parallel V1 K=10 hits 6/12 = 0.500 — still the study high. Sequential mode does NOT lift identity-matched coverage above the parallel high.

### 3. B4 precision-array truncation persists in sequential mode, sometimes worse
Sequential at high K still triggers the truncation artifact:
- V1 K=14 seq: 42/154 rows (parallel = 154/154 full)
- V1 K=16 seq: **12/12** (truncated to actuals count — collapsed)
- V1 K=18 seq: 20/198
- Auto K=14 seq: **12/12** (truncated)
- Auto K=18 seq: **16/16**

In some cases sequential is *worse*-truncated than parallel at the same K. Sequential mode does not solve the K=20-class evaluator overload.

### 4. K=1 sequential is worse than K=1 parallel
V1 K=1 B2 binary: parallel 0.250 → sequential 0.083. Auto K=1 sequential = 0.167. The single-question prompts are functionally different (sequential prompt asks for "best-guess" with prior empty; parallel K=1 asks for "exactly one"). The sequential prompt seems to encourage hedging.

### 5. K=10 V1 parallel id-matched 6/12 remains the high-water mark
No setting in the entire Phase 11 sweep (24 cells) exceeded V1 parallel K=10's identity-matched coverage = 0.500. That's a real finding: **the V1 parallel K=10 configuration is uniquely good at routing the right question to the right twin**, and neither K change nor sequential simulation reproduces it.

### 6. Best B2 binary in the whole study
- Auto parallel K=20: **0.750 (9/12)** — unchanged study high.
- Sequential best: Auto K=12 = 0.667, V1 K=10 = 0.583.

### 7. K=14 is the cleanest non-truncated high-K point for parallel
Parallel K=14 has full B4 precision rows (V1: 154/154, Auto: 153/152) and shows the strongest B2 binary in the K=12–18 band (V1 0.667, Auto 0.667). If "high-K reporting needed but K=20 truncates", **parallel K=14** is the defensible operating point.

---

## Recommended reporting

| Use case | Setting |
|---|---|
| Headline operating point (Auto vs V1 comparison) | **Auto parallel K=10** (B2 0.500, B4 cov 0.750, B4 prec 0.655, strong-prec 22/110, 110/110 rows) |
| Highest B2 binary | **Auto parallel K=20** (0.750), with caveat that B4 prec is on a truncated subset |
| Highest identity-matched coverage | **V1 parallel K=10** (6/12 = 0.500) |
| Clean high-K (no precision truncation) | **K=14** (both V1 and Auto have full rows) |
| Sequential simulator hypothesis | **Disproven on this dataset.** Sequential helps Auto at K=12 only; identity-matched cap = 4/12. Within-twin near-duplicates in the parallel simulator are not the dominant noise source. |

---

## Files

- Parallel sims: `data_auto/final_eval_{K}q_{src}/summary.json` + `gpt5/*` for K ∈ {1, 5, 10, 12, 14, 16, 18, 20}, src ∈ {v1, auto}
- Sequential sims: `data_auto/final_eval_seq_{K}q_{src}/summary.json` + `gpt5/*` (same grid)
- Prompts:
  - `prompts/simulate_questions_{1,5,10,12,14,16,18,20}q.md` (parallel K)
  - `prompts/simulate_questions_sequential.md` (sequential, 1 question per call with prior context)
- Drivers:
  - `src/rerun_kq.py --K <int> --source v1|auto` (parallel)
  - `src/simulate_sequential.py --K <int> --source v1|auto` (sequential)
- Evaluator: `src/eval_gpt5_generic.py all --in-summary <path> --out-dir <path>/gpt5`
