# B4 Rubric Quality Review — 20 Examples per Score (gpt-5 Evaluator)

## Rubric Reminder

| Score | Definition |
|---|---|
| 0 | no meaningful relation |
| 1 | same broad business area only |
| 2 | partial theme match but wrong trigger or different ask |
| 3 | substantially similar question target with some phrasing/granularity differences |
| 4 | very close match / would plausibly substitute |
| **covered/useful** | True if score ≥ 3 |

## Methodology

- **Source**: gpt-5 B4 `predicted_precision[]` entries from v5 K=10 baseline pool evaluations (5 fresh sims, sync + batch runs).
- **Selection**: 20 unique candidate questions per score level (1, 2, 3), each paired with the actual question the evaluator deemed best-match for it.
- **For each example**: show predicted question (simulator output), actual question (the holdout 2026-Q1 Q&A), evaluator's reasoning, and my assessment of whether the score is reasonable.

---


## Score 3 Examples (n=20)

**Rubric says**: substantially similar question target; phrasing/granularity differs. This is the lowest score that counts as `covered/useful=True`.

### 3.1 — kevin kopelman → sharon zackfia (src: baseline_s5)

**Predicted** (kevin kopelman): Hi — Q2 Net Cruise Costs ex‑fuel are now expected up ~4.6%–5.1% with almost 400bp of headwinds from dry docks and crew travel — how much of that increase is timing (one‑time/dry‑dock) versus permanent underlying cost inflation, and what cadence should we expect in H2?

**Actual** (sharon zackfia): Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Evaluator reasoning**: Timing vs structural Q2 cost inflation aligns with cost discussion.

---

### 3.2 — sharon zackfia → sharon zackfia (src: baseline_s5)

**Predicted** (sharon zackfia): Hi, good morning — on Q2 cadence you flagged ~200bps yield headwind and almost 400bps of cost headwinds (dry docks, crew travel); can you provide a short breakout (bps or $) of the biggest cost items in Q2 (dry docks vs crew travel vs other) and which of those you view as timing/transitory versus structural?

**Actual** (sharon zackfia): Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Evaluator reasoning**: Breakdown of Q2 cost headwinds aligns with cost discussion.

---

### 3.3 — vince ciepiel → andrew didora (src: baseline_s5)

**Predicted** (vince ciepiel): A quick one on fuel/hedging: you mentioned roughly 60% hedged for 2026 and a $0.62 per‑share headwind from fuel for the year (and that using the forward curve would be ~4% lower). Can you confirm the exact hedge coverage and strike/pricing bands for the remaining 2026 volume, give a sensitivity ($/share) to a $10/bbl move in Brent, and comment on whether your hedging posture changes for 2027 given current volatility? Thanks.

**Actual** (andrew didora): Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Evaluator reasoning**: Hedge coverage/strikes and sensitivity match hedging discussion.

---

### 3.4 — brandt montour → vince ciepiel (src: baseline_s2)

**Predicted** (brandt montour): Hey, good morning — thanks. Quick one on yields: you reported Net Yields up 2% in Q1 and are guiding 1.5%–2.5% for the year; just to clarify, can you split that Q1 2% into ticket vs onboard contribution and tell us how much was mix (Europe/Med vs Caribbean) versus pure price? And as a follow-up, relative to 2019, what percent of the pre‑COVID APD gap have you recovered today?

**Actual** (vince ciepiel): Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**Evaluator reasoning**: Q1 yield split and mix context generally aligns with actual yield source discussion.

---

### 3.5 — steven wieczynski → lizzie dove (src: baseline_s2)

**Predicted** (steven wieczynski): Hey, guys. Good morning. On the private‑destination and Beach Club rollouts — you called out openings and ramp timing for Perfect Day Mexico/Costa Maya and Royal Beach Club Cozumel (early 2028) and said these are accretive to yield; can you quantify the expected incremental yield or EBITDA per pax for Perfect Day Mexico and the Beach Clubs at stabilized run‑rate and the capex cadence through the ramp period?

**Actual** (lizzie dove): Hi. Good morning. Thanks for taking the question. I was wondering if you could maybe give us a refresh on Perfect Day Mexico. You mentioned it's opening late 2027, ramping 2028. Could you maybe share some more details on the cadence of that ramp? You know, just bigger picture, your latest thinking around the long-term, you know, structural yield growth opportunity there in the Western Caribbean market and particularly around, you know, the Galveston, Texas penetration opportunity.

**Evaluator reasoning**: Quantifies yield/EBITDA uplift and capex cadence for private destinations.

---

### 3.6 — robin farley → andrew didora (src: baseline_s4)

**Predicted** (robin farley): Great — fuel sensitivity question: you noted $1.35bn of fuel expense, ~59% hedged for the remainder and that current spot implies a ~$0.62 EPS headwind — can you give the EPS sensitivity per $10/bbl move in bunker for 2026, how much of the $0.62 would reverse if the forward curve held, and whether you have appetite/opportunity to increase hedges at current levels? Thanks.

