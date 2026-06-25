# Strict B4 — evaluation (judge) variance on fixed settings

Evaluator gpt-5-mini + `prompts/b4_eval_strict.md`, run **5× on the SAME predictions** per setting (predictions fixed; only judge stochasticity varies). For each actual question we list the 5 per-run scores (0–4) and mark whether `covered` (score≥3) **flips** across runs.

Batch `batch_6a20453ecae88190bb0042a1b4faa5a5`. Settings: final_eval_10q_v1, final_eval_14q_auto, final_eval_14q_v1, final_eval_14q_v5.


## final_eval_10q_v1

Coverage per run: ['0.667', '0.583', '0.667', '0.667', '0.667'] → mean 0.650, spread 0.083

**7 of 12 actual questions flip** the covered threshold across the 5 runs (5 stable).


### `robin_farley-actual-0` — scores [2, 0, 1, 0, 4] (min 0, max 4)

**ACTUAL:** Thanks. I had a question on yields, but also just a quick follow-up. Michael's comment may have just answered it, but, you know, it sounded like Mexico there had been, like, a little bit of a pause in construction becaus…

**matched pred (`robin_farley-pred-0`):** Thanks — a two-part one on yields: Q1 Net Yield was +2% and you guide 1.5%-2.5% for the year — can you split the drivers of that yield into ticket versus onboard (in bps or %), and tell us how each compares to 2019? Also…


### `robin_farley-actual-1` — scores [4, 2, 2, 4, 4] (min 2, max 4)

**ACTUAL:** Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a m…

**matched pred (`robin_farley-pred-1`):** Great — on the Mediterranean and West Coast Mexico disruption: you noted a short‑term moderation in high‑yield Mediterranean bookings and softer West Coast Mexico demand. Can you quantify the yield impact in basis points…


### `kevin_kopelman-actual-0` — scores [1, 2, 3, 2, 2] (min 1, max 3)

**ACTUAL:** Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North Ame…

**matched pred (`matthew_boss-pred-2`):** Good morning and congrats — Jason, on the Mediterranean softening you said the moderation lasted a few weeks and bookings have started to rebound: can you quantify that — what was the peak‑to‑trough APD or booking pace d…


### `matthew_boss-actual-0` — scores [3, 3, 3, 3, 2] (min 2, max 3)

**ACTUAL:** Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Mayb…

**matched pred (`vince_ciepiel-pred-0`):** Thanks, Jason and Naftali — a multi-part one on yield: you reported Net Yield +2% in Q1 and guided +1.5%-2.5% for 2026 — can you split that full-year guide between ticket yield versus onboard/ancillary, and separately qu…

**matched pred (`matthew_boss-pred-1`):** Congrats — Jason/Naftali, on Perfecta you're targeting a 20% compound adjusted EPS through 2027 and high‑teens ROIC: can you bridge that target for us — how much of the 20% CAGR is expected to come from yield expansion v…


### `steven_wieczynski-actual-0` — scores [3, 3, 2, 3, 3] (min 2, max 3)

**ACTUAL:** Yeah. Hey, guys. Good morning. Thanks for all the color so far. Jason, as we think about the rest of the year, we obviously have your second quarter yield guidance, and I have to assume based on Naftali's comments that y…

**matched pred (`steven_wieczynski-pred-0`):** Congrats on a strong quarter and the record wave season — quick multi-part on bookings and yield: can you give current percent booked by quarter (Q2–Q4) and APD versus 2019 for those periods, and when you say booked load…


### `lizzie_dove-actual-0` — scores [3, 3, 3, 2, 3] (min 2, max 3)

**ACTUAL:** Hi. Good morning. Thanks for taking the question. I was wondering if you could maybe give us a refresh on Perfect Day Mexico. You mentioned it's opening late 2027, ramping 2028. Could you maybe share some more details on…

**matched pred (`lizzie_dove-pred-6`):** Hi there. Good morning — you highlighted Royal Beach Club Paradise Island and Santorini as accretive to yield; can you quantify how much these private‑destination assets contributed to Q1 APD or Net Yield and what run‑ra…

**matched pred (`vince_ciepiel-pred-7`):** Thanks — on Perfect Day and Royal Beach Clubs: you flagged Santorini and Paradise Island momentum and Perfect Day Mexico/Costa Maya ramping in late 2027/early 2028 — can you quantify expected APD uplift per passenger at …


### `andrew_didora-actual-0` — scores [2, 2, 3, 3, 2] (min 2, max 3)

**ACTUAL:** Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. Yo…

**matched pred (`andrew_didora-pred-7`):** You noted the forward curve would imply ~4% lower fuel expense versus your spot‑based guidance and that you're ~59–60% hedged — can you explain your hedge sizing/pricing philosophy and whether you consider extending hedg…


## final_eval_14q_auto

Coverage per run: ['0.583', '0.667', '0.667', '0.583', '0.833'] → mean 0.667, spread 0.250

**4 of 12 actual questions flip** the covered threshold across the 5 runs (8 stable).


### `kevin_kopelman-actual-0` — scores [2, 0, 3, 0, 3] (min 0, max 3)

**ACTUAL:** Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North Ame…

**matched pred (`steven_wieczynski-pred-6`):** On the Mediterranean and West Coast Mexico softness: you said the softer booking trends were short-lived and are now rebounding; can you quantify the revenue/yield hit you expect for Q2 and Q3 from those region-specific …


### `andrew_didora-actual-0` — scores [2, 3, 2, 2, 4] (min 2, max 4)

**ACTUAL:** Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. Yo…

