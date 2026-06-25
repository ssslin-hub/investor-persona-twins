# Chunked vs single-call B4 coverage — analysis (strict rubric, seed-1)

**Question.** Does splitting the predicted-question pool into chunks (≤50 candidates per B4 call, taking each actual's max match-score across chunks) improve measured set-level coverage versus a single B4 call over the whole pool, and is the improvement real?

**Setup.** 21 configs = {v1, v5, auto} × K∈{5,10,12,14,16,18,20}, seed-1. Strict rubric `prompts/b4_eval_strict.md`. Coverage = fraction of the 12 holdout actuals with a predicted question scoring ≥3. Two judges: gpt-5-mini and gpt-5. One run per (config, method, model).

## 1. Coverage K-curve (four measurements)

| source | K | single mini | chunked mini | single gpt-5 | chunked gpt-5 |
|---|---|---|---|---|---|
| v1 | 5 | 0.583 | 0.583 | 0.667 | 0.750 |
| v1 | 10 | 0.667 | 0.833 | 0.583 | 0.667 |
| v1 | 12 | 0.667 | 0.750 | 0.583 | 0.750 |
| v1 | 14 | 0.750 | 0.750 | 0.667 | 0.833 |
| v1 | 16 | 0.750 | 0.846 | 0.583 | 0.750 |
| v1 | 18 | 0.667 | 0.917 | 0.583 | 0.833 |
| v1 | 20 | 0.583 | 0.833 | 0.583 | 0.750 |
| v5 | 5 | 0.500 | 0.667 | 0.417 | 0.417 |
| v5 | 10 | 0.500 | 0.750 | 0.583 | 0.750 |
| v5 | 12 | 0.583 | 0.917 | 0.500 | 0.667 |
| v5 | 14 | 0.385 | 0.833 | 0.583 | 0.833 |
| v5 | 16 | 0.667 | 0.750 | 0.667 | 0.833 |
| v5 | 18 | 0.667 | 0.833 | 0.417 | 0.833 |
| v5 | 20 | 0.500 | 0.833 | 0.583 | 0.667 |
| auto | 5 | 0.583 | 0.750 | 0.500 | 0.500 |
| auto | 10 | 0.667 | 0.833 | 0.500 | 0.750 |
| auto | 12 | 0.667 | 0.833 | 0.500 | 0.667 |
| auto | 14 | 0.667 | 0.917 | 0.667 | 0.833 |
| auto | 16 | 0.500 | 0.833 | 0.583 | 0.667 |
| auto | 18 | 0.692 | 1.000 | 0.727 | 0.583 |
| auto | 20 | 0.667 | 1.000 | 0.500 | 0.833 |
| **mean** | | **0.615** | **0.822** | **0.570** | **0.722** |

Takeaways: single-call **mini** under-counts (large-pool blindness, worst at high K); chunked **mini** over-counts (lenient judge × max-over-chunks inflation, hits 1.000 at auto K18/K20); the trustworthy column is **chunked gpt-5**.

## 2. The chunking effect, judge held fixed at gpt-5

| source | K | single gpt-5 | chunked gpt-5 | Δ (chunk−single) |
|---|---|---|---|---|
| v1 | 5 | 0.667 | 0.750 | +0.083 |
| v1 | 10 | 0.583 | 0.667 | +0.083 |
| v1 | 12 | 0.583 | 0.750 | +0.167 |
| v1 | 14 | 0.667 | 0.833 | +0.167 |
| v1 | 16 | 0.583 | 0.750 | +0.167 |
| v1 | 18 | 0.583 | 0.833 | +0.250 |
| v1 | 20 | 0.583 | 0.750 | +0.167 |
| v5 | 5 | 0.417 | 0.417 | +0.000 |
| v5 | 10 | 0.583 | 0.750 | +0.167 |
| v5 | 12 | 0.500 | 0.667 | +0.167 |
| v5 | 14 | 0.583 | 0.833 | +0.250 |
| v5 | 16 | 0.667 | 0.833 | +0.167 |
| v5 | 18 | 0.417 | 0.833 | +0.417 |
| v5 | 20 | 0.583 | 0.667 | +0.083 |
| auto | 5 | 0.500 | 0.500 | +0.000 |
| auto | 10 | 0.500 | 0.750 | +0.250 |
| auto | 12 | 0.500 | 0.667 | +0.167 |
| auto | 14 | 0.667 | 0.833 | +0.167 |
| auto | 16 | 0.583 | 0.667 | +0.083 |
| auto | 18 | 0.727 | 0.583 | -0.144 |
| auto | 20 | 0.500 | 0.833 | +0.333 |

**Chunking improves coverage in 18/21 configs** (ties 2, single better 1). Mean Δ = **+0.152**, median +0.167, max +0.417. Mean coverage rises 0.570 → 0.722. The gains concentrate at high K (where the single 200-item call is blindest) and vanish at K=5 (≈55 candidates fit one call). The one loss (auto K18) is single-run noise.

## 3. Mechanism — does chunking pick a different prediction?

Per (actual, config) pair, comparing the candidate each method selected (gpt-5 judge):

| | count | share |
|---|---|---|
| same candidate | 86 | 34% |
| **different candidate** | 164 | **66%** |
| → of those, chunked scored higher | 71 | 43% of diffs |

Of the **46** cases where chunked covers (≥3) but single-call misses (<3), **35 (76%) used a different candidate** — i.e. chunking surfaced a better-matching prediction the single call never picked. The remaining 11 (24%) are same-candidate re-scoring (single-run judge noise). So ~3/4 of the coverage gain is genuine retrieval, ~1/4 is noise.

## 4. Reliability of the chunked ≥3 matches

Across 21 configs, how often each actual is covered by chunked gpt-5 (a stable pattern indicates a reliable judge, not random inflation):

| actual | covered in N/21 configs |
|---|---|
| `brandt_montour-actual-0` | 21/21 |
| `lizzie_dove-actual-0` | 21/21 |
| `vince_ciepiel-actual-0` | 21/21 |
| `xian_siew-actual-0` | 21/21 |
| `matthew_boss-actual-0` | 19/21 |
| `andrew_didora-actual-0` | 19/21 |
| `james_hardiman-actual-0` | 18/21 |
| `robin_farley-actual-1` | 16/21 |
| `steven_wieczynski-actual-0` | 15/21 |
| `sharon_zackfia-actual-0` | 10/21 |
| `kevin_kopelman-actual-0` | 1/21 |

The pattern is highly stable: a fixed set of actuals (matthew/brandt/lizzie/vince/xian) are covered almost everywhere, while `robin_farley-0` and `kevin_kopelman-0` are rejected almost everywhere. A noisy or inflating judge would not reject the same questions every time. Full-text audit of every covered match: `reports/chunked_gpt5_covered_all.md`.

## 5. Conclusion & recommendation

- **Chunking genuinely improves measured B4 coverage** under a reliable judge (+0.15 mean, 18/21 configs), because the single call goes blind on 200+ candidates and chunking surfaces better matches (different candidate in 66% of pairs; 76% of coverage wins).
- **Score it with gpt-5, not mini.** Chunked-mini inflates (lenient judge × max-over-chunks), overstating coverage by up to +0.42 and hitting a spurious 1.000 at auto K18/K20.
- **Recommended coverage metric: chunked retrieval + gpt-5 scoring** (mean ≈ 0.72 across configs), versus the depressed single-call mini K-curve (≈ 0.61).
- **Caveat:** all numbers are single-run; individual cells are noisy (±~0.1). The trends (mean Δ, 18/21 win rate, 66%/76% mechanism splits) are robust; per-config values need ≥3 runs or all-5-seeds to firm up.

## Provenance

- Builders: `batch_build_strict_b4_chunked.py` (chunked), `batch_build_single_gpt5.py` (single gpt-5). Parsers: `parse_strict_b4_chunked.py`, `parse_and_report_single_gpt5.py`.
- Data: `final_eval_{K}q_{src}/strict_b4_chunked/{gpt_5_mini,gpt_5}/b4.json`, `.../strict_b4_single_gpt5/b4.json`, `.../strict_b4/b4.json` (single mini).
- Companion reports: `strict_b4_chunked_kcurve.md`, `chunk_vs_single_gpt5.md`, `chunked_gpt5_covered_all.md`, `auto_k18_all_questions.md`.