**Actual** (andrew didora): Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Evaluator reasoning**: Fuel sensitivity and hedge appetite tie directly to hedging approach in a high fuel environment.

---

### 3.7 — kevin kopelman → james hardiman (src: baseline_s2)

**Predicted** (kevin kopelman): Good morning — can you quantify your current booked position for the full year in terms of booked load factor and APD, and how much of 2026 capacity (or revenue) is effectively locked at current prices versus close‑in sales?

**Actual** (james hardiman): Good morning, thanks for taking my questions. I wanted to sort of zoom in on the idea that we're turning the corner. Obviously, you know, the weeks following the initial geopolitical disruption were probably the worst, but maybe some indication of where we stand today in terms of the booking trajectory versus where we were in February before a lot of this started. I don't know if we're fully back or we're just heading in that direction. As we think about sort of the 2Q and 3Q, we're saying that's most pronounced. I'm just curious if that's because those are what's next or whether consumers are

**Evaluator reasoning**: Booked position and locked revenue relate to trajectory vs February and near-term periods.

---

### 3.8 — andrew didora → andrew didora (src: baseline_s3)

**Predicted** (andrew didora): You said you're roughly 60% hedged for 2026 and guidance is based on spot, and that forwards would make fuel expense meaningfully lower — what's your guiding framework for incremental hedging (i.e., why stop at ~60%), and under what market relationship between spot and forward would you decide to layer further hedges?

**Actual** (andrew didora): Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Evaluator reasoning**: Framework for layering hedges in a high fuel environment matches the hedging portion of the actual.

---

### 3.9 — james hardiman → vince ciepiel (src: baseline_s5)

**Predicted** (james hardiman): Hey, good morning — congrats on the quarter. Net Yield guide for 2026 is 1.5%–2.5%; can you walk me through a like‑for‑like decomposition of that range — i.e., how much is (a) ticket/APD re‑pricing on existing itineraries, (b) ticket mix and deployment changes (including Legend/Icon redeployments), and (c) discrete contributions from new products and private destinations (Royal Beach Club/Perfect Day)? If you can put dollar or bps targets on each bucket for 2026, that would be helpful.

**Actual** (vince ciepiel): Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**Evaluator reasoning**: Explicitly breaks out new products/private destinations, as in the actual.

---

### 3.10 — vince ciepiel → brandt montour (src: baseline_s1)

**Predicted** (vince ciepiel): Mediterranean and West Coast book disruption: you said Med bookings moderated for a few weeks and have started rebounding, and West Coast Mexico also moderated — can you quantify the peak impact to APD and load factor in Q2/Q3 from those disruptions, whether you saw cancellations or simple slower new bookings, and how much of that demand is re‑timed into other itineraries versus lost? Thanks.

**Actual** (brandt montour): Great. Thanks for taking my question. I just wanted to circle back on the third quarter and the Med, and just maybe if you could put a bit of a finer point on it. You know, how much do you have left to book at this point in the year? How much damage do you think was done over the last few weeks? What are you sort of baking into your forward guidance in terms of how the conflict plays out and how bookings play out from here?

**Evaluator reasoning**: Quantifies Med/W. Coast disruption on APD/load, cancellations vs re-timing.

---

### 3.11 — matthew boss → matthew boss (src: baseline_s1)

**Predicted** (matthew boss): Finally, you said you’re trying to ‘win a greater share of the large and growing vacation market’ — maybe help us frame the KPI: what specific metrics should we watch for market‑share gains versus land‑based alternatives (booked share, NPS‑driven conversion, repeat rates), and realistically how many share points of the TAM can you target to capture over the next 3 years — what inning are we in on TAM capture?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: TAM/share and KPIs speak to durable multi-year growth relative to broader vacation market.

---

### 3.12 — brandt montour → lizzie dove (src: baseline_s4)

**Predicted** (brandt montour): Hey, congrats on the new Beach Club openings — quick question on private‑destination economics: you said Santorini demand is very strong and Cozumel/Perfect Day Mexico are coming online in 2027–28 — can you give an APD or yield uplift and incremental margin you’re seeing from Royal Beach Club Santorini, and the run‑rate contribution you expect for Perfect Day Mexico and Cozumel in the first 12–24 months after opening?

**Actual** (lizzie dove): Hi. Good morning. Thanks for taking the question. I was wondering if you could maybe give us a refresh on Perfect Day Mexico. You mentioned it's opening late 2027, ramping 2028. Could you maybe share some more details on the cadence of that ramp? You know, just bigger picture, your latest thinking around the long-term, you know, structural yield growth opportunity there in the Western Caribbean market and particularly around, you know, the Galveston, Texas penetration opportunity.

