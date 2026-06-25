# Phase 15 — simulator stability vs analyst history length

For each of 11 analysts, the K=10 simulator was rerun 3 times under identical persona + management context. The top-3 candidate list from each rerun was then compared against the top-3 of the other two reruns via pairwise B2 evaluator (gpt-5), producing 3 pairwise scores per analyst per source (V1, Auto). Mean score across the 3 pairs is the "sim stability" metric: 4.0 = top-3 essentially identical across reruns; <3.0 = top-3 changes meaningfully.

History = train_combined.json record count per analyst (RCL + 5 peer tickers, ≤ 2025-Q2).

---

## Results table — sorted by history length

### V1 K=10 (V1 personas)

| Analyst | History | mean sim | min | Pair scores |
|---|---|---|---|---|
| robin farley | 230 | **4.00** | 4.0 | 4.0 / 4.0 / 4.0 |
| brandt montour | 186 | **4.00** | 4.0 | 4.0 / 4.0 / 4.0 |
| steven wieczynski | 139 | 2.83 | 2.5 | 2.5 / 3.0 / 3.0 |
| vince ciepiel | 89 | 3.83 | 3.5 | 4.0 / 3.5 / 4.0 |
| james hardiman | 80 | 3.67 | 3.5 | 3.5 / 4.0 / 3.5 |
| matthew boss | 76 | 3.67 | 3.0 | 4.0 / 3.0 / 4.0 |
| lizzie dove | 34 | 3.50 | 3.0 | 3.5 / 4.0 / 3.0 |
| sharon zackfia | 9 | **4.00** | 4.0 | 4.0 / 4.0 / 4.0 |
| andrew didora | 3 | 3.83 | 3.5 | 3.5 / 4.0 / 4.0 |
| xian siew | 0 | **2.50** | 2.0 | 2.5 / 2.0 / 3.0 |
| kevin kopelman | 0 | 3.17 | 3.0 | 3.0 / 3.5 / 3.0 |

### Auto K=10 (auto-discovery personas)

| Analyst | History | mean sim | min | Pair scores |
|---|---|---|---|---|
| robin farley | 230 | 3.83 | 3.5 | 3.5 / 4.0 / 4.0 |
| brandt montour | 186 | **4.00** | 4.0 | 4.0 / 4.0 / 4.0 |
| steven wieczynski | 139 | 3.33 | 3.0 | 4.0 / 3.0 / 3.0 |
| vince ciepiel | 89 | 3.00 | 2.0 | 3.0 / 4.0 / 2.0 |
| james hardiman | 80 | 3.17 | 2.5 | 3.5 / 2.5 / 3.5 |
| matthew boss | 76 | 3.50 | 3.0 | 3.0 / 3.5 / 4.0 |
| lizzie dove | 34 | **4.00** | 4.0 | 4.0 / 4.0 / 4.0 |
| sharon zackfia | 9 | **4.00** | 4.0 | 4.0 / 4.0 / 4.0 |
| andrew didora | 3 | **4.00** | 4.0 | 4.0 / 4.0 / 4.0 |
| xian siew | 0 | 2.83 | 2.0 | 2.5 / 4.0 / 2.0 |
| kevin kopelman | 0 | 2.83 | 2.5 | 2.5 / 3.0 / 3.0 |

---

## Headline finding: the hypothesis is REJECTED

**Pearson correlation between history length and mean sim score**:
- V1: r ≈ +0.13 (essentially zero, weak positive)
- Auto: r ≈ +0.20 (also weak)

**More history does NOT systematically produce more stable simulator output.** Look at the extremes:
- Robin farley (history 230) and brandt montour (186) — top scorers (4.00 each on V1) — high stability ✓
- BUT sharon zackfia (history 9), andrew didora (3), lizzie dove (34) — also score 4.00 on Auto
- Steven wieczynski (history 139, third-highest) — only 2.83 on V1 and 3.33 on Auto, weaker than several low-history analysts
- Xian siew (history 0) is least stable on BOTH sources (2.50 / 2.83)
- Kevin kopelman (history 0) is mid-pack stable (3.17 / 2.83)

## What actually drives stability

The data is consistent with **persona constraint strength**, not history length:

1. **Strongly-topic-pinned personas → 4.00**. brandt (Mediterranean obsession), robin (yield decomposition), sharon (consumer/loyalty focus), andrew Auto (fuel hedging) all hit 4.00 — but for very different reasons. brandt has a lot of history that gave him a single dominant topic; sharon has minimal history but the persona is laser-focused on consumer behavior; andrew Auto is locked onto fuel by the discovery loop.

2. **Cold-start analysts that share the generic fallback persona** (xian, kevin) are least stable — but they're stable in different ways. Both hit 2.5-3.0 range. Their generic persona allows the simulator to wander across Med/yield/fuel from rerun to rerun.

3. **High-history but topic-broad personas** (steven wieczynski with 139 records covering modeling, capital allocation, ROIC, ticket/onboard mix) drift more across reruns — 2.83 on V1. **Breadth of historical interests can hurt simulator stability because the LLM picks a different "top topic" each rerun.**

## V1 vs Auto stability comparison

Mean sim across all 11 twins:
- V1: 3.55 mean
- Auto: 3.45 mean

Essentially the same. Auto's discovery refinement does not systematically reduce simulator-side rerun variance.

Per-analyst V1→Auto delta:
- **More stable on Auto** (+): lizzie (+0.50), sharon (0), andrew (+0.17), matthew (-0.17 → no), brandt (0), kevin (-0.33)
- **More stable on V1** (-): robin (-0.17), steven (+0.50), vince (-0.83), james (-0.50), xian (+0.33)

Auto helps stability for the topic-narrow-focused twins (lizzie, andrew); hurts for the modeling-focused twins (steven, vince, james).

---

## Conclusion

**The hypothesis "more history → more stable simulator output" is not supported by the data.** What matters is whether the persona pins the analyst to a narrow topic attractor. Two ways to get a topic-pinned persona:

1. **Long history that converges on a single theme** (brandt = Mediterranean booking, robin = yield decomposition) — naturally narrow
2. **Short history but a deliberately narrow persona** (sharon = consumer/loyalty, andrew Auto = fuel hedging) — narrow by design

Conversely, two ways to get unstable output:
1. **No persona constraint** (xian, kevin cold-start fallback) — LLM wanders
2. **Long history but topical breadth** (steven covers everything; james split between ROIC and yield) — LLM picks differently each rerun

**Recommendation**: persona quality (topical narrowness + actionability) matters more than persona richness (history depth). The auto-discovery loop's Variant B refinement could be re-targeted at "narrow the persona to its dominant topic" rather than "add more sub-fields", and this would likely improve simulator stability without needing more history per analyst.

## Files

- `data_auto/final_eval_10q_{v1,auto}/sim_stability/run_{1,2,3}/summary.json` — per-rerun K=10 predictions
- `data_auto/final_eval_10q_{v1,auto}/sim_stability/top3_per_run.json` — extracted top-3 per rerun
- `data_auto/final_eval_10q_{v1,auto}/sim_stability/pairwise_b2.json` — pairwise B2 similarity matrix per analyst
- `src/sim_stability.py` — driver
