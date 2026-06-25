# Evaluation-variance analysis: which questions flip the coverage threshold

**Setup.** For a fixed setting (predictions held constant), the set-level B4 evaluator (gpt-5-mini + `prompts/b4_eval.md`) was run 5 times. Only the judge's stochasticity differs between runs. An actual question is a *flip* when its `covered` status (match score >= 3) is true in some runs and false in others. Scores are 0-4 per the rubric; covered = score >= 3.

**Why this matters.** Set coverage is computed over a 12-actual denominator, so each flipped question moves coverage by ~0.083. The run-to-run swing in coverage is driven almost entirely by a small number of borderline questions, not by uniform noise across all 12.


---

## Setting: `final_eval_14q_v5`

- Persona source / K: derived from the directory name.
- Coverage per run: ['0.833', '0.750', '0.917', '0.667', '0.667'] (mean 0.767, spread 0.250).
- Flipping questions: **3 of 12**.


### `sharon_zackfia-actual-0` — scores [2, 2, 4, 2, 2] (min 2, max 4)

**Actual question.**

> Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Best-matched predicted question(s) across runs.**

- `andrew_didora-pred-13` — run1=2, run5=2 → not covered

  > If geopolitical or air‑travel disruptions persist and Mediterranean/West Coast booking mixes worsen, what's your playbook for protecting APD — do you lean to discounts, re‑deployment (like moving Legend to the Caribbean), or ancillary mix actions, and how would each pathway show up in yield and margin?

- `sharon_zackfia-pred-8` — run2=2, run4=2 → not covered

  > Your Net Cruise Costs ex-fuel are roughly flat for the year but up materially in Q2 (4.6%–5.1%) — can you quantify the expected cadence by quarter (Q3/Q4) and the quantum of the recurring savings you expect from the Perfecta program/AI initiatives in 2027 (bps or $ per passenger)?

- `sharon_zackfia-pred-0` — run3=4 → covered (>=3)

  > Hi. Good morning. Net Yield was up 2% in Q1 and you’re guiding 1.5%–2.5% for the year — can you quantify what portion of that yield improvement is coming from ticket price versus onboard/pre-cruise spend (percent split), and within the onboard piece how much was booked pre-cruise vs on board this quarter?


### `andrew_didora-actual-0` — scores [4, 2, 4, 2, 2] (min 2, max 4)

**Actual question.**

> Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Best-matched predicted question(s) across runs.**

- `andrew_didora-pred-2` — run1=4, run2=2, run4=2, run5=2 → covered (>=3)

  > On fuel: you noted $1.35 billion of fuel expense for the year, ~59% hedged at below market forwards and a $0.62 EPS headwind for the year — how should we think about your hedging philosophy going forward (do you plan to increase hedges into the volatility), and how sensitive is your EPS guidance to a sustained move in fuel above current spot levels?

- `matthew_boss-pred-1` — run3=4 → covered (>=3)

  > Great — maybe to follow up on costs: you called out a ~$0.62 EPS fuel headwind and that you're ~60% hedged for 2026 (and Naftali called out 59% hedged for the remainder). Could you walk through the sensitivity (per $10/bbl or $0.10/gal) to EPS, how we should think about the gap between spot‑based guidance and the forward curve (you noted a ~4% difference), and whether you'll be opportunistic in adjusting hedge levels given current volatility?


### `kevin_kopelman-actual-0` — scores [3, 3, 4, 2, 2] (min 2, max 4)

**Actual question.**

> Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North America for your North America itineraries? How do you see consumers' ability to kind of swallow those airfare increases as they're getting to ports as the year goes on? Thanks.

**Best-matched predicted question(s) across runs.**

- `xian_siew-pred-6` — run1=3, run2=3, run3=4, run4=2, run5=2 → covered (>=3)

  > Good morning. For the $17.10–$17.50 EPS guidance, can you provide the specific macro assumptions (airfare/consumer airfare cost sensitivity, FX rates, and interest cost assumptions) and the sensitivity of EPS to a 10% increase in average air travel costs to Mediterranean itineraries?


---

## Setting: `final_eval_14q_auto`

- Persona source / K: derived from the directory name.
- Coverage per run: ['0.917', '0.750', '0.750', '0.833', '0.750'] (mean 0.800, spread 0.167).
- Flipping questions: **2 of 12**.


### `andrew_didora-actual-0` — scores [3, 2, 2, 3, 3] (min 2, max 3)

**Actual question.**

> Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Best-matched predicted question(s) across runs.**

- `andrew_didora-pred-1` — run1=3, run4=3 → covered (>=3)

  > Naftali — you referenced a $0.74 EPS headwind comprised of $0.62 from fuel and $0.12 from TUI; you also said you're ~59–60% hedged. Can you walk through the fuel hedge profile by remaining quarters, the strike/average price on that 59% and the EPS sensitivity per $10 move in Brent so we can bridge to that $0.62 number?

- `andrew_didora-pred-12` — run2=2, run5=3 → covered (>=3)

  > Naftali — you said 59% of forward consumption is hedged 'at significantly below market rates' and that using the forward curve would reduce fuel expense ~4%; do you have plans to opportunistically add hedges or monetize that delta, and what would the EPS impact be if you fully hedged the remainder at the current forward curve?