**Evaluator reasoning**: Requests APD uplift and run-rate contribution/ramp for destinations, consistent with the long-term structural yield opportunity inquiry.

---

### 3.13 — sharon zackfia → lizzie dove (src: baseline_s1)

**Predicted** (sharon zackfia): You highlighted Royal Beach Club Santorini and Paradise Island, and that owned destinations are accretive to yield — can you help quantify the premium you’re seeing at Beach Clubs (Santorini/Paradise) versus typical shore excursions today, and the ramp profile and assumed yield uplift you’re modeling for Perfect Day Mexico, Costa Maya and Beach Club Cozumel into 2027–28?

**Actual** (lizzie dove): Hi. Good morning. Thanks for taking the question. I was wondering if you could maybe give us a refresh on Perfect Day Mexico. You mentioned it's opening late 2027, ramping 2028. Could you maybe share some more details on the cadence of that ramp? You know, just bigger picture, your latest thinking around the long-term, you know, structural yield growth opportunity there in the Western Caribbean market and particularly around, you know, the Galveston, Texas penetration opportunity.

**Evaluator reasoning**: Beach Club premium and ramp tie to destination ramp economics.

---

### 3.14 — brandt montour → robin farley (src: baseline_s3)

**Predicted** (brandt montour): Hey — on the Med and West Mexico softness you referenced: can you quantify how much of the reduction in your January implied yield trajectory is driven by (a) lost bookings (units) versus (b) price/airfare‑driven lower ARPD, and what percentage of the 1.5%-2.5% full‑year yield range reduction is attributable to those regions specifically for Q2/Q3?

**Actual** (robin farley): Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a mid-single digit sort of shift in where you had expected European yields to come, to come in this year. Is it fair to assume that you would kind of fully expect that to come back in 2027 when we're kind of thinking ahead to, you know, the impact this year being kind of, you know, not necessarily coming out of next year? Just help us to size that. Thank you.

**Evaluator reasoning**: Quantifies yield guide reduction from Med/Mex impacts; aligns with size/timing of Euro headwinds.

---

### 3.15 — james hardiman → matthew boss (src: baseline_s3)

**Predicted** (james hardiman): You’ve reiterated the Perfecta program target of 20% compound adjusted EPS through 2027 and a ROIC in the high teens — can you break down the key contributors to that target (percent from yields, percent from net cruise cost efficiencies, percent from JV improvement and percent from new products/destinations)?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Perfecta levers map to durable, multi-year growth.

---

### 3.16 — vince ciepiel → matthew boss (src: baseline_s4)

**Predicted** (vince ciepiel): Capacity for the year is up 6.7% and you continue to order Icon ships — how should we think about industry supply versus Royal Caribbean's own deployment over the next 24–36 months, and does the current order book (yours and competitors') meaningfully change your confidence in sustaining mid‑single to low‑double digit yield expansion beyond 2026?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Industry supply vs deployment and sustained yields support durable growth.

---

### 3.17 — vince ciepiel → matthew boss (src: baseline_s1)

**Predicted** (vince ciepiel): Perfecta and ROIC bridge: you reiterated the Perfecta target of 20% CAGR to 2027 and a high‑teens ROIC — can you give us a bridge showing the relative contribution to that target from yield improvement, net cruise cost savings (ex‑fuel), JV upside, and incremental returns from private destinations/Beach Clubs? And how much of the margin lift is already embedded in the $17.10–$17.50 EPS guide? Thanks.

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Perfecta EPS/ROIC bridge ties to multi-year growth drivers.

---

### 3.18 — lizzie dove → vince ciepiel (src: baseline_s4)

**Predicted** (lizzie dove): Hi there. Thanks for taking the question. You called out Legend of the Seas being in a very strong book with prices higher than Icon and Star — can you quantify how much of your APD improvement and Net Yield upside is explicitly driven by new‑ship pricing (Icon/Legend) versus like‑for‑like price/mix, and is that premium sustainable as you redeploy Icon‑class capacity into the Caribbean? Got it. Thank you.

**Actual** (vince ciepiel): Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**Evaluator reasoning**: Sustainability of new-ship pricing premium aligns with hardware contribution to yields.

---

### 3.19 — kevin kopelman → vince ciepiel (src: baseline_s2)

**Predicted** (kevin kopelman): Hi — you said Legend of the Seas is in a very strong book position with prices higher than Icon and Star — can you give an APD comparison (Legend vs. fleet average) and the expected incremental EPS or ROIC contribution from the Icon series and new Beach Clubs over the next two years?

**Actual** (vince ciepiel): Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**Evaluator reasoning**: Legend vs fleet APD and Icon/Beach Club contribution match new asset contribution to yields.

---

### 3.20 — robin farley → brandt montour (src: baseline_s1)

