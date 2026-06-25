# Phase 13b — within-twin top-3 K-stability across 6 settings

For each of 11 analysts, the top-3 predicted questions (rank 0/1/2) were extracted from each of 6 settings: `parallel_K10_v1`, `parallel_K10_auto`, `parallel_K14_v1`, `parallel_K14_auto`, `parallel_K20_v1`, `parallel_K20_auto`. Each section diagnoses whether the top-3 is STABLE across K (the same 3 sub-topics recur) or DRIFTING, and whether the actual 2026-Q1 question is semantically covered by any setting's top-3.

Note: this analysis was produced by the main session after Sonnet sub-agents failed on long-context credits.

---

## matthew boss

**Actual 2026-Q1**: drivers of durable multi-year yield growth despite geopolitical/capacity headwinds (Trifecta framing).

V1 top-3 is **stable** across K=10/14/20: `booked_position_translation` + `demand/booking_curve (Med)` + `margins/Trifecta` recur consistently. K=14 swaps margins/Trifecta for pricing/yield decomposition, but Trifecta returns at K=20. Auto top-3 is also **stable**: `demand/booking_curve (Med)` + `yield_to_cost/margin` + `fuel_hedging` repeat at K=10/14/20. The actual question maps directly to "margins/Trifecta" (Perfecta 20% CAGR through 2027) — covered by V1 K=10 [1] and V1 K=20 [2] but **not** by any Auto setting (Auto skips Trifecta entirely in favor of fuel).

- Actual 2026-Q1: drivers of durable multi-year yield growth (Trifecta 20% CAGR drivers)...
- Verdict: **persona-pinned** (top-3 stable, but V1 and Auto pin different sub-topics)

## steven wieczynski

**Actual 2026-Q1**: Q3 yield trajectory similar to Q2 + capacity implications for 2027.

Both V1 and Auto top-3 are **stable** across K. V1 consistently: `booking/visibility` + `ticket/onboard mix` + `capital_return`. Auto consistently: `bookings/booking_curve` + `yield_vs_onboard guidance` + `costs/cadence`. The actual question (Q3 yield + 2027 capacity) maps to "guidance_upside" in V1 K=20 [2] (which references $17.10-$17.50 EPS guide) and Auto K=14 [0] (Perfecta 20% CAGR to 2027). Partial coverage in both.

- Actual 2026-Q1: Q3 yield trajectory similar to Q2 + 2027 capacity implications...
- Verdict: **persona-pinned**

## brandt montour

**Actual 2026-Q1**: Q3 + Mediterranean specifics — how much left to book, damage assessment.

Strongest persona-pin in the study. All 6 settings produce the SAME top-3 triple: `pricing/yield` + `booking_curve` + `demand/booking_curve (Med)`. The Mediterranean booking-curve question literally appears as the [1] or [2] slot in every single setting. The actual question is a direct semantic match for this Med booking-curve theme — covered in **every** setting.

- Actual 2026-Q1: Q3 + Mediterranean: how much left to book, damage assessment...
- Verdict: **persona-pinned**

## james hardiman

**Actual 2026-Q1**: bookings recovery trajectory + Trifecta progress through 2027 (turning the corner).

V1 top-3 is **stable**: `Returns/ROIC + capital allocation` + `Yields/pricing` + `CapEx/newbuild economics (Icon)`. Trifecta + ROIC theme persistent. Auto **drifts** across K: K=10 leads with `fuel/hedging`, K=14 with `ROIC/capital`, K=20 with `pricing/yield`. The actual (bookings recovery + Trifecta) is partially covered by V1's persistent Perfecta/ROIC theme, but the "booking recovery" angle is missed by all 6.

- Actual 2026-Q1: bookings recovery trajectory + Trifecta progress through 2027...
- Verdict: **mixed** (V1 stable, Auto drifts; actual partially covered)

## lizzie dove

**Actual 2026-Q1**: Perfect Day Mexico opening cadence + private destination ramp 2028.

Top-3 **stable** across all 6 settings: `pricing/yield` + `costs` + `demand/booking_curve` (or yield cadence). Lizzie's predictions converge tightly on yield decomposition and Q2 cost timing, with no setting addressing the Perfect Day Mexico / private destination theme. The actual question is **not covered** in any of the 6 top-3.

- Actual 2026-Q1: Perfect Day Mexico opening cadence + private destination ramp 2028...
- Verdict: **persona-pinned** (top-3 stable, but pinned to wrong topic vs actual)

## robin farley

**Actual 2026-Q1**: (Q0) Mexico construction pause clarification; (Q1) 200bp Q2/Q3 impact + European yield math.

Top-3 **stable** across all 6 settings: `pricing/yield` + `demand/booking_curve (Med)` + `costs/fuel`. Auto K=10 [0] directly addresses "Q2 is roughly +0.2% with almost a 200bp regional/dry-dock headwind" — direct semantic match for Q1's actual question.

- Actual 2026-Q1: Mexico construction pause + 200bp Q2/Q3 yield math...
- Verdict: **persona-pinned** (stable + actual Q1 matched in Auto K=10)

## vince ciepiel

**Actual 2026-Q1**: new hardware (Star, Xcel, Paradise Island, RBC Santorini) contribution to yield growth.