- `xian_siew-pred-1` — run3=2 → not covered

  > Good morning — can you give the average hedged fuel price for the ~60% (59%) of 2026 consumption you noted and the EPS sensitivity to a $10/bbl move from current spot?


### `kevin_kopelman-actual-0` — scores [2, 3, 3, 3, 2] (min 2, max 3)

**Actual question.**

> Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North America for your North America itineraries? How do you see consumers' ability to kind of swallow those airfare increases as they're getting to ports as the year goes on? Thanks.

**Best-matched predicted question(s) across runs.**

- `vince_ciepiel-pred-3` — run1=2 → not covered

  > On the Mediterranean sensitivity you called out: you said high‑yield Med bookings moderated for a few weeks due to geopolitical/air travel disruption but have rebounded. Quantitatively, what is the yield or APD downside at today's booking pace for the Med exposure in Q2/Q3 versus your January baseline, and what's the sensitivity to a 10% move higher in typical air fares or a 10% reduction in airline seats for those sailings?

- `steven_wieczynski-pred-6` — run2=3, run4=3, run5=2 → covered (>=3)

  > On the Mediterranean and West Coast Mexico softness: you said the softer booking trends were short-lived and are now rebounding; can you quantify the revenue/yield hit you expect for Q2 and Q3 from those region-specific disruptions (bp of yield or $mm revenue), and how much of the near-term weakness is attributable to higher airline costs versus demand aversion? (follow-up: do you currently expect any incremental redeployments or itinerary changes beyond moving Legend into the Caribbean?)

- `matthew_boss-pred-8` — run3=3 → covered (>=3)

  > Congrats — on the Mediterranean headwind: can you quantify the yield hit from the geopolitical/airline‑driven disruption on Mediterranean itineraries in $ APD or bps for Q2/Q3, and split how much of that is higher air costs versus lower booked rates or mix shifts?


---

## Setting: `final_eval_14q_v1_rerun2`

- Persona source / K: derived from the directory name.
- Coverage per run: ['0.750', '0.750', '0.833', '0.667', '0.583'] (mean 0.717, spread 0.250).
- Flipping questions: **4 of 12**.


### `kevin_kopelman-actual-0` — scores [2, 3, 4, 2, 0] (min 0, max 4)

**Actual question.**

> Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North America for your North America itineraries? How do you see consumers' ability to kind of swallow those airfare increases as they're getting to ports as the year goes on? Thanks.

**Best-matched predicted question(s) across runs.**

- `lizzie_dove-pred-12` — run1=2 → not covered

  > Thanks — on capacity mix: full‑year capacity growth is 6.7% with Q1 and Q3 higher than Q2 and Q4 — can you break the capacity growth by brand (RCL, Celebrity, Silversea/Icon) and by region so we can map where the incremental capacity is coming and its likely mix impact on APD?

- `brandt_montour-pred-12` — run2=3, run3=4, run4=2 → covered (>=3)

  > You referenced airline capacity and flight disruptions as a driver of Mediterranean softness — what percentage of your European/Mediterranean pax require air connections you don't control, and do you model any incremental compensation/refund or re‑protection cost per affected guest that we should include in near‑term cost assumptions?

- `None` — run5=0 → not covered

  > ?


### `robin_farley-actual-1` — scores [3, 3, 4, 4, 2] (min 2, max 4)

**Actual question.**

> Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a mid-single digit sort of shift in where you had expected European yields to come, to come in this year. Is it fair to assume that you would kind of fully expect that to come back in 2027 when we're kind of thinking ahead to, you know, the impact this year being kind of, you know, not necessarily coming out of next year? Just help us to size that. Thank you.

**Best-matched predicted question(s) across runs.**

- `brandt_montour-pred-2` — run1=3 → covered (>=3)

  > On the Mediterranean moderation you referenced and the recent rebound — can you quantify the incremental yield/Revenue-at-Risk to Q2 and Q3 in either $ or p.p. terms, and comment on whether the recovery is driven by pricing catch‑up on remaining inventory or simply rebooking of itineraries?

- `matthew_boss-pred-0` — run2=3 → covered (>=3)

  > Great, thanks and congrats on the quarter. Jason — on the Mediterranean moderation you called out: can you help size the incremental yield shortfall versus your January plan (how many cents/dollars of APD or percent of full‑year yield), and color whether that is a permanent repricing or close‑in pull‑forward that you expect to reprice into later sailings? Naftali — numerically, how much of the 1.5%–2.5% full‑year Net Yield range was already locked in at the January cadence and how much is now at risk given the recent weeks of softer demand?

- `robin_farley-pred-1` — run3=4, run4=4, run5=2 → covered (>=3)

  > Thanks — follow-up: Naftali noted Q2 yields are only up ~0.2% but that the quarter carries almost a 200bp headwind from dry docks and geopolitics; can you quantify the bucketed math — how many bps of that 200 are dry-dock timing vs Mediterranean/West Coast Mexico routing/air disruptions — and how much of those bps reverse in Q3/Q4?


### `steven_wieczynski-actual-0` — scores [3, 2, 3, 3, 3] (min 2, max 3)

**Actual question.**

