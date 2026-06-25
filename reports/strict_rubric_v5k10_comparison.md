4# Strict Rubric vs Old Rubric — v5 K=10 sim_1 baseline (110 pool)

## Aggregate

| Metric | OLD (`b4_eval.md`) | STRICT (`b4_eval_strict.md`) | Δ |
|---|---|---|---|
| mini cov (5 runs) | 0.727 | **0.583** | **−14.4pp** |
| mini prec | 0.787 | 0.698 | −8.9pp |
| gpt-5 cov (5 vs 2 runs) | 0.733 | 0.625 | −10.8pp |
| gpt-5 prec | 0.449 | 0.477 | +2.8pp |

Strict 让 cov 降 11–14pp (substitution test catches stretches). mini-gpt-5 prec gap 从 34pp 缩到 22pp.

### Per-run breakdown (STRICT)
- **mini 5 runs cov**: [0.583, 0.667, 0.500, 0.583, 0.583] → mean 0.583, range [0.50, 0.67]
- **gpt-5 2 runs cov**: [0.583, 0.667] → mean 0.625, range [0.58, 0.67]
- mini/gpt-5 cov 在 sample noise 内一致

---

## 10 Per-Candidate Examples — Old Score vs New Score

Each block shows: **predicted question** (full text), **best-matched actual** (full text), avg mini score under OLD vs STRICT rubric, my analysis.

---

### A. Big demotions (strict caught old stretches)

5#### 1. `sharon_zackfia-pred-4` — Δ = **3.2 → 0.6** (−2.6)

**PREDICTED** (sharon zackfia):
> "Hi — on the digital/AI point: you've said mobile monthly active users are 5x 2019 and app adoption is >90%, and you're embedding AI across yield mgmt — can you quantify the incremental APD or onboard spend lift attributable to those investments today, and roughly when we should expect bigger benefits to flow through?"

**BEST-MATCHED ACTUAL** (matthew boss):
> "Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?"

**Why OLD gave 3**: shared "yield/growth" vocabulary; mgmt prepared remarks mentioned both AI and durable growth.
**Why STRICT gives 0–1**: substitution test FAILS — answering "AI uplift in bps" doesn't tell listener about "durable multi-year growth vs pre-pandemic." Different sub-topics under strict.

**Verdict**: STRICT is right.

---

#### 2. `vince_ciepiel-pred-9` — Δ = **3.0 → 0.6** (−2.4)

**PREDICTED** (vince ciepiel):
> "Technology/AI attribution: you emphasized the AI/digital flywheel and said earlier engagement has driven more pre-cruise booking — what is the AI-attributable APD lift today, and how should we model the share of the 2026 yield range that comes from these tools versus traditional drivers?"