**Predicted** (robin farley): Great — on bookings and mix: 1) you noted booked load factor is within historical ranges and APD/record prices are high — can you give current booked APD and load factor versus the comparable 2019 booking point (% or $)? 2) Are you having to trade occupancy for onboard spend in any itineraries, or are both lifting — please quantify the marginal onboard revenue per incremental point of occupancy if possible. Thanks.

**Actual** (brandt montour): Great. Thanks for taking my question. I just wanted to circle back on the third quarter and the Med, and just maybe if you could put a bit of a finer point on it. You know, how much do you have left to book at this point in the year? How much damage do you think was done over the last few weeks? What are you sort of baking into your forward guidance in terms of how the conflict plays out and how bookings play out from here?

**Evaluator reasoning**: Booked APD/load and occupancy vs onboard spend relate to how much is left to book/damage assessment.

---


## Score 2 Examples (n=20)

**Rubric says**: partial theme match but wrong trigger or different ask. Counts as `False` (uncovered).

### 2.1 — sharon zackfia → sharon zackfia (src: baseline_s1)

**Predicted** (sharon zackfia): On costs and cadence: Q2 Net Cruise Costs ex-fuel are guided to be up ~4.6%–5.1% driven by ~400bps of headwinds from dry docks and crew travel — can you quantify the stock-to-flow of those timing items (i.e., how much of the quarterly step-up is genuinely structural vs. timing that reverses later in the year) and the implied $ or bps improvement you expect in back-half cost dynamics?

**Actual** (sharon zackfia): Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Evaluator reasoning**: Cost timing vs structure overlaps only partly with itinerary/fuel deferrals.

---

### 2.2 — matthew boss → vince ciepiel (src: baseline_s2)

**Predicted** (matthew boss): Great, thanks — on Icon/Legend economics: you said Legend of the Seas is in a 'very strong book position' with prices higher than Icon and Star; can you quantify the premium APD you're seeing on Legend relative to prior Icon and Star launches and the expected incremental margin/APD contribution as you redeploy that ship into the Caribbean in November?

**Actual** (vince ciepiel): Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**Evaluator reasoning**: Legend pricing relates to new hardware contribution but is narrower.

---

### 2.3 — matthew boss → matthew boss (src: baseline_s2)

**Predicted** (matthew boss): Great, thanks — on technology and yield management: you highlighted a unified intelligence layer and AI deployment; maybe could you elaborate quantitatively — what incremental APCD or Net Yield lift have you measured from the yield/AI tools to date, and how should we think about the timing and magnitude of that benefit as you scale across the fleet?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: AI/yield tool uplift is a long-term driver topic but actual asks broader durable growth vs pre-pandemic, not specific AI quantification.

---

### 2.4 — steven wieczynski → sharon zackfia (src: baseline_s5)

**Predicted** (steven wieczynski): Hey, guys. Good morning. On costs cadence — you said Net Cruise Costs ex‑fuel are roughly flat for the year but Q2 is up 4.6%–5.1% driven by dry docks and crew travel; how much of that Q2 increase is timing versus structural (e.g., recurring wage or benefits), and when should we expect APCD to normalize to your 'flat' full‑year view?

**Actual** (sharon zackfia): Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Evaluator reasoning**: Cost cadence overlap is partial; actual focuses on itinerary changes/deferrals rather than cost phasing.

---

### 2.5 — matthew boss → matthew boss (src: baseline_s5)

**Predicted** (matthew boss): Great, thanks — you said the Caribbean is 57% of deployment and that yields should be positive despite elevated industry capacity; can you help us parse how much of the Caribbean outperformance is share capture (demand shift) versus pure pricing, and what gives you confidence on sustained pricing in a market with elevated supply— any measured elasticity you can point to? Thanks.

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Caribbean elasticity is a subset of broader durable growth; partial overlap.

---

### 2.6 — steven wieczynski → matthew boss (src: baseline_s2)

**Predicted** (steven wieczynski): Hey, guys. Good morning. Quick one on the Perfecta performance program — you reiterated a 20% compound annual EPS target through 2027 and a ROIC in the high teens; can you walk us through a numeric decomposition of that 20% CAGR (how much is coming from yields vs cost savings vs mix/JV contributions vs buybacks) and confirm whether that target assumes the remaining $1 billion of buyback authorization or is purely operational? Thanks, guys.

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Perfecta EPS CAGR breakdown overlaps with long-term growth but not the specific pre/post-pandemic positioning.

---

### 2.7 — sharon zackfia → xian siew (src: baseline_s1)

**Predicted** (sharon zackfia): Can I ask a quick follow-up on demographics: you said you saw an increase in millennials and younger guests in Q1 — what share of the pre-cruise bookings and the increase in spend-per-night is coming from those younger cohorts versus older cohorts, and are younger guests booking earlier or buying different types of items (excursions, F&B, upgrades)?

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: Touches cohort effects but actual focuses broadly on repeat/loyalty impacts.

---

### 2.8 — brandt montour → matthew boss (src: baseline_s3)