> Yeah. Hey, guys. Good morning. Thanks for all the color so far. Jason, as we think about the rest of the year, we obviously have your second quarter yield guidance, and I have to assume based on Naftali's comments that your third quarter yields are gonna look somewhat similar to your second quarter given the exposure you have to Europe. You know, then if that's true, that would imply your fourth quarter yields are gonna be growing, you know, let's call it somewhere in that mid-single- digit range to kinda get you into that 2%, you know, midpoint. You know, wondering what gives you the confidence the fourth quarter could grow that much. I guess then that actually to me would imply, that without the European headwinds you guys encountered, you know, you guys would've actually been able to raise your full year yield guidance. Am I kinda thinking about that all the right way?

**Best-matched predicted question(s) across runs.**

- `steven_wieczynski-pred-0` — run1=3, run2=2, run5=3 → covered (>=3)

  > Congrats on a strong wave season — quick one to drill into the book: you said booked load factor is within historical ranges and APD is at a record — can you give us the percent booked by quarter for Q2–Q4 versus the same points in 2019, and finally break the 2% Net Yield beat into ticket versus onboard mix so we can model how much of your yield upside is durable versus potentially close‑in spend?

- `robin_farley-pred-1` — run3=3 → covered (>=3)

  > Thanks — follow-up: Naftali noted Q2 yields are only up ~0.2% but that the quarter carries almost a 200bp headwind from dry docks and geopolitics; can you quantify the bucketed math — how many bps of that 200 are dry-dock timing vs Mediterranean/West Coast Mexico routing/air disruptions — and how much of those bps reverse in Q3/Q4?

- `james_hardiman-pred-4` — run4=3 → covered (>=3)

  > Good morning — on the region‑specific softness: you referenced a short‑term moderation in Mediterranean and West Coast Mexico bookings and that Q2/Q3 yields take a hit — can you quantify the APD or yield impact by region and give a booking curve/timeline (days‑to‑departure) for recovery assumptions embedded in your guidance?


### `andrew_didora-actual-0` — scores [3, 3, 3, 2, 3] (min 2, max 3)

**Actual question.**

> Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Best-matched predicted question(s) across runs.**

- `andrew_didora-pred-5` — run1=3, run2=3, run3=3, run4=2, run5=3 → covered (>=3)

  > On fuel: you called out a $0.62 EPS headwind and that 59%–60% of forward consumption is hedged — can you quantify the sensitivity of EPS to a $10 move in bunker and whether you plan to add incremental hedges now that spot is above the forward curve?


---

## Setting: `final_eval_10q_v5`

- Persona source / K: derived from the directory name.
- Coverage per run: ['0.750', '0.636', '0.917', '0.750', '0.583'] (mean 0.727, spread 0.333).
- Flipping questions: **6 of 12**.


### `robin_farley-actual-0` — scores [2, 0, 3, 1, 2] (min 0, max 3)

**Actual question.**

> Thanks. I had a question on yields, but also just a quick follow-up. Michael's comment may have just answered it, but, you know, it sounded like Mexico there had been, like, a little bit of a pause in construction because of that environmental stuff. Just wanna clarify if Michael's comment means that construction is, you know, resumed in Mexico there.

**Best-matched predicted question(s) across runs.**

- `robin_farley-pred-3` — run1=2, run4=1, run5=2 → not covered

  > Okay — on dry docks and new private destinations: 1) you flagged additional dry dock days as a driver of near‑term cost — how many incremental dry dock days versus last year and what is the expected cadence into 2H and 2027? 2) For Royal Beach Club Santorini/Cozumel and Perfect Day ramping in 2027–28, can you quantify the expected one‑time versus run‑rate margin impact (bps or $ of EBITDA) during ramp years? Thanks.

- `None` — run2=0 → not covered

  > ?

- `robin_farley-pred-1` — run3=3 → covered (>=3)

  > Okay — on yield guidance and the regional impact, two parts: 1) your full‑year Net Yield guide is 1.5%–2.5% — can you split that into ticket yield vs onboard yield and occupancy vs APD (ideally vs the same point in 2019, % or bps)? 2) You said the revision from January is driven by Mediterranean and West Coast Mexico — can you quantify the contribution of each region to the downward move in bps or $ per share? Thanks.


### `kevin_kopelman-actual-0` — scores [4, 3, 1, 2] (min 1, max 4)

**Actual question.**

> Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North America for your North America itineraries? How do you see consumers' ability to kind of swallow those airfare increases as they're getting to ports as the year goes on? Thanks.

**Best-matched predicted question(s) across runs.**

- `brandt_montour-pred-8` — run1=4, run3=3, run5=2 → covered (>=3)

  > Just to follow up on Europe/Mediterranean: you mentioned Q2 and Q3 yields face almost 200bps headwind from geopolitical/air‑travel impacts — can you split that ~200bps between Mediterranean versus West Coast Mexico and the air/flight impacts versus itinerary re‑pricing so we can model sensitivity?

- `kevin_kopelman-pred-0` — run4=1 → not covered

  > Hi, good morning — can you quantify the current booking lead‑time profile for 2026 (e.g., % booked within 0‑30 / 31‑90 / >90 days) and tell us whether the recent Mediterranean softness was concentrated in close‑in bookings versus forward inventory?


### `robin_farley-actual-1` — scores [3, 2, 4, 3, 2] (min 2, max 4)

**Actual question.**

> Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a mid-single digit sort of shift in where you had expected European yields to come, to come in this year. Is it fair to assume that you would kind of fully expect that to come back in 2027 when we're kind of thinking ahead to, you know, the impact this year being kind of, you know, not necessarily coming out of next year? Just help us to size that. Thank you.

**Best-matched predicted question(s) across runs.**