**matched pred (`andrew_didora-pred-1`):** Naftali — you referenced a $0.74 EPS headwind comprised of $0.62 from fuel and $0.12 from TUI; you also said you're ~59–60% hedged. Can you walk through the fuel hedge profile by remaining quarters, the strike/average pr…


### `steven_wieczynski-actual-0` — scores [2, 3, 2, 2, 3] (min 2, max 3)

**ACTUAL:** Yeah. Hey, guys. Good morning. Thanks for all the color so far. Jason, as we think about the rest of the year, we obviously have your second quarter yield guidance, and I have to assume based on Naftali's comments that y…

**matched pred (`steven_wieczynski-pred-11`):** Thanks — on Q2 cadence specifically: you guide Q2 Net Yields to ~+0.2% with almost 200 bps of headwind from dry docks and geopolitical factors; can you split that ~200 bps between dry-dock/timing effects and the Europe/M…

**matched pred (`steven_wieczynski-pred-0`):** Congrats on a nice quarter and the buyback — quick one to start: you opened the call by reiterating the companys "moderate capacity, moderate yield, cost discipline" framework and the Perfecta 20% CAGR target to 2027; c…


### `robin_farley-actual-1` — scores [3, 2, 3, 3, 3] (min 2, max 3)

**ACTUAL:** Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a m…

**matched pred (`robin_farley-pred-2`):** On the Mediterranean and West Coast Mexico disruption: can you quantify how many basis points of Net Yield downside you baked into your updated 2026 guidance that are attributable to those two regions (both for Q2/Q3 and…

**matched pred (`xian_siew-pred-13`):** Good morning — if geopolitical disruption in the Mediterranean were to persist through Q3, what percentage of the lost yield could you reasonably recapture via redeployment and pricing in other itineraries?


## final_eval_14q_v1

Coverage per run: ['0.833', '0.750', '0.833', '0.667', '0.833'] → mean 0.783, spread 0.167

**2 of 12 actual questions flip** the covered threshold across the 5 runs (10 stable).


### `andrew_didora-actual-0` — scores [3, 2, 4, 2, 3] (min 2, max 4)

**ACTUAL:** Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. Yo…

**matched pred (`andrew_didora-pred-4`):** You call out fuel as the most notable impact — you said ~60% hedged earlier and the CFO said forward consumption is 59% hedged; can you clarify your fuel hedging horizon and whether you plan to add hedges into the forwar…


### `robin_farley-actual-1` — scores [3, 3, 3, 2, 3] (min 2, max 3)

**ACTUAL:** Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a m…

**matched pred (`robin_farley-pred-2`):** Thanks — on the Mediterranean / Middle East impact: is the moderation you saw in high‑yield Mediterranean bookings and the temporary pause/repositioning in the Middle East fully baked into the 1.5–2.5% Net Yield guide, o…

**matched pred (`robin_farley-pred-12`):** On the quarterly cadence: you referenced a ~200 bps headwind to Q2 yields from year‑over‑year comparison elements including dry docks and geopolitical impacts — how much of that ~200 bps is timing versus structural deman…


## final_eval_14q_v5

Coverage per run: ['0.667', '0.667', '0.500', '0.667', '0.667'] → mean 0.633, spread 0.167

**4 of 13 actual questions flip** the covered threshold across the 5 runs (9 stable).


### `brandt_montour-actual-0` — scores [3, 2, 2, 3, 4] (min 2, max 4)

**ACTUAL:** Great. Thanks for taking my question. I just wanted to circle back on the third quarter and the Med, and just maybe if you could put a bit of a finer point on it. You know, how much do you have left to book at this point…

**matched pred (`james_hardiman-pred-2`):** Got it — on the Mediterranean weakness you described as a 'short‑term moderation' that 'lasted a few weeks' but is now rebounding: can you size the peak impact to booked APD or load factor during that window (percentage …

**matched pred (`brandt_montour-pred-6`):** Good morning — on the Mediterranean and West Coast Mexico disruption: you said those region‑specific events trimmed yields and that bookings have started to rebound. How much of the reduction in your January-to‑today yie…


### `robin_farley-actual-1` — scores [4, 3, 2, 2, 2] (min 2, max 4)

**ACTUAL:** Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a m…

**matched pred (`robin_farley-pred-1`):** Okay, yield decomposition: you guided Net Yield up 1.5%–2.5% for 2026 and noted record APD — can you quantify how much of that guidance is APD versus occupancy versus onboard/spend mix (bps or % points) and, as a follow …

**matched pred (`robin_farley-pred-4`):** Great — on Mediterranean and West Coast Mexico demand: you said bookings moderated for a few weeks and are now rebounding — can you quantify the incremental yield hit to the full‑year guide from those regional disruption…


### `andrew_didora-actual-0` — scores [2, 2, 2, 3, 2] (min 2, max 3)

**ACTUAL:** Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. Yo…

**matched pred (`andrew_didora-pred-2`):** On fuel: you noted $1.35 billion of fuel expense for the year, ~59% hedged at below market forwards and a $0.62 EPS headwind for the year — how should we think about your hedging philosophy going forward (do you plan to …


### `kevin_kopelman-actual-0` — scores [2, 3, 2, 2, 3] (min 2, max 3)

**ACTUAL:** Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North Ame…

**matched pred (`xian_siew-pred-6`):** Good morning. For the $17.10–$17.50 EPS guidance, can you provide the specific macro assumptions (airfare/consumer airfare cost sensitivity, FX rates, and interest cost assumptions) and the sensitivity of EPS to a 10% in…