**Predicted** (brandt montour): Hey — on your tech/AI comment: you noted mobile MAUs 5x 2019 and that >50% of onboard revenue is booked pre‑cruise with 5+ items per pre‑booking. Can you quantify the impact of these digital/AI initiatives on conversion and APD — e.g., what percent of the APD improvement or spend per passenger increase since 2019 is attributable to pre‑cruise personalization versus other factors?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Tech/AI attribution is tangential to the broader durable growth framing.

---

### 2.9 — brandt montour → sharon zackfia (src: baseline_s2)

**Predicted** (brandt montour): Good morning — a two‑part on costs/drydocks: you called out Q2 Net Cruise Costs ex‑fuel up 4.6%–5.1% with almost 400bps of headwinds tied to additional dry dock days and cadence — can you put that dry‑dock impact in $ per cruise day (or $ per passenger night) and separately quantify how much of the year‑over‑year improvement you’re attributing to Perfecta/efficiency programs versus timing?

**Actual** (sharon zackfia): Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Evaluator reasoning**: Cost cadence overlap; actual centers on itinerary/fuel responses.

---

### 2.10 — robin farley → xian siew (src: baseline_s3)

**Predicted** (robin farley): Great — bookings and onboard mix given the younger guest shift. You said Q1 saw more millennials/younger guests and that >50% of onboard revenue is now booked pre‑cruise with ~5 items per booking. (1) Are younger guests changing onboard spend composition (F&B, experiences, excursions) and APU/APD? Please quantify incrementally. (2) How much of Net Yield growth is directly attributable to pre‑cruise capture versus higher onboard conversion on board? Thanks.

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: Younger guest spend composition is adjacent to loyalty-driven yield effects.

---

### 2.11 — matthew boss → matthew boss (src: baseline_s5)

**Predicted** (matthew boss): Great, thanks — you highlighted AI and a unified intelligence layer and said digital penetration has more than doubled and app MAUs are 5x 2019; maybe be specific on which revenue levers are already AI‑driven (dynamic ticket pricing, ancillary personalization, bundling, close‑in optimization), what bps of yield or APCD uplift you can point to today from those deployments, and how we should phase additional yield benefits into our model over 12–24 months? Thanks.

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: AI/digital uplift is a component of growth but the actual asks broader multi-year setup vs pre-pandemic.

---

### 2.12 — sharon zackfia → sharon zackfia (src: baseline_s2)

**Predicted** (sharon zackfia): Net Cruise Costs ex-fuel are roughly flat for the year but Q2 costs are expected up 4.6%-5.1% — can you walk through the cadence (dry dock timing, crew travel, other items) in dollars per APC or per pax-night terms, and how much of the year-over-year cost improvement is structural versus timing-related?

**Actual** (sharon zackfia): Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Evaluator reasoning**: Cost cadence overlap; actual asks about itinerary/fuel changes and deferrals.

---

### 2.13 — kevin kopelman → andrew didora (src: baseline_s3)

**Predicted** (kevin kopelman): Hi, thanks — you noted Q2 Net Cruise Costs ex‑fuel up ~4.6–5.1% and that first‑half cost growth is higher due to dry docks — can you quantify the incremental EBITDA drag from the additional dry‑dock days and the timing/size of the underlying run‑rate savings you expect in H2?

**Actual** (andrew didora): Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Evaluator reasoning**: Dry dock EBITDA drag and H2 savings timing only partially overlap.

---

### 2.14 — james hardiman → vince ciepiel (src: baseline_s4)

**Predicted** (james hardiman): Jason, you said Legend of the Seas is in a very strong book position with prices higher than Icon and Star — can you quantify the APD and onboard spend delta versus Icon/Star and comment on how that should inform our modeling of incremental ROIC for the Icon platform (given the new Icon 6 and 7 orders)?

**Actual** (vince ciepiel): Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**Evaluator reasoning**: Icon/Legend deltas are part of yield mix; actual also covers regional Europe assumption.

---

### 2.15 — robin farley → xian siew (src: baseline_s1)

**Predicted** (robin farley): Great — on commercial/AI and onboard revenue: 1) you said >50% of onboard revenue is booked pre‑cruise and five items per booking with 70% pre‑cruise penetration — how much of the year‑over‑year APD and onboard spend improvement is driven by pre‑cruise conversion versus onboard upsell (please give $/guest or % split)? 2) How much of your Perfecta EPS roadmap (20% CAGR to 2027) is explicitly tied to these digital/commercial initiatives versus cost reductions? Thanks.

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: Onboard pre-cruise/AI uplift is adjacent but not the loyalty/repeat focus.

---

### 2.16 — sharon zackfia → vince ciepiel (src: baseline_s2)

**Predicted** (sharon zackfia): Hi. Good morning. First — you said today that more than half of onboard revenue is now booked before guests step on board and that Net Yield grew 2% this quarter — can you help quantify how much of that yield improvement was driven by ticket versus onboard revenue (in percentage points or as a share of the 2%), and can I ask a quick follow-up on whether that split is shifting as more purchases move pre-cruise?

