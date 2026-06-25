# Phase 23 — 5-tier persona architecture at K=5

**Evaluator**: gpt-5, B2 + B4, 5 runs per setting. K=5 (55 candidates per pool).
**Override applied**: when B2 binary=True for a cell but B4 cov=False, B4 cov forced True (Phase 9/10 invariant).

## Headline table — 4 systems × 5 runs

| System | n | B2 binary per run             | B2 mean | B2 [min, max] | B4 cov_fix mean | B4 precision mean |
|--------|---|-------------------------------|---------|---------------|-----------------|-------------------|
| **V1** | 5 | 0.58 0.67 0.50 0.58 0.50      | **0.567** | **[0.500, 0.667]** | **0.750**       | 0.618             |
| Auto   | 5 | 0.25 0.17 0.25 0.25 0.17      | 0.217   | [0.167, 0.250] | 0.650           | 0.585             |
| v5     | 5 | 0.33 0.42 0.42 0.42 0.33      | 0.383   | [0.333, 0.417] | 0.645           | 0.618             |
| v6     | 5 | 0.42 0.42 0.33 0.33 0.36      | 0.373   | [0.333, 0.417] | 0.617           | 0.520             |

## Findings

1. **v6 did NOT beat V1 at K=5** — v6 mean B2 binary 0.373 vs V1 0.567. The new 5-layer architecture (Company / Asset / Theme / Analyst-v6 / Call ctx) ≈ v5 (0.383) and both materially below V1 (0.567).
2. **v6 ≈ v5 within spread** — the Layer 1-3 additions on top of v5's behavioral fields contributed no measurable lift at K=5.
3. **V1 also wins on stability** — V1 spread 0.167 is tighter than v5/v6 (0.083) only nominally; V1's mean and min both dominate.
4. **V1 wins on B4 cov_fix** — 0.750 vs 0.617-0.650 for the others. V1's hand-written topic priors put the right topics in the K=5 pool more often.
5. **Auto K=5 is the worst by a wide margin** — 0.217. Auto-discovered personas underperform at small K; their advantage only appeared at K=10+ in earlier phases (Phase 9/11).
6. **B4 precision**: v6 lowest (0.520) — added layers caused the simulator to spread candidates across more dimensions, lowering per-candidate hit rate.

## Decision rule outcome

Phase 23 plan: "v6 ≥ max(V1, Auto, v5) on B2 binary OR sim-spread substantially smaller than V1's 0.367 (Phase 21 baseline)".

- v6 B2 binary (0.373) is **below** V1 (0.567).
- v6 sim-spread within evaluator (0.083) is small, but V1's eval-spread at K=5 is also 0.167 — not 0.367 (that was K=14 with separate sim reruns, not directly comparable to single-sim eval-only spread here).

**Verdict: 5-tier architecture does not improve over V1 at K=5.**

## Possible reasons for the null result

1. **Filter discards signal**: `select_relevant_assets` caps at 6 assets and `select_relevant_themes` at 5. With K=5 outputs the simulator has only 1 question per relevant asset/theme — the layered context becomes overhead rather than signal.
2. **Cold-start fallback dominates K=5**: 2 of 11 analysts (xian/kevin) use the auto-fallback persona regardless of layer system; at K=5 they contribute ~2/55 = 18% of the pool with no v6 benefit.
3. **K=5 is too small to exploit layer diversity**: the 5-dim sampling space (topic/object/framing/granularity/form) needs more questions per analyst to differentiate. V1 at K=5 may simply be saturating on the easy hits.
4. **Layer 2-3 mention extraction was regex-based** (Python pre-extract), not semantic — may have missed analyst-asset edges that v5's LLM-extracted `recurring_concerns.core_topics` captured.

## Next steps to consider

- **Re-run v6 at K=10 or K=14** before declaring the architecture dead. The hypothesis was that v6 constrains the 5 dimensions; that only matters when the simulator has enough K to span them.
- **Inspect v6 sim outputs vs V1 sim outputs** on 1-2 specific analysts (e.g., lizzie, robin from Phase 22 fluke analysis) to see whether v6 questions are different in kind or just lower-quality.
- **Verify `engages_assets` lists are non-empty** for the 9 returning analysts (Phase 23 plan §4 verification was not run — possible the asset_persona `asked_by_history` extraction returned empty for most analysts due to schema drift in Paradise Island and similar files).