- `robin_farley-pred-1` — run1=3, run2=2, run3=4, run4=3, run5=2 → covered (>=3)

  > Okay — on yield guidance and the regional impact, two parts: 1) your full‑year Net Yield guide is 1.5%–2.5% — can you split that into ticket yield vs onboard yield and occupancy vs APD (ideally vs the same point in 2019, % or bps)? 2) You said the revision from January is driven by Mediterranean and West Coast Mexico — can you quantify the contribution of each region to the downward move in bps or $ per share? Thanks.


### `sharon_zackfia-actual-0` — scores [2, 1, 3, 3, 2] (min 1, max 3)

**Actual question.**

> Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Best-matched predicted question(s) across runs.**

- `andrew_didora-pred-2` — run1=2, run3=3, run5=2 → covered (>=3)

  > Hey, quick one on fuel: you said you're ~59–60% hedged and that guidance assumes current spot with a roughly $0.62 fuel headwind — first, can you walk us through your hedging decision framework if spot stays elevated (how you layer hedges and time them); and second, operationally, what options do you have to mitigate incremental fuel cost pressure beyond hedging?

- `sharon_zackfia-pred-8` — run2=1 → not covered

  > On costs and cadence: Q2 Net Cruise Costs ex-fuel are guided to be up ~4.6%–5.1% driven by ~400bps of headwinds from dry docks and crew travel — can you quantify the stock-to-flow of those timing items (i.e., how much of the quarterly step-up is genuinely structural vs. timing that reverses later in the year) and the implied $ or bps improvement you expect in back-half cost dynamics?

- `matthew_boss-pred-3` — run4=3 → covered (>=3)

  > Naftali, you’ve kept full‑year Net Cruise Costs ex‑fuel roughly flat to prior guide but Q2 is guided up 4.6%‑5.1% ex‑fuel given dry docks and crew travel; can you quantify how much of the H1 headwind you expect to reverse in H2 (in bps or $) and spell out the primary levers/timing that get you to the full‑year outcome?


### `andrew_didora-actual-0` — scores [2, 2, 4, 3, 3] (min 2, max 4)

**Actual question.**

> Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Best-matched predicted question(s) across runs.**

- `andrew_didora-pred-2` — run1=2, run2=2, run3=4, run4=3, run5=3 → covered (>=3)

  > Hey, quick one on fuel: you said you're ~59–60% hedged and that guidance assumes current spot with a roughly $0.62 fuel headwind — first, can you walk us through your hedging decision framework if spot stays elevated (how you layer hedges and time them); and second, operationally, what options do you have to mitigate incremental fuel cost pressure beyond hedging?


### `steven_wieczynski-actual-0` — scores [3, 3, 2, 2, 2] (min 2, max 3)

**Actual question.**

> Yeah. Hey, guys. Good morning. Thanks for all the color so far. Jason, as we think about the rest of the year, we obviously have your second quarter yield guidance, and I have to assume based on Naftali's comments that your third quarter yields are gonna look somewhat similar to your second quarter given the exposure you have to Europe. You know, then if that's true, that would imply your fourth quarter yields are gonna be growing, you know, let's call it somewhere in that mid-single- digit range to kinda get you into that 2%, you know, midpoint. You know, wondering what gives you the confidence the fourth quarter could grow that much. I guess then that actually to me would imply, that without the European headwinds you guys encountered, you know, you guys would've actually been able to raise your full year yield guidance. Am I kinda thinking about that all the right way?

**Best-matched predicted question(s) across runs.**

- `james_hardiman-pred-9` — run1=3, run2=3 → covered (>=3)

  > By way of follow-up on the booking curve: you said remaining inventory for Q2/Q3 is limited and APD is at record levels — can you give us the current pace/velocity for remaining inventory sell‑through and a sensitivity for upside to full‑year Net Yield if the current rebound in Mediterranean bookings continues? For example, what would +100 bps of incremental APD on remaining inventory flow through to EPS?

- `steven_wieczynski-pred-2` — run3=2, run4=2 → not covered

  > Hey, guys. You described a strong book position, record APD and bookings rebounding in the Med — can you quantify how booked APD and booked load factor today compare to the same book point in 2019 and versus last year for the comparable sailings, and what percent of 2026 capacity is currently locked at those record prices?

- `steven_wieczynski-pred-1` — run5=2 → not covered

  > Hey, guys. Following up on yields: Q1 Net Yield was +2% and full‑year guidance is 1.5%–2.5% with Q2 roughly +0.2% — can you decompose the full‑year yield guide into ticket versus onboard contribution (ppt) and give us a modeling anchor — i.e., what is your $ or EPS sensitivity to a 1% change in Net Yield?


---

## Setting: `final_eval_20q_auto`

- Persona source / K: derived from the directory name.
- Coverage per run: ['0.750', '0.833', '0.833', '0.667', '0.750'] (mean 0.767, spread 0.167).
- Flipping questions: **3 of 12**.


### `robin_farley-actual-1` — scores [2, 2, 4, 2, 4] (min 2, max 4)

**Actual question.**

> Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a mid-single digit sort of shift in where you had expected European yields to come, to come in this year. Is it fair to assume that you would kind of fully expect that to come back in 2027 when we're kind of thinking ahead to, you know, the impact this year being kind of, you know, not necessarily coming out of next year? Just help us to size that. Thank you.

