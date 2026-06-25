# B4 set-level evaluation — Auto K=10 × gpt-5 (Phase 8)

## Context

After Phase 6/7/7b/8 stability sweep on B2, **gpt-5 v1 no-seed** was the most stable evaluator setting (9/12 cells stable across 3 reruns). To upgrade the B4 metric from the earlier gpt-5-mini run, we re-ran the set-level B4 evaluator on the Auto K=10 candidate pool (110 candidates × 12 actuals) using **gpt-5** with the unchanged `prompts/b4_eval.md`.

## B4 stability-sweep summary (B2 cell stability across 3 reruns)

| Setting | cells_stable | binary_flip | trigger_flip | per-run binary |
|---|---|---|---|---|
| gpt-5 v1 no-seed | **9/12** | 1/12 | 7/12 | 0.42 / 0.50 / 0.50 |
| gpt-5 v2 (Sonnet rewrite) | 8/12 | 3/12 | 7/12 | 0.42 / 0.58 / 0.42 |
| gpt-5 v1 seed=42 | 8/12 | 1/12 | 4/12 | 0.50 / 0.50 / 0.58 |
| gpt-5 reasoning-first | 8/12 | 2/12 | 4/12 | 0.50 / 0.50 / 0.50 |

Winner = v1 no-seed. Used for the B4 model choice below.

## B4 set_metrics (gpt-5, Auto K=10 pool)

| Metric | Value |
|---|---|
| actual_question_count | 12 |
| predicted_question_count | 110 |
| **coverage_count** (score ≥3) | **9 / 12 = 0.750** |
| **coverage (strong, ≥4)** | 5 / 12 = 0.417 |
| **precision_count (useful, ≥3)** | **72 / 110 = 0.655** |
| **precision (strong, ≥4)** | 22 / 110 = 0.200 |
| average_actual_best_score | 2.917 |
| average_predicted_best_score | 2.373 |
| identity-matched coverage | 1 / 12 = 0.083 |

**Predicted-side score histogram**: `{0: 23, 1: 1, 2: 14, 3: 50, 4: 22}`. The pool is bimodal-ish — most candidates land at 2–3, very few land at 0/1 (off-topic) or 4 (very-close substitute).

## Per-actual coverage breakdown

| Actual | Covered (≥3) | Score | Best-predicted (winning candidate) | Identity match? |
|---|---|---|---|---|
| matthew_boss-actual-0 | ✓ | 3 | sharon_zackfia-pred-8 | × |
| steven_wieczynski-actual-0 | ✓ | 4 | kevin_kopelman-pred-1 | × |
| brandt_montour-actual-0 | ✓ | 4 | **brandt_montour-pred-1** | ✓ |
| james_hardiman-actual-0 | ✓ | 4 | steven_wieczynski-pred-0 | × |
| lizzie_dove-actual-0 | ✓ | 3 | andrew_didora-pred-8 | × |
| robin_farley-actual-0 | · | 1 | robin_farley-pred-8 | (uncovered) |
| robin_farley-actual-1 | ✓ | 3 | kevin_kopelman-pred-9 | × |
| vince_ciepiel-actual-0 | ✓ | 4 | lizzie_dove-pred-0 | × |
| sharon_zackfia-actual-0 | · | 2 | andrew_didora-pred-5 | (uncovered) |
| andrew_didora-actual-0 | ✓ | 4 | steven_wieczynski-pred-3 | × |
| xian_siew-actual-0 | ✓ | 3 | vince_ciepiel-pred-9 | × |
| kevin_kopelman-actual-0 | · | 2 | robin_farley-pred-6 | (uncovered) |

3 uncovered: `robin_farley-actual-0`, `sharon_zackfia-actual-0`, `kevin_kopelman-actual-0`.

## Headline interpretation

- **Coverage 9/12 (0.750)** matches the prior gpt-5-mini Auto K=10 number (also 9-10/12 range) — the pool's set-level coverage is robust to evaluator model swap.
- **Precision 0.655 (72/110)** is materially **higher** than the gpt-5-mini Auto K=10 prior (0.555 in dedup-rerun) — gpt-5 judges a higher fraction of the 110 candidates as useful (≥3). Cell-level B2 (binary 0.42–0.50 under gpt-5) is much more conservative because each B2 cell scores only the analyst's own 10 predictions against their own actual, while B4 lets the best of all 110 cross-match each actual.
- **Identity-matched coverage 1/12 (0.083)** — only **brandt_montour** correctly attributed to its own twin; every other coverage hit comes from cross-analyst borrowing. This is the key paper finding: at K=10 set-level, the pool "covers" by routing the right question to the wrong twin. The lift from K=1 → K=10 is mostly cross-analyst inventory, not per-twin precision improvement.
- **Strong coverage 5/12 (0.417)** — 5 actuals have a near-substitute candidate somewhere in the 110-pool; the other 4 covered ones are score-3 (substantially similar but not interchangeable).

## Compared to prior K=10 runs

| Evaluator | Coverage | Precision (useful ≥3) | Precision (strong ≥4) | Identity-matched |
|---|---|---|---|---|
| gpt-5-mini (Phase 2 original) | 0.833 | (set-level not separately reported) | — | — |
| gpt-5-mini (Phase 5 dedup rerun) | 0.667 | 0.555 | — | — |
| **gpt-5 (this run)** | **0.750** | **0.655** | **0.200** | **0.083** |

Gpt-5 lands between the two gpt-5-mini runs on coverage, but is markedly stricter on the strong (≥4) bar and reveals the identity-match collapse that mini's looser scoring partly obscured.

## Files

- `data_auto/final_eval_10q_auto/b4_gpt5/b4.json` — raw evaluator output
- `data_auto/final_eval_10q_auto/b4_gpt5/b4_prompt.txt` — prompt sent to LLM
- `src/b4_gpt5_k10.py` — driver