**Actual** (vince ciepiel): Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**Evaluator reasoning**: Ticket vs onboard split overlaps yield theme but not the full decomp asked.

---

### 2.17 — vince ciepiel → brandt montour (src: baseline_s5)

**Predicted** (vince ciepiel): On the Mediterranean and West Coast Mexico commentary — you said bookings moderated for a few weeks and are now rebounding; how much of the reduction in your Net Yield outlook versus January is attributable to those two regions in aggregate (bps or $/APD), what's the current booking pace versus the same point in 2019 and versus January, and what gives you confidence that the recent rebound will fully recover the lost high‑yield inventory? Thanks.

**Actual** (brandt montour): Great. Thanks for taking my question. I just wanted to circle back on the third quarter and the Med, and just maybe if you could put a bit of a finer point on it. You know, how much do you have left to book at this point in the year? How much damage do you think was done over the last few weeks? What are you sort of baking into your forward guidance in terms of how the conflict plays out and how bookings play out from here?

**Evaluator reasoning**: Focus on change vs January; actual asked level/trajectory not the delta to prior guide.

---

### 2.18 — vince ciepiel → xian siew (src: baseline_s3)

**Predicted** (vince ciepiel): You mentioned more than half of onboard revenue is now booked pre‑cruise and five items per booking — can you quantify how much of the year‑over‑year onboard revenue growth in Q1 came from pre‑cruise capture versus higher spend while onboard, and whether pre‑cruise pricing is less, equally, or more margin‑accretive than traditional onboard spend? Also, any change in cancellation/refund behavior in that pre‑cruise mix? Thanks.

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: Pre-cruise vs onboard spend split overlaps partially with loyalty yield implications.

---

### 2.19 — lizzie dove → xian siew (src: baseline_s4)

**Predicted** (lizzie dove): Hi there. Thanks for taking the question. You’ve highlighted strong digital adoption (app MAUs 5x since 2019 and >50% of onboard revenue booked pre‑cruise) — can you quantify the incremental lift to booking conversion, APD, and onboard spend per pax from these digital/AI initiatives and any margin improvement (in operating‑profit points) you’re already capturing? Got it. Thank you.

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: Digital/AI lifts adjacent to loyalty effects.

---

### 2.20 — robin farley → sharon zackfia (src: baseline_s3)

**Predicted** (robin farley): Great — a two‑part cost question on Net Cruise Costs ex‑fuel. (1) You said NCC ex‑fuel 'performed better than expected' and that full‑year NCC ex‑fuel is now ~flat (or ~50bps better). Can you decompose that improvement into: a) structural productivity/efficiency gains (bps), b) one‑time/timing items (bps), and c) fleet mix or onboard‑related effects (bps)? (2) How much of the better‑than‑expected Q1 performance is repeatable into Q2/Q3 once dry‑dock timing normalizes? Please give bps or $ amounts. Thanks.

**Actual** (sharon zackfia): Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Evaluator reasoning**: NCC ex-fuel structure vs timing is adjacent to fuel-driven itinerary/deferral asks.

---


## Score 1 Examples (n=20)

**Rubric says**: same broad business area only. Counts as `False`.

### 1.1 — andrew didora → vince ciepiel (src: baseline_s4)

**Predicted** (andrew didora): Hey, good morning — on the Icon platform capex/returns: you announced Icon 6 and 7 — can you give the incremental ROIC or margin profile you expect from the Icon series versus the fleet average and the expected payback period that underpins the confidence to add more Icons?

**Actual** (vince ciepiel): Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**Evaluator reasoning**: Icon ROIC/payback is only loosely linked to hardware contribution to yields.

---

### 1.2 — andrew didora → matthew boss (src: baseline_s1)

**Predicted** (andrew didora): Good morning — on fleet growth and Perfecta targets: you announced Icon 6 and 7 and reiterated the 20% CAGR Adjusted EPS target to 2027 — first, can you describe the expected incremental ROIC profile of the new Icon orders versus the current fleet, and second, how do the incremental unit economics support the Perfecta 20% ambition if macro/yields are modest?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Icon ROIC vs fleet is tangential to multi-year growth discussion.

---

### 1.3 — xian siew → matthew boss (src: baseline_s1)

**Predicted** (xian siew): Good morning — with Icon 6 & 7 ordered and Legend of the Seas showing pricing above prior Icon/Star levels, can you quantify the expected incremental margin or ROIC profile for Icon‑class ships versus fleet average and how that flows into your 'high‑teens' ROIC target?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: High-level ROIC/Icon profile adjacent to growth drivers but not asked.

---

### 1.4 — vince ciepiel → xian siew (src: baseline_s1)