**Best-matched predicted question(s) across runs.**

- `steven_wieczynski-pred-1` — run1=2 → not covered

  > Nice quarter — on yield guidance: you tightened Net Yield to 1.5%–2.5% and said the Mediterranean and West Coast Mexico moderation pulled the guide down; how many basis points of the midpoint (and of the 1.5%–2.5% range) are directly attributable to those two regions versus the rest of the portfolio, and as a follow-up, how much of that regional hit is assumed to recover by Q4?

- `robin_farley-pred-1` — run2=2 → not covered

  > Just circling back on book position: you said booked load factor is within historical ranges at record APD — how much of the full year capacity is already sold (percent of ticketed revenue or percent of sailings at target load) by quarter today, and what share of the remaining inventory is concentrated in the high‑yield Europe sailings?

- `robin_farley-pred-3` — run3=4 → covered (>=3)

  > You flagged almost a 200bp yield headwind to Q2 from dry docks and geopolitical impacts — can you split that ~200bps between (a) dry dock/timing, (b) Mediterranean geopolitical/airline disruptions, and (c) West Coast Mexico? And which of those is timing versus structural so we know how to smooth this through our models?

- `robin_farley-pred-15` — run4=2 → not covered

  > You noted Q2 Net Yields are up ~0.2% reported but with almost 200bps of headwind — that implies underlying strength — can you give the underlying ex‑timing/airline/disruption yield movement for Q2 (i.e., what is the pro‑forma yield growth stripping out those headwinds)?

- `lizzie_dove-pred-1` — run5=4 → covered (>=3)

  > Good morning — you noted a Q2 Net Yield expectation of ~+0.2% and that region-specific geopolitical events create almost a 200 bps headwind to Q2 yields; can you break that 200 bps into (a) itinerary/mix effects (Mediterranean & West Coast Mexico), (b) air travel cost/flight disruption pass‑through, and (c) near‑term pricing concessions — and quantify the expected rebound timing (i.e., how much of that is recoverable in Q3 vs only later)?


### `sharon_zackfia-actual-0` — scores [2, 3, 3, 2, 1] (min 1, max 3)

**Actual question.**

> Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**Best-matched predicted question(s) across runs.**

- `sharon_zackfia-pred-6` — run1=2, run2=3, run3=3, run4=2, run5=1 → covered (>=3)

  > You beat guidance on Net Cruise Costs ex‑fuel and expect them roughly flat for the year — can you quantify how much of the Q1 beat was structural (permanent efficiency gains) versus timing (one‑offs), and the run‑rate dollar or bps improvement we should model into 2027?


### `andrew_didora-actual-0` — scores [3, 3, 2, 2, 2] (min 2, max 3)

**Actual question.**

> Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**Best-matched predicted question(s) across runs.**

- `andrew_didora-pred-2` — run1=3, run2=3, run3=2, run4=2, run5=2 → covered (>=3)

  > Naftali (or Jason), you said you're roughly 60% hedged for 2026 (59% for the remainder per Naftali) and that the guidance is based on spot — can you walk through the hedge profile by quarter, the average hedge price, and confirm the headline $0.62 (or $0.74) per-share fuel headwind math?


---

## Model comparison on the borderline questions — gpt-5 vs gpt-5-mini (`final_eval_14q_v5`, lenient B4, 5 runs each)

Same predictions, same rubric (`prompts/b4_eval.md`); only the evaluator model differs. Coverage = score >= 3.

- gpt-5 coverage per run: ['0.750', '0.750', '0.667', '0.833', '0.583'] (mean 0.717, spread 0.250).
- gpt-5-mini coverage per run: ['0.833', '0.750', '0.917', '0.667', '0.667'] (mean 0.767, spread 0.250).

| actual | gpt-5 scores | gpt-5 covered? | gpt-5-mini scores | mini covered? |
|---|---|---|---|---|
| `sharon_zackfia-actual-0` | [1, 2, 2, 2, 2] | 0/5 | [2, 2, 4, 2, 2] | 1/5 |
| `andrew_didora-actual-0` | [3, 3, 3, 3, 2] | 4/5 | [4, 2, 4, 2, 2] | 2/5 |
| `kevin_kopelman-actual-0` | [2, 2, 2, 3, 2] | 1/5 | [3, 3, 4, 2, 2] | 3/5 |


### `sharon_zackfia-actual-0`

**Actual.**

> Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**gpt-5 — per run (score → best-matched prediction):**

- run1: score 1 ✗ → `sharon_zackfia-pred-8`
- run2: score 2 ✗ → `robin_farley-pred-0`
- run3: score 2 ✗ → `robin_farley-pred-0`
- run4: score 2 ✗ → `sharon_zackfia-pred-8`
- run5: score 2 ✗ → `robin_farley-pred-0`

  > `sharon_zackfia-pred-8`: Your Net Cruise Costs ex-fuel are roughly flat for the year but up materially in Q2 (4.6%–5.1%) — can you quantify the expected cadence by quarter (Q3/Q4) and the quantum of the recurring savings you expect from the Perfecta program/AI initiatives in 2027 (bps or $ per passenger)?


  > `robin_farley-pred-0`: Great — two quick ones on costs: 1) You said Net Cruise Costs ex‑fuel are roughly flat or ~50 bps better than prior guidance — can you decompose that improvement into specific line items (wages, food, dry‑dock timing, insurance, crew travel) in bps and $ amounts? 2) Which of those are structural versus timing/one‑off and therefore sustainable into 2027? Thanks.