**BEST-MATCHED ACTUAL** (vince's own actual):
> "Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star, Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like-for-Like impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume?"

**OLD**: 3 (both about yield growth).
**STRICT**: 0.6 — vince's actual asks **new hardware + regional Europe**, predicted asks **AI/digital attribution**. Substitution test FAILS.

**Verdict**: STRICT correct. OLD let "both about yield" become 3 even though the asks are completely different drivers.

---

#### 3. `kevin_kopelman-pred-6` — Δ = **2.8 → 0.6** (−2.2)

**PREDICTED** (kevin kopelman):
> "Hi, good morning — Legend of the Seas is in a very strong book position with prices reportedly higher than Icon and Star — can you give an APD comparison (Legend vs. fleet average) and the expected incremental EPS or ROIC contribution from the Icon series and new Beach Clubs over the next two years?"

**BEST-MATCHED ACTUAL** (vince ciepiel, the same yield-outlook actual quoted above):
> "Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star, Xcel contribution, Paradise Island, RBC Santorini, ..."

**OLD**: 2.8.
**STRICT**: 0.6 — kevin asks specific Legend-class APD + ROIC; vince asks broad new-hardware contribution to yields + regional Europe. Same broad area (new hardware), totally different ask shape (unit-economics vs yield-mix decomp).

**Verdict**: STRICT correct.

---

#### 4. `andrew_didora-pred-0` — Δ = **2.0 → 0.0** (−2.0)

**PREDICTED** (andrew didora):
> "Hey, good morning. On the $2.5 billion investment-grade bond you priced this quarter — first, can you walk us through the rationale and structure, and the future financing flexibility this creates given your liquidity position and the upcoming Icon orders?"

**BEST-MATCHED ACTUAL** (no good match found — evaluator picked andrew's own actual on hedging + NCC ex-fuel):
> "Hi, good morning, everyone. Two quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range?"

**OLD**: 2 (broad "financials" overlap).
**STRICT**: 0 — bond financing vs hedging/cost is **different sub-area entirely**. No actual asks about bonds in 2026-Q1.

**Verdict**: STRICT correct — there is no actual the bond question covers.

---

#### 5. `lizzie_dove-pred-5` — Δ = **2.2 → 0.6** (−1.6)

**PREDICTED** (lizzie dove):
> "Hi there. Thanks for taking the question. You said Legend of the Seas is 'in a very strong book position with prices higher than Icon/Star' — can you quantify the APD premium vs. Icon/Star and the ROIC contribution Legend redeployment will give in the Caribbean from November?"

**BEST-MATCHED ACTUAL** (vince ciepiel, yield outlook again):
> "Thanks. Just wanted to dig a little bit more into yield outlook for the year. ..."

**OLD**: 2.2.
**STRICT**: 0.6 — Same as #3 (Legend-specific vs broad new-hardware yield).

**Verdict**: STRICT correct.

---

### B. Stable (both rubrics agree — substantive cover)

#### 6. `robin_farley-pred-1` — old 3.2, **strict 3.2** (no change)

**PREDICTED** (robin farley):
> "Okay — on yield guidance and the regional impact, two parts: 1) your full-year Net Yield guide is 1.5%–2.5% — can you split the range by Med vs Caribbean vs Mexico (bps each), and 2) given the 200bps Q2/Q3 European headwind, what does the full-year ex-Med yield look like, and is the Med headwind expected to fully reverse in 2027?"

**BEST-MATCHED ACTUAL** (robin's own Q2):
> "Great. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a mid-single digit sort of shift in where you had expected European yields to come, to come in this year. Is it fair to assume that you would kind of fully expect that to come back in 2027 when we're kind of thinking ahead to, you know, the impact this year being kind of, you know, not necessarily coming out of next year? Just help us to size that. Thank you."

**Both rubrics give 3**: robin's actual asks about size of Euro yield delta + 2027 recovery; predicted covers regional yield decomp incl Med + asks if 2027 reverses. Substitution test passes.

**Verdict**: ✓ True substantive cover.

---

#### 7. `matthew_boss-pred-0` — old 3.0, **strict 3.0** (no change)

**PREDICTED** (matthew boss):
> "Great, thanks, and congrats on another nice quarter. Maybe to start on demand — you said booked load factor is within historical ranges and APD is at record levels while Q1 net yields were +2% and full-year guide is 1.5%-2.5%. Can you help size the durable underlying demand drivers — what gives confidence in the 1.5%-2.5% absent the Mediterranean impact, and how much of that came from new commercial/AI tools versus traditional booking strength?"

**BEST-MATCHED ACTUAL** (matthew's own):
> "Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?"

**Both rubrics 3.0**: predicted covers demand drivers + 1.5-2.5% durability question, matches actual's "drivers of durable multi-year growth". Substitution passes.

**Verdict**: ✓ True cover.

---

#### 8. `matthew_boss-pred-8` — old 3.4, **strict 3.4** (no change)

**PREDICTED** (matthew boss):
> "On destinations — Beach Club Santorini demand is strong and Perfect Day Mexico/Cozumel are coming in late 2027/early 2028 — can you size the cumulative APD/yield uplift you expect from your owned destinations over the next 3 years and how the Western Caribbean economics rank versus the Med?"

**BEST-MATCHED ACTUAL** (lizzie dove):
> "Hi. Good morning. Thanks for taking the question. I was wondering if you could maybe give us a refresh on Perfect Day Mexico. You mentioned it's opening late 2027, ramping 2028. Could you maybe share some more details on the cadence of that ramp? You know, just bigger picture, your latest thinking around the long-term, you know, structural yield growth opportunity there in the Western Caribbean market and particularly around, you know, the Galveston, Texas penetration opportunity."

**Both rubrics 3.4**: matthew's prediction covers Perfect Day Mexico timing + Western Caribbean APD ranking — matches lizzie's ramp + Western Caribbean question almost exactly.

**Verdict**: ✓ Strong substantive cover — near 4.

---

### C. Boundary cases (modest demotion)

#### 9. `robin_farley-pred-9` — Δ = **3.0 → 1.6** (−1.4)

**PREDICTED** (robin farley):
> "Okay — capacity mix and Legend of the Seas redeployment: 1) with 6.7% capacity growth and Legend entering the Caribbean in November, can you quantify the incremental APD/yield benefit you expect from that redeployment in FY-2026 ($/APD or bps)? 2) Given elevated industry capacity in the Caribbean, what actions (itinerary mix, length, pricing levers) are you taking to protect yields? Thanks."

**BEST-MATCHED ACTUAL** (matthew boss, broad durable growth — same as 6/7):
> "Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, ..."

**OLD**: 3 (both touch capacity/growth).
**STRICT**: 1.6 — robin asks tactical Legend-specific quantification + Caribbean defensive pricing; matthew asks broad multi-year durability narrative. Same broad area, different sub-aspect (tactical vs strategic) + different ask shape (quantitative vs qualitative).

**Verdict**: STRICT right — these don't substitute. Score lands between 1 ("broad area only") and 2 ("shared sub-topic, ask different") — borderline.

---

#### 10. `matthew_boss-pred-9` — Δ = **3.2 → 2.0** (−1.2)

**PREDICTED** (matthew boss):
> "Finally, you said you're trying to 'win a greater share of the large and growing vacation market' — maybe help us frame the KPI: what specific metrics should we watch for market-share gains versus land-based alternatives (booked share, NPS-driven conversion, repeat rates), and realistically how many share points of the TAM can you target to capture over the next 3 years — what inning are we in on TAM capture?"

**BEST-MATCHED ACTUAL** (matthew's own — durable growth narrative):
> "Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?"

**OLD**: 3.2 (both about durable growth).
**STRICT**: 2 — predicted asks for KPIs + TAM share quantification; actual asks for narrative on what makes growth durable. Same sub-topic (multi-year growth), different ask shape (quantitative KPIs vs qualitative narrative). Substitution test fails — listener of TAM-KPI answer wouldn't get the "durable drivers narrative" matthew asked for.

**Verdict**: STRICT correctly distinguishes ask-shape mismatch.

---

## Summary

- **5/10**: big demotion — strict caught real stretches (AI attribution, bond, Legend-specific ROIC). All correct.
- **3/10**: stable — both rubrics agree on substantive cover (yield decomp, demand setup, Beach Club destinations).
- **2/10**: boundary — strict distinguishes "shared topic, different ask shape" → demotes from 3 to 1.6–2.

## Recommendation

Ship STRICT rubric for production reporting; aggregate cov drops 10–14pp (more honest), per-candidate scores defensible. For side-by-side reporting, show both `cov_strict` (conservative) and `cov_old` (lenient) so reviewers see the gap.

---

**Note on mini vs gpt-5 under strict** (user's check):
- mini cov 0.583 vs gpt-5 cov 0.625 → within sample noise (gpt-5 only 2 runs hit [0.58, 0.67]; mini 5 runs span [0.50, 0.67])
- mini prec 0.698 vs gpt-5 prec 0.477 → mini systematically more lenient on "useful=True", same pattern as old rubric (was 0.787 vs 0.449)
- Strict **narrowed** the mini-gpt-5 prec gap from 34pp → 22pp (not widened)
- To rule out gpt-5 sample noise, recommend running 3 more gpt-5 strict runs (cost ~$0.50)

**Data sources**
- Strict: `data_auto/batch/tracker_strict_v5k10_{mini,gpt5}.json`
- Old: `data_auto/final_eval_10q_v5/variance_batch/{gpt_5_mini,gpt_5}/run_*/b4.json`
- Prompts: `prompts/b4_eval.md` (old) vs `prompts/b4_eval_strict.md` (new)