**Predicted** (vince ciepiel): Onboard revenue and digital pre-booking: you said more than half of onboard revenue is now booked pre‑cruise and app MAUs are 5x 2019, and that onboard spending remains well above prior years — can you quantify how much of the onboard per‑guest lift is attributable to earlier digital sell (penetration/more items per booking) versus changes in guest mix (you noted more millennials and repeat guests)? And what magnitude uplift should we model per booking or per cruise day? Thanks.

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: Onboard pre-booking lift vs mix not asked.

---

### 1.5 — james hardiman → matthew boss (src: baseline_s5)

**Predicted** (james hardiman): You reiterated the Perfecta target — 20% CAGR in adjusted EPS through 2027 and ROIC in the high teens — for Icon and the Beach Club strategy, what are the underlying IRR/ROIC assumptions and payback periods you are using? Specifically, what ROIC do you expect Icon 6/7 to deliver on a stabilized basis and what APD uplift are you modeling from Royal Beach Club Santorini/Cozumel when fully ramped?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Project-level IRRs/ROIC are tangential to the durability question.

---

### 1.6 — brandt montour → vince ciepiel (src: baseline_s2)

**Predicted** (brandt montour): Hey, good morning — thanks. Quick one on yields: you reported Net Yields up 2% in Q1 and are guiding 1.5%–2.5% for the year; just to clarify, can you split that Q1 2% into ticket vs onboard contribution and tell us how much was mix (Europe/Med vs Caribbean) versus pure price? And as a follow-up, relative to 2019, what percent of the pre‑COVID APD gap have you recovered today?

**Actual** (vince ciepiel): Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**Evaluator reasoning**: Q1 split overlaps yield theme but not the full-year/new product mix ask.

---

### 1.7 — kevin kopelman → steven wieczynski (src: baseline_s2)

**Predicted** (kevin kopelman): Thanks — you said Q2 net yields are ~+0.2% but that there’s almost a 200bp headwind from comparison and dry docks — can you state what Q2 underlying yield would be excluding those temporary headwinds so we can understand the underlying pricing momentum?

**Actual** (steven wieczynski): Yeah. Hey, guys. Good morning. Thanks for all the color so far. Jason, as we think about the rest of the year, we obviously have your second quarter yield guidance, and I have to assume based on Naftali's comments that your third quarter yields are gonna look somewhat similar to your second quarter given the exposure you have to Europe. You know, then if that's true, that would imply your fourth quarter yields are gonna be growing, you know, let's call it somewhere in that mid-single- digit range to kinda get you into that 2%, you know, midpoint. You know, wondering what gives you the confiden

**Evaluator reasoning**: Underlying Q2 pricing only loosely tied to Q4 setup.

---

### 1.8 — brandt montour → matthew boss (src: baseline_s4)

**Predicted** (brandt montour): Hey, quick one on capital allocation — you finished the quarter with leverage below 3x, $6.9bn liquidity and $1bn remaining repurchase authority: what specific leverage or ROIC thresholds does the board want to see before materially expanding buybacks or reinstating a larger dividend cadence, and is there flexibility to accelerate the remaining $1bn this year if the fuel/mediterranean headwinds abate?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Capital allocation detail not an actual theme.

---

### 1.9 — robin farley → andrew didora (src: baseline_s4)

**Predicted** (robin farley): Okay — on joint ventures and TUI: you said better JV performance helped Q1 but included a $0.12 EPS headwind from lower expected TUI contribution — can you quantify expected full‑year JV contribution relative to last year in $s or EPS, explain the drivers at TUI (pricing, utilization, FX), and say how much downside risk you see to that $0.12 number? Thanks.

**Actual** (andrew didora): Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Evaluator reasoning**: TUI/JV specifics not an actual theme.

---

### 1.10 — brandt montour → xian siew (src: baseline_s4)

**Predicted** (brandt montour): Hey, thanks — on commercial and AI: you noted more than half of onboard revenue is now booked pre‑cruise and the app MAUs are 5x 2019 — can you quantify the incremental margin on pre‑cruise upgrades/experiences versus onboard impromptu spend and tell us whether earlier, more digital purchasing is compressing or expanding your close‑in pricing power (i.e., is it lifting APD or pulling demand forward)?

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: AI/digital monetization is adjacent but not the loyalty-driven yield behavior question.

---

### 1.11 — matthew boss → matthew boss (src: baseline_s5)

**Predicted** (matthew boss): Great, thanks — you highlighted AI and a unified intelligence layer and said digital penetration has more than doubled and app MAUs are 5x 2019; maybe be specific on which revenue levers are already AI‑driven (dynamic ticket pricing, ancillary personalization, bundling, close‑in optimization), what bps of yield or APCD uplift you can point to today from those deployments, and how we should phase additional yield benefits into our model over 12–24 months? Thanks.

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: AI/digital monetization was not a focus of the actual questions.

---