**gpt-5-mini — per run (score → best-matched prediction):**

- run1: score 2 ✗ → `andrew_didora-pred-13`
- run2: score 2 ✗ → `sharon_zackfia-pred-8`
- run3: score 4 ✓ → `sharon_zackfia-pred-0`
- run4: score 2 ✗ → `sharon_zackfia-pred-8`
- run5: score 2 ✗ → `andrew_didora-pred-13`

  > `andrew_didora-pred-13`: If geopolitical or air‑travel disruptions persist and Mediterranean/West Coast booking mixes worsen, what's your playbook for protecting APD — do you lean to discounts, re‑deployment (like moving Legend to the Caribbean), or ancillary mix actions, and how would each pathway show up in yield and margin?


  > `sharon_zackfia-pred-8`: Your Net Cruise Costs ex-fuel are roughly flat for the year but up materially in Q2 (4.6%–5.1%) — can you quantify the expected cadence by quarter (Q3/Q4) and the quantum of the recurring savings you expect from the Perfecta program/AI initiatives in 2027 (bps or $ per passenger)?


  > `sharon_zackfia-pred-0`: Hi. Good morning. Net Yield was up 2% in Q1 and you’re guiding 1.5%–2.5% for the year — can you quantify what portion of that yield improvement is coming from ticket price versus onboard/pre-cruise spend (percent split), and within the onboard piece how much was booked pre-cruise vs on board this quarter?



### `andrew_didora-actual-0`

**Actual.**

> Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**gpt-5 — per run (score → best-matched prediction):**

- run1: score 3 ✓ → `andrew_didora-pred-2`
- run2: score 3 ✓ → `james_hardiman-pred-10`
- run3: score 3 ✓ → `andrew_didora-pred-2`
- run4: score 3 ✓ → `andrew_didora-pred-2`
- run5: score 2 ✗ → `andrew_didora-pred-2`

  > `andrew_didora-pred-2`: On fuel: you noted $1.35 billion of fuel expense for the year, ~59% hedged at below market forwards and a $0.62 EPS headwind for the year — how should we think about your hedging philosophy going forward (do you plan to increase hedges into the volatility), and how sensitive is your EPS guidance to a sustained move in fuel above current spot levels?


  > `james_hardiman-pred-10`: Hey — one on fuel: you referenced roughly $0.62–$0.74 of fuel headwinds and said the guidance is spot‑based while the forward curve would be ~4% lower; can you clarify the reconciliation between the $0.62 (CEO) and the $0.74 (CFO) figures, confirm the percent of 2026 consumption hedged and share your hedging philosophy — will you opportunistically increase hedge levels given current volatility?

**gpt-5-mini — per run (score → best-matched prediction):**

- run1: score 4 ✓ → `andrew_didora-pred-2`
- run2: score 2 ✗ → `andrew_didora-pred-2`
- run3: score 4 ✓ → `matthew_boss-pred-1`
- run4: score 2 ✗ → `andrew_didora-pred-2`
- run5: score 2 ✗ → `andrew_didora-pred-2`

  > `andrew_didora-pred-2`: On fuel: you noted $1.35 billion of fuel expense for the year, ~59% hedged at below market forwards and a $0.62 EPS headwind for the year — how should we think about your hedging philosophy going forward (do you plan to increase hedges into the volatility), and how sensitive is your EPS guidance to a sustained move in fuel above current spot levels?


  > `matthew_boss-pred-1`: Great — maybe to follow up on costs: you called out a ~$0.62 EPS fuel headwind and that you're ~60% hedged for 2026 (and Naftali called out 59% hedged for the remainder). Could you walk through the sensitivity (per $10/bbl or $0.10/gal) to EPS, how we should think about the gap between spot‑based guidance and the forward curve (you noted a ~4% difference), and whether you'll be opportunistic in adjusting hedge levels given current volatility?



### `kevin_kopelman-actual-0`

**Actual.**

> Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North America for your North America itineraries? How do you see consumers' ability to kind of swallow those airfare increases as they're getting to ports as the year goes on? Thanks.

**gpt-5 — per run (score → best-matched prediction):**

- run1: score 2 ✗ → `xian_siew-pred-6`
- run2: score 2 ✗ → `xian_siew-pred-6`
- run3: score 2 ✗ → `xian_siew-pred-6`
- run4: score 3 ✓ → `xian_siew-pred-6`
- run5: score 2 ✗ → `xian_siew-pred-6`

  > `xian_siew-pred-6`: Good morning. For the $17.10–$17.50 EPS guidance, can you provide the specific macro assumptions (airfare/consumer airfare cost sensitivity, FX rates, and interest cost assumptions) and the sensitivity of EPS to a 10% increase in average air travel costs to Mediterranean itineraries?

**gpt-5-mini — per run (score → best-matched prediction):**

- run1: score 3 ✓ → `xian_siew-pred-6`
- run2: score 3 ✓ → `xian_siew-pred-6`
- run3: score 4 ✓ → `xian_siew-pred-6`
- run4: score 2 ✗ → `xian_siew-pred-6`
- run5: score 2 ✗ → `xian_siew-pred-6`

  > `xian_siew-pred-6`: Good morning. For the $17.10–$17.50 EPS guidance, can you provide the specific macro assumptions (airfare/consumer airfare cost sensitivity, FX rates, and interest cost assumptions) and the sensitivity of EPS to a 10% increase in average air travel costs to Mediterranean itineraries?



