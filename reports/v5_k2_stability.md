# v5 K=2 simulator stability (3 reruns, pairwise B2 gpt-5)

v5 personas (`data/personas_v5/`) × K=2 simulator, run 3 times. For each twin, pairwise B2 across the 3 reruns measures whether top-2 stays the same.

---

## Results (sorted by history)

| Analyst | History | v5 K=2 mean sim | min | Pair scores | Verdict |
|---|---|---|---|---|---|
| robin farley | 230 | 3.67 | 3.0 | 4.0 / 4.0 / 3.0 | stable |
| brandt montour | 186 | **3.17** | 2.0 | 3.5 / **2.0** / 4.0 | wobbly — one outlier |
| steven wieczynski | 139 | **4.00** | 4.0 | 4.0 / 4.0 / 4.0 | rock-solid |
| vince ciepiel | 89 | **4.00** | 4.0 | 4.0 / 4.0 / 4.0 | rock-solid |
| james hardiman | 80 | 3.50 | 3.0 | 3.5 / 3.0 / 4.0 | stable |
| matthew boss | 76 | 3.50 | 3.0 | 3.5 / 3.0 / 4.0 | stable |
| lizzie dove | 34 | **2.67** | **1.0** | 3.0 / **1.0** / 4.0 | **unstable** — one pair scored 1 |
| sharon zackfia | 9 | 3.00 | 3.0 | 3.0 / 3.0 / 3.0 | stable but mid |
| andrew didora | 3 | 3.33 | 3.0 | 3.0 / 4.0 / 3.0 | stable |
| xian siew | 0 | 3.17 | 3.0 | 3.5 / 3.0 / 3.0 | stable (cold-start fallback) |
| kevin kopelman | 0 | 3.00 | 2.0 | 3.0 / 2.0 / 4.0 | wobbly |

**Mean across 11 twins**: 3.36 (vs Phase 15: v1 K=10 = 3.55, Auto K=10 = 3.45).

## Cross-setting stability comparison

| Twin | v5 K=2 | V1 K=10 (P15) | Auto K=10 (P15) |
|---|---|---|---|
| matthew | 3.50 | 3.67 | 3.50 |
| steven | **4.00** | 2.83 | 3.33 |
| brandt | 3.17 | **4.00** | **4.00** |
| james | 3.50 | 3.67 | 3.17 |
| lizzie | **2.67** | 3.50 | **4.00** |
| robin | 3.67 | **4.00** | 3.83 |
| vince | **4.00** | 3.83 | 3.00 |
| sharon | 3.00 | **4.00** | **4.00** |
| andrew | 3.33 | 3.83 | **4.00** |
| xian | 3.17 | 2.50 | 2.83 |
| kevin | 3.00 | 3.17 | 2.83 |
| **mean** | **3.36** | **3.55** | **3.45** |

## Findings

1. **v5 K=2 is slightly less stable on average than V1/Auto at K=10** (3.36 vs 3.45-3.55). Mechanism: with only 2 slots, rerun-to-rerun differences in which 2 topics make it through the simulator are amplified.

2. **Winners on v5 K=2**: steven, vince hit 4.00. v5's persona for these two pins them to narrow modeling-style asks (Net Yield decomposition + onboard split for steven; yield + new hardware for vince) — the K=2 slots get filled identically every time.

3. **Losers on v5 K=2**: lizzie drops to 2.67 with one pair scoring **1.0** — between two of the three reruns the top-2 questions are essentially unrelated. lizzie's v5 persona breadth (yield + cost + private destinations) is too wide for K=2.

4. **v5 LIFTS steven's stability from 2.83 (V1) → 4.00 — biggest single-twin improvement**. v5's extraction grabbed steven's persistent "modeling-heavy / capital-return / booking visibility" theme tighter than V1 did.

5. **v5 DROPS brandt and lizzie**: brandt was rock-solid 4.00 on both V1/Auto K=10 but dips to 3.17 at v5 K=2; lizzie drops from 3.50/4.00 to 2.67. At K=2 the wider v5 persona doesn't help — needs more K slots to surface its richness.

## Interpretation

v5 personas have **higher topical resolution per analyst** (queue_behavior + cross_analyst_reactivity + ranked core_topics with n_turns) but at K=2 the simulator can only express the top 2 of that richness. Cell-by-cell stability shows that:
- For analysts where v5's TOP-2 topic is unambiguously dominant (steven, vince) → v5 K=2 is rock-solid
- For analysts where v5 holds 5+ near-equal topics (lizzie, brandt) → K=2 rerun variation amplified

**Implication**: v5 personas should pair with K ≥ 5 to surface their depth. The K=2 single-shot is too tight a bottleneck. We'll see this confirmed when Phase 17 (v5 K=10 × 3 runs × 2 models) lands.

## Files

- `data_auto/final_eval_2q_v5/run_{1,2,3}/summary.json` — per-rerun K=2 predictions
- `data_auto/final_eval_2q_v5/pairwise_b2.json` — pairwise similarity matrix
- `src/v5_k2_stability.py` — driver
- `prompts/simulate_questions_2q.md` — forked K=2 simulator prompt