### 1.12 — andrew didora → xian siew (src: baseline_s1)

**Predicted** (andrew didora): Morning — regarding the digital/AI investments and the note that over half of onboard revenue is booked pre‑cruise: first, how are you measuring the incremental lift from AI/commerce changes (conversion, spend per pax), and second, do you have plans to change pricing mechanics or introduce dynamic pre‑cruise offers to capture more of that value?

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: AI measurement/pricing mechanics not asked.

---

### 1.13 — kevin kopelman → sharon zackfia (src: baseline_s2)

**Predicted** (kevin kopelman): Good morning — you attribute better Net Cruise Costs ex‑fuel to cost discipline and AI/tech — can you quantify the run‑rate savings or margin improvement from Perfecta/technology to date and when the bulk of those savings will flow through?

**Actual** (sharon zackfia): Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Evaluator reasoning**: Tech/AI savings quantification differs from itinerary/fuel changes or deferrals.

---

### 1.14 — robin farley → matthew boss (src: baseline_s1)

**Predicted** (robin farley): Okay — capacity mix and Legend of the Seas redeployment: 1) with 6.7% capacity growth and Legend entering the Caribbean in November, can you quantify the incremental APD/yield benefit you expect from that redeployment in FY‑2026 ($/APD or bps)? 2) Given elevated industry capacity in the Caribbean, what actions (itinerary mix, length, pricing levers) are you taking to protect yields? Thanks.

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Capacity mix/redeployment specifics were not probed.

---

### 1.15 — sharon zackfia → xian siew (src: baseline_s4)

**Predicted** (sharon zackfia): Hi. Good morning. Congrats on the quarter — quick one: you said "more than half of onboard revenue is booked before guests ever step on board" and that pre-cruise penetration in booking engines is over 70% with >5 items per booking — can you quantify that pre-booked share by category (shore excursions vs specialty dining vs F&B vs spa/retail), which categories are driving the year-over-year increase in spend per night, and how that mix has shifted versus 2019?

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: Category-level pre-book shares do not directly address loyalty-driven yield behavior.

---

### 1.16 — sharon zackfia → xian siew (src: baseline_s5)

**Predicted** (sharon zackfia): Hi, can I ask a follow-up? You noted an increase in millennials/younger guests and that pre-cruise penetration is now over 70% with 5+ items per booking — do younger cohorts pre-book at materially higher rates or spend per night than older cohorts, and if so by how much (e.g., % higher attach or $/night)?

**Actual** (xian siew): Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**Evaluator reasoning**: Cohort spend detail is tangential to the loyalty/repeat implications sought.

---

### 1.17 — matthew boss → matthew boss (src: baseline_s1)

**Predicted** (matthew boss): You highlighted technology and AI being embedded across pricing and personalization — can you give a concrete, measurable example where AI has already driven incremental yield or onboard spend (bps lift or $/APD), the timeline to scale that improvement across the fleet, and whether any portion of the 1.5%‑2.5% yield guidance assumes incremental AI-driven lift?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: AI attribution to yield not asked; only high-level durability was asked.

---

### 1.18 — james hardiman → sharon zackfia (src: baseline_s2)

**Predicted** (james hardiman): Got it — cost cadence for Q2 and modeling the back half: you flagged Q2 Net Cruise Costs ex‑fuel up ~4.6%–5.1% and said the quarter contains ~400bp of headwinds from dry docks, crew travel and timing. For modeling purposes, can you split that 4.6%–5.1% into (a) recurring structural inflation, (b) timing/dry‑dock one‑offs, and (c) crew/airlift costs — and confirm whether you expect the second half to be meaningfully better on a like‑for‑like basis?

**Actual** (sharon zackfia): Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Evaluator reasoning**: Cost cadence split differs from itinerary/fuel change or deferral focus.

---

### 1.19 — steven wieczynski → andrew didora (src: baseline_s4)

**Predicted** (steven wieczynski): Hey, guys. On joint ventures/TUI — Naftali flagged a $0.12 headwind from lower expected TUI contribution and said JVs underperformed in the quarter: can you give the expected dollar contribution from JVs (and TUI specifically) for 2026 versus 2025, and the sensitivity to a recovery or further softening at TUI?

**Actual** (andrew didora): Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Evaluator reasoning**: TUI/JV specifics not a focus of actual questions.

---

### 1.20 — steven wieczynski → matthew boss (src: baseline_s2)

**Predicted** (steven wieczynski): Hey, guys. Good morning. On the balance sheet and capital allocation — you finished the quarter <3x leverage, completed a $2.5 billion bond and repurchased $836 million with $1 billion remaining authority; do you have a target leverage range you're aiming for (is sub‑3x the steady-state goal) and how are you prioritizing between debt paydown and using the remaining buyback authorization over the next 12 months?

**Actual** (matthew boss): Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**Evaluator reasoning**: Capital allocation/buybacks not asked in the actual set.

---