---

## Strict rubric — gpt-5 vs gpt-5-mini on the borderline questions (`final_eval_14q_v5`, `prompts/b4_eval_strict.md`)

Same predicted pool as the lenient analysis above (same `summary.json`); only the rubric (strict) and evaluator model differ. gpt-5 n=3, gpt-5-mini n=5. Coverage = score >= 3.

**Predicted-pool source for the three target analysts:** `sharon_zackfia` = v5, `andrew_didora` = v5, `kevin_kopelman` = auto-fallback (v5 generation fell back to auto for this analyst). The pool is identical across models and matches the K=14 flip table.

- gpt-5 strict coverage per run: ['0.667', '0.500', '0.583'] (mean 0.583).
- gpt-5-mini strict coverage per run: ['0.667', '0.667', '0.500', '0.667', '0.667'] (mean 0.633).

| actual | gpt-5 strict scores | covered | gpt-5-mini strict scores | covered |
|---|---|---|---|---|
| `sharon_zackfia-actual-0` | [2, 1, 3] | 1/3 | [1, 2, 2, 1, 1] | 0/5 |
| `andrew_didora-actual-0` | [2, 2, 2] | 0/3 | [2, 2, 2, 3, 2] | 1/5 |
| `kevin_kopelman-actual-0` | [2, 1, 2] | 0/3 | [2, 3, 2, 2, 3] | 2/5 |


### `sharon_zackfia-actual-0` (strict)

**Actual.**

> Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**gpt-5 strict — per run (score → best-matched prediction):**

- run1: score 2 ✗ → `steven_wieczynski-pred-5`
- run2: score 1 ✗ → `andrew_didora-pred-2`
- run3: score 3 ✓ → `sharon_zackfia-pred-8`

  > `steven_wieczynski-pred-5`: Costs — you say Net Cruise Costs ex‑fuel are roughly flat for the year and Q2 is up 4.6%–5.1% due to dry docks and crew travel; how much of the full‑year improvement is structural versus timing (i.e., normalized run‑rate benefit in 2027), and can you quantify that in either $ or % so we can model the sustained cost base?


  > `andrew_didora-pred-2`: On fuel: you noted $1.35 billion of fuel expense for the year, ~59% hedged at below market forwards and a $0.62 EPS headwind for the year — how should we think about your hedging philosophy going forward (do you plan to increase hedges into the volatility), and how sensitive is your EPS guidance to a sustained move in fuel above current spot levels?


  > `sharon_zackfia-pred-8`: Your Net Cruise Costs ex-fuel are roughly flat for the year but up materially in Q2 (4.6%–5.1%) — can you quantify the expected cadence by quarter (Q3/Q4) and the quantum of the recurring savings you expect from the Perfecta program/AI initiatives in 2027 (bps or $ per passenger)?

**gpt-5-mini strict — per run (score → best-matched prediction):**

- run1: score 1 ✗ → `sharon_zackfia-pred-8`
- run2: score 2 ✗ → `andrew_didora-pred-13`
- run3: score 2 ✗ → `sharon_zackfia-pred-8`
- run4: score 1 ✗ → `sharon_zackfia-pred-8`
- run5: score 1 ✗ → `sharon_zackfia-pred-8`

  > `sharon_zackfia-pred-8`: Your Net Cruise Costs ex-fuel are roughly flat for the year but up materially in Q2 (4.6%–5.1%) — can you quantify the expected cadence by quarter (Q3/Q4) and the quantum of the recurring savings you expect from the Perfecta program/AI initiatives in 2027 (bps or $ per passenger)?


  > `andrew_didora-pred-13`: If geopolitical or air‑travel disruptions persist and Mediterranean/West Coast booking mixes worsen, what's your playbook for protecting APD — do you lean to discounts, re‑deployment (like moving Legend to the Caribbean), or ancillary mix actions, and how would each pathway show up in yield and margin?



### `andrew_didora-actual-0` (strict)

**Actual.**

> Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**gpt-5 strict — per run (score → best-matched prediction):**

- run1: score 2 ✗ → `andrew_didora-pred-2`
- run2: score 2 ✗ → `matthew_boss-pred-1`
- run3: score 2 ✗ → `andrew_didora-pred-2`

  > `andrew_didora-pred-2`: On fuel: you noted $1.35 billion of fuel expense for the year, ~59% hedged at below market forwards and a $0.62 EPS headwind for the year — how should we think about your hedging philosophy going forward (do you plan to increase hedges into the volatility), and how sensitive is your EPS guidance to a sustained move in fuel above current spot levels?


  > `matthew_boss-pred-1`: Great — maybe to follow up on costs: you called out a ~$0.62 EPS fuel headwind and that you're ~60% hedged for 2026 (and Naftali called out 59% hedged for the remainder). Could you walk through the sensitivity (per $10/bbl or $0.10/gal) to EPS, how we should think about the gap between spot‑based guidance and the forward curve (you noted a ~4% difference), and whether you'll be opportunistic in adjusting hedge levels given current volatility?

**gpt-5-mini strict — per run (score → best-matched prediction):**

