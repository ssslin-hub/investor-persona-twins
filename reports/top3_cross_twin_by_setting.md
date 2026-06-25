# Phase 13b — cross-twin top-3 convergence per setting

For each of 6 settings, this report inspects all 11 twins' top-3 predictions and asks: do different personas produce DISTINCT top-3 (high persona discrimination), or do all twins COLLAPSE onto the same management-presentation hotspots (low discrimination)?

Phase 9 prior finding: "Auto twins converge on shared salient topics (fuel ~$0.62, Med booking moderation, Trifecta) — 10 of 22 score-4 B4 candidates pointed at andrew_didora's fuel question". This report verifies that pattern across the K-curve.

Topic-label counting follows the JSON `topic_label` field literally (with minor semantic grouping where labels differ trivially — e.g., `booking_curve` and `demand/booking_curve (Med)` count together as Med-booking).

---

## parallel_K10_v1

**Topic counts across 11 twins × 3 picks = 33 top-3 slots**:
- demand/booking_curve (Mediterranean): 6 twins (matthew, lizzie, robin, vince, xian, kevin)
- pricing/yield: 5 twins (brandt, lizzie, robin, vince, kevin)
- costs / Q2 dry-dock: 4 twins (brandt, lizzie, robin, kevin)
- booked-position translation: 3 twins (matthew, steven, brandt)
- Trifecta/ROIC: 2 (matthew, james)
- andrew's bond-financing triple: niche (all 3 picks all andrew, not cross-twin)