Top-3 **stable** across all 6 settings: `pricing/yield` + `demand/booking_curve` + `new hardware/onboard`. The "new hardware contribution" theme explicitly appears as [2] in V1 K=10, V1 K=14, V1 K=20, and as [0] in Auto K=20 (decomposes yield by Icon/Legend/Utopia). Direct semantic match for actual in multiple settings.

- Actual 2026-Q1: new hardware (Star, Xcel, Paradise Island, RBC Santorini) yield contribution...
- Verdict: **persona-pinned** (stable + actual directly matched in 4+ settings)

## sharon zackfia

**Actual 2026-Q1**: cost focus — itinerary changes for 2027/2028 with higher fuel.

V1 top-3 **stable** but on different theme: `passenger/source-market mix` + `booking behavior by demographic` + `owned-destinations`. Auto top-3 **stable** but ALSO different: `pre-booking penetration` + `demographics/spend` + `AI/digital monetization`. V1 K=20 [1] is the only setting that includes "costs" (fuel reconciliation). Actual question (itinerary/fuel) is **missed by 5 of 6 settings**; V1 and Auto pin to wildly different topics — clearly distinct persona reads.

- Actual 2026-Q1: itinerary changes 2027/2028 in high-fuel environment + unit cost outlook...
- Verdict: **mixed** (within-persona stable; V1 and Auto pin completely different topics; actual missed)

## andrew didora

**Actual 2026-Q1**: cost — fuel hedging strategy in high-fuel environment + unit cost outlook.

V1 top-3 **stable** on bond-financing theme: `capital_structure/financing_choice` + `cost_of_financing` + `maturity_profile`. Auto top-3 **stable** on demand+fuel theme: `booking_curve` + `fuel_hedging/sensitivity` + Mediterranean. The actual (fuel hedging) is directly covered in **every Auto setting** ([1] or [2]) and V1 K=20 [2] (fuel/headwind reconciliation). V1 K=10/14 miss fuel entirely.

- Actual 2026-Q1: fuel hedging strategy in high-fuel environment + unit cost outlook...
- Verdict: **persona-pinned** (Auto stable on fuel; V1 stable on bond financing; both pinned, just to different topics — Auto matches actual)

## xian siew

**Actual 2026-Q1**: co-branded credit card + loyalty program impact on yield growth and margins.

Top-3 **stable** across all 6 settings: `demand/booking_curve (Med)` + `pricing/yield` + `costs/fuel`. Stable but **generic** — xian is a cold-start analyst using the aggregate-fallback persona, so all 6 settings produce the same generic Med/yield/fuel triple with no loyalty/credit-card theme. Actual **not covered** anywhere.

- Actual 2026-Q1: co-branded credit card + loyalty program impact on yields and margins...
- Verdict: **persona-pinned** (stable but generic; cold-start persona doesn't capture xian's actual focus)

## kevin kopelman

**Actual 2026-Q1**: North American customer behavior + reaction to higher airfares.

Top-3 **stable** across all 6 settings: same generic Med/yield/fuel triple as xian (kevin also uses cold-start fallback persona). Auto K=14 substitutes capital_return into [2] slot, otherwise identical structure. Actual (NA consumer behavior + airfares) **not covered** anywhere.

- Actual 2026-Q1: North American customer behavior + reaction to higher airfares...
- Verdict: **persona-pinned** (stable but generic; cold-start persona doesn't capture kevin's actual focus)

---

## Summary

**Verdict counts (n=11)**:
- `persona-pinned`: **9** (matthew, steven, brandt, lizzie, robin, vince, andrew, xian, kevin)
- `mixed`: **2** (james, sharon)
- `noise-dominated`: **0**

**Top-3 stability across K is the dominant pattern.** Within each persona source (V1 or Auto), the same 3 sub-topics recur at K=10, K=14, K=20 in 9 of 11 twins. This validates the hypothesis that **K only changes the tail of the candidate list, not the top picks**. Only james (Auto drifts) and sharon (V1 and Auto pin to different topics) show within-K drift.

**Actual-question coverage in top-3 is the BAD news**. Of 11 twins:
- Direct semantic match in top-3 (some setting): brandt, robin, vince, andrew (Auto), matthew (V1) → **5 / 11**
- Partial match: steven, james → **2 / 11**
- No coverage in any setting's top-3: lizzie, sharon, xian, kevin → **4 / 11**

The 4 "no coverage" twins split into: 2 cold-start (xian, kevin — expected, persona is generic fallback) + 2 returning twins (lizzie asked about Perfect Day Mexico — persona didn't predict it; sharon asked about itinerary/fuel cost discipline — Auto persona drifted to AI/digital, V1 to passenger demographics).

**V1 vs Auto pinning patterns**:
- Same topic: matthew, brandt, robin, vince (Auto K=20 pins same yield decomp as V1)
- Different topic: andrew (V1=financing, Auto=fuel), sharon (V1=passenger mix, Auto=AI/digital), james (V1=ROIC, Auto=fuel→ROIC→yield drift)

**Recommendation**: the auto-discovery loop's persona refinements **do not produce more accurate predictions on average** but they do **shift the top-3 stable attractor**. For sharon, andrew, james the V1 and Auto personas pin different topics. Whether the auto-shifted topic is closer to the actual depends on the analyst — Auto helps andrew (fuel matches actual) and hurts matthew (drops Trifecta which matches actual).