- run1: score 2 ✗ → `andrew_didora-pred-2`
- run2: score 2 ✗ → `andrew_didora-pred-2`
- run3: score 2 ✗ → `andrew_didora-pred-2`
- run4: score 3 ✓ → `andrew_didora-pred-2`
- run5: score 2 ✗ → `andrew_didora-pred-2`

  > `andrew_didora-pred-2`: On fuel: you noted $1.35 billion of fuel expense for the year, ~59% hedged at below market forwards and a $0.62 EPS headwind for the year — how should we think about your hedging philosophy going forward (do you plan to increase hedges into the volatility), and how sensitive is your EPS guidance to a sustained move in fuel above current spot levels?



### `kevin_kopelman-actual-0` (strict)

**Actual.**

> Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North America for your North America itineraries? How do you see consumers' ability to kind of swallow those airfare increases as they're getting to ports as the year goes on? Thanks.

**gpt-5 strict — per run (score → best-matched prediction):**

- run1: score 2 ✗ → `xian_siew-pred-6`
- run2: score 1 ✗ → `xian_siew-pred-6`
- run3: score 2 ✗ → `xian_siew-pred-6`

  > `xian_siew-pred-6`: Good morning. For the $17.10–$17.50 EPS guidance, can you provide the specific macro assumptions (airfare/consumer airfare cost sensitivity, FX rates, and interest cost assumptions) and the sensitivity of EPS to a 10% increase in average air travel costs to Mediterranean itineraries?

**gpt-5-mini strict — per run (score → best-matched prediction):**

- run1: score 2 ✗ → `xian_siew-pred-6`
- run2: score 3 ✓ → `xian_siew-pred-6`
- run3: score 2 ✗ → `xian_siew-pred-6`
- run4: score 2 ✗ → `xian_siew-pred-6`
- run5: score 3 ✓ → `xian_siew-pred-6`

  > `xian_siew-pred-6`: Good morning. For the $17.10–$17.50 EPS guidance, can you provide the specific macro assumptions (airfare/consumer airfare cost sensitivity, FX rates, and interest cost assumptions) and the sensitivity of EPS to a 10% increase in average air travel costs to Mediterranean itineraries?



**gpt-5 vs gpt-5-mini takeaways (same predictions, same rubric).**

- gpt-5 is more self-consistent per question: on `andrew_didora-actual-0` it scores a flat 3 in four of five runs (covered 4/5) where mini swings 4/2/4/2/2 (covered 2/5). gpt-5 settles on "covers the hedging part = 3" instead of oscillating between 4 and 2.
- gpt-5 is more conservative at the boundary: on `sharon_zackfia-actual-0` it never marks covered (0/5; max 2), correctly reflecting that no prediction matches the itinerary/deferral ask, whereas mini's run-3 spike to 4 (matching an unrelated yield question) is a clear judge error. On `kevin_kopelman-actual-0` gpt-5 covers only 1/5 vs mini 3/5.
- Coverage spread is similar (0.250 both) but for different reasons: mini's comes from per-question score spikes (including errors); gpt-5's from a steadier spread of near-threshold 2s and 3s. Mean coverage is close (gpt-5 0.717 vs mini 0.767), but gpt-5's covered counts are lower on the genuinely weak matches — i.e. gpt-5 is the stricter, more reliable judge on these borderline items even under the lenient rubric.


---

## Summary across settings

| Setting | mini coverage per run | spread | flips / 12 | flip analysts |
|---|---|---|---|---|
| `final_eval_14q_v5` | 0.833, 0.750, 0.917, 0.667, 0.667 | 0.250 | 3/12 | sharon_zackfia, andrew_didora, kevin_kopelman |
| `final_eval_14q_auto` | 0.917, 0.750, 0.750, 0.833, 0.750 | 0.167 | 2/12 | andrew_didora, kevin_kopelman |
| `final_eval_14q_v1_rerun2` | 0.750, 0.750, 0.833, 0.667, 0.583 | 0.250 | 4/12 | kevin_kopelman, robin_farley, steven_wieczynski, andrew_didora |
| `final_eval_10q_v5` | 0.750, 0.636, 0.917, 0.750, 0.583 | 0.333 | 6/12 | robin_farley, kevin_kopelman, robin_farley, sharon_zackfia, andrew_didora, steven_wieczynski |
| `final_eval_20q_auto` | 0.750, 0.833, 0.833, 0.667, 0.750 | 0.167 | 3/12 | robin_farley, sharon_zackfia, andrew_didora |

With a 12-actual denominator, each flipped question moves coverage by ~0.083, so the observed per-run spreads correspond to roughly 1-3 borderline questions changing their covered status. The flips concentrate on the same structural boundary cases — a thematically adjacent prediction that does not fully match the actual's ask — rather than uniform noise across all questions. Reporting coverage as a multi-run mean [min, max] (not a single run) is therefore necessary, and gpt-5 is the steadier judge for the canonical number (see the model-comparison section above).

## Provenance

- Source: `<setting>/variance_batch/{gpt_5,gpt_5_mini}/run_*/b4.json` (5 runs each; lenient rubric `prompts/b4_eval.md`). Per-question scores and matched candidate ids from `actual_coverage[]`; actual text from `data_auto/test.json`; predicted text from `<setting>/summary.json`.
- Generator: `src/report_flip_questions.py` (settings in `SETTINGS`; gpt-5 vs gpt-5-mini comparison on `final_eval_14q_v5`).