**Distinct twins** (top-3 doesn't overlap with the cross-convergence hotspots):
- sharon: passenger source-mix + booking behavior + owned-destinations
- andrew: bond financing (rates / refinancing / maturity) — completely outside the demand/yield/cost cluster

**Collapsing twins** (top-3 dominated by the shared Med/yield/cost trio):
- 7 twins: matthew, steven, brandt, lizzie, robin, vince, xian, kevin (cold-start uses generic Med+yield+fuel triple)

**Hotspots**: Mediterranean demand (6), yield decomposition (5), Q2 costs (4).

- Convergence hotspots: Med demand (6/11), yield (5/11), costs (4/11)
- Distinct twins: 2 (sharon, andrew)
- Collapsing twins: 8/11 (incl. 2 cold-start)
- **Verdict: medium**

## parallel_K10_auto

**Topic counts**:
- demand/booking_curve (Mediterranean): **9 twins** (matthew, brandt, steven, lizzie, robin, vince, andrew, xian, kevin) — almost everyone
- fuel/hedging: **5 twins** (matthew, james, robin, xian, kevin)
- pricing/yield: 4 twins (brandt, lizzie, robin, vince)
- ROIC / capital: 1 (james)
- costs/cadence: 2 (steven, lizzie)
- pre-booking / demographics / AI: 1 (sharon, all 3 slots)
- forward booking visibility: 1 (andrew [0])
- onboard_spend: 1 (vince [2])

**Distinct twins**: only sharon (pre-booking, demographics, AI/digital monetization). Even andrew's normally bond-focused persona now leads with `booking_curve / forward_visibility` and includes fuel — he's been pulled into the convergence.

**Collapsing twins**: 10/11. The auto-discovery loop's persona refinements pushed everyone except sharon onto Med/fuel/yield.

- Convergence hotspots: Med demand (9/11!), fuel (5/11), yield (4/11)
- Distinct twins: 1 (sharon)
- Collapsing twins: 10/11
- **Verdict: low** (confirms Phase 9 — Auto's persona refinement homogenizes twins onto management's hot signals)

## parallel_K14_v1

**Topic counts**:
- demand/booking_curve (Med): 6 twins (matthew, brandt, robin, vince, xian, kevin)
- pricing/yield: 5 twins (brandt, robin, vince, xian, kevin)
- costs: 4 twins (lizzie, robin, xian, kevin)
- booked-position: 2 (matthew, steven)
- Returns/ROIC: 2 (james, steven via capital_return)
- ticket-vs-onboard / new hardware / capex: scattered (steven [1], james [2], vince [2])
- bond financing: 3 (all andrew — niche)
- passenger / booking behavior / owned-destinations: 3 (all sharon — niche)
- yield cadence + cost timing (lizzie [1][2]): niche

**Distinct twins**: sharon, andrew (same as K=10_v1).
**Collapsing twins**: matthew, steven, brandt, lizzie, robin, vince, xian, kevin (8/11).

Pattern identical to K10_v1 — adding 4 more candidates per twin (10→14) doesn't change top-3 cross-twin distribution.

- Convergence hotspots: Med (6/11), yield (5/11), costs (4/11)
- Distinct twins: 2 (sharon, andrew)
- Collapsing twins: 9/11 (incl 2 cold-start)
- **Verdict: medium** (= K10_v1)

## parallel_K14_auto

**Topic counts**:
- demand/booking_curve (Med): **9 twins** (matthew, brandt twice, lizzie, robin, vince, xian, kevin, andrew)
- pricing/yield: 6 twins (matthew, brandt, lizzie, robin, vince, kevin)
- costs / fuel: 5 twins (matthew, lizzie, xian, kevin, andrew)
- Returns/ROIC/CapEx/balance-sheet: 3 (all james — niche)
- pre-booking / AI / passenger sourcing: 3 (all sharon — niche)
- capital_return: 2 (steven, kevin [2])
- yield_vs_onboard / onboard_spend: 2 (steven, vince)
- forward visibility: 1 (andrew [0])

**Distinct twins**: sharon (pre-booking/AI/demographics), james (ROIC/CapEx/balance-sheet — at K=14 Auto, james doesn't drift into Med).
**Collapsing twins**: matthew, brandt, lizzie, robin, vince, xian, kevin, andrew (8/11 incl 2 cold-start).

- Convergence hotspots: Med (9/11), yield (6/11), costs/fuel (5/11)
- Distinct twins: 2 (sharon, james)
- Collapsing twins: 9/11
- **Verdict: low** (= K10_auto)

## parallel_K20_v1

**Topic counts** (inferred from compact file):
- demand/booking_curve (Med): 6+ twins (matthew, brandt, robin, vince, xian, kevin)
- pricing/yield: 5+ twins (brandt, lizzie, robin, vince, xian, kevin)
- costs / fuel: 4-5 twins (lizzie, robin, xian, kevin, sharon K=20 [1] added a fuel question)
- booked-position / Trifecta: matthew[0]+matthew[2], steven[0]
- new hardware: vince[1]
- bond financing: 3 (all andrew, K=20 V1 also kept on bond theme)
- passenger source-mix + booking behavior: 2 (sharon)

**Distinct twins**: sharon (with one fuel-bleed at slot [1] at K=20), andrew.
**Collapsing twins**: 8/11.

- Convergence hotspots: Med (6/11), yield (5/11), costs (5/11)
- Distinct twins: 2 (sharon partially, andrew)
- Collapsing twins: 9/11
- **Verdict: medium** (slight degradation from K=10_v1 — sharon starts bleeding into costs/fuel at K=20)

## parallel_K20_auto

**Topic counts**:
- demand/booking_curve (Med): 9+ twins
- pricing/yield: 6+ twins
- fuel/hedging: 5+ twins (across multiple positions)
- ROIC / capital_return: 2 (james [2], kevin K=20 [2] capital_return)
- pre-booking / passenger sourcing / AI: 3 (sharon — slightly drifted, K20_auto [1] is geographic_mix not passenger source-mix; still distinct)
- onboard_spend / digital monetization: 2 (vince [1], sharon [2])
- booking visibility: 1 (andrew [0])

**Distinct twins**: sharon (pre-booking + geographic_mix + AI/monetization).
**Collapsing twins**: 10/11 — same as K=10_auto pattern. Even james at K=20 Auto bleeds: his top-3 is yield + fuel_hedge + capital_return, no longer pure Trifecta/CapEx focus.

- Convergence hotspots: Med (9+/11), yield (6+/11), fuel (5+/11)
- Distinct twins: 1 (sharon)
- Collapsing twins: 10/11
- **Verdict: low**

---

## Summary

### Verdict counts across 6 settings

| Setting | Convergence on Med | Convergence on fuel/cost | Distinct twins | Verdict |
|---|---|---|---|---|
| parallel_K10_v1 | 6/11 | 4/11 | sharon, andrew (2) | medium |
| parallel_K10_auto | **9/11** | 5/11 | sharon (1) | **low** |
| parallel_K14_v1 | 6/11 | 4/11 | sharon, andrew (2) | medium |
| parallel_K14_auto | **9/11** | 5/11 | sharon, james (2) | **low** |
| parallel_K20_v1 | 6+/11 | 5/11 | sharon (partial), andrew (~2) | medium |
| parallel_K20_auto | **9+/11** | 5+/11 | sharon (1) | **low** |

### V1 vs Auto at matched K (cross-twin convergence)

| K | V1 verdict | Auto verdict | Δ |
|---|---|---|---|
| 10 | medium | **low** | Auto more convergent (-1 distinct twin) |
| 14 | medium | **low** | Auto more convergent (-0 distinct twins, but more Med dominance) |
| 20 | medium | **low** | Auto more convergent (-1 distinct twin) |

**V1 consistently preserves more distinct personas (sharon AND andrew) than Auto (sharon only, occasionally james).** This is the same Phase 9 finding stated differently — Auto's discovery loop refinements push every twin to attend to management's most-salient signals (Mediterranean disruption, fuel hedge, yield range), homogenizing them. V1's hand-written personas leave sharon (consumer/loyalty focus) and andrew (financing focus) intact as distinct attractors.

### K-effect: does cross-twin convergence grow with K?

No — the convergence count is essentially flat across K=10/14/20 (Auto: 9/9/9+ twins on Med). Adding more candidates per twin (K=10→14→20) doesn't pull niche twins (sharon, andrew, james) into the convergence — they keep their distinct top-3. **K is not the convergence lever; persona source (V1 vs Auto) is.**

### Why the convergence happens

Three management-presentation signals dominated the 2026-Q1 call:
1. **Mediterranean booking moderation** (then "turning the corner") — explicitly called out by Jason
2. **$0.62 / $0.74 per-share fuel headwind** + ~60% hedged for 2026
3. **Net Yield guide 1.5-2.5%** with Q2 only +0.2%

Every persona that includes any version of "I care about yield/costs/demand" gets pulled to predict questions about these three. Auto's loop apparently amplifies this attention because Variant A's shared-prompt refinement teaches all personas to be more responsive to management's quantitative signals. Personas with strong orthogonal focus (sharon = consumer behavior; andrew = capital structure) resist.

### Recommendation

If the goal is **set-level coverage of high-salience actuals**, Auto's homogenization is a feature (precision strong 22/110 at K=10 vs V1's 5/110). If the goal is **identity-matched coverage** (right question to right twin) or **persona diversity**, V1 wins. For paper presentation:
- Report Auto K=10 for "best B2 binary + B4 precision" headlines
- Report V1 K=10 for "highest identity-matched coverage" + "stronger persona discrimination"
- Note that the trade-off is fundamentally about how aggressive the discovery loop refines personas toward observed management hot signals
