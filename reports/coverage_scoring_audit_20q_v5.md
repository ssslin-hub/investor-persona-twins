# Coverage scoring audit — `final_eval_20q_v5`

Per actual: matched predicted question + score under single-call strict vs chunked strict (max over chunks). Both gpt-5-mini, `b4_eval_strict.md`. covered = score >= 3.

**Single-call coverage = 0.500; chunked coverage = 0.750.**

| actual | single score | chunked score | inflated? |
|---|---|---|---|
| `matthew_boss-actual-0` | 3 | 3 |  |
| `steven_wieczynski-actual-0` | 2 | 4 | ⚠️ yes |
| `brandt_montour-actual-0` | 3 | 4 |  |
| `james_hardiman-actual-0` | 3 | 3 |  |
| `lizzie_dove-actual-0` | 3 | 3 |  |
| `robin_farley-actual-0` | 0 | 2 |  |
| `robin_farley-actual-1` | 4 | 3 |  |
| `vince_ciepiel-actual-0` | 4 | 4 |  |
| `sharon_zackfia-actual-0` | 1 | 2 |  |
| `andrew_didora-actual-0` | 2 | 4 | ⚠️ yes |
| `xian_siew-actual-0` | 2 | 4 | ⚠️ yes |
| `kevin_kopelman-actual-0` | 1 | 2 |  |


### `matthew_boss-actual-0` — single=3, chunked=3

**ACTUAL:** Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to…

- single-call match (`matthew_boss-pred-5`, score 3): Great, congrats — on Perfecta you’re targeting 20% CAGR to 2027 and high‑teens ROIC; can you decompose that 20% into yield improvement vs cost efficiencies vs JV/other contributions, and tell us how much of that is already captured in the 2…

- chunked match (`james_hardiman-pred-16`, score 3): Perfecta targets a 20% CAGR in Adjusted EPS through 2027 and ROIC in the high teens — can you break that down (roughly) into the contributions from (a) pricing/organic yield, (b) fleet/destination new-build economics, (c) cost savings / AI,…


### `steven_wieczynski-actual-0` — single=2, chunked=4  ⚠️ INFLATED

**ACTUAL:** Yeah. Hey, guys. Good morning. Thanks for all the color so far. Jason, as we think about the rest of the year, we obviously have your second quarter yield guidance, and I have to assume based on Naftali's comments that your third quarter yi…

- single-call match (`steven_wieczynski-pred-3`, score 2): Hey, guys. On the regional headwinds: you mentioned a short-term moderation for Mediterranean and West Coast Mexico and that bookings have since rebounded — how should we think about the yield cadence across Q2 and Q3 specifically, i.e., ho…

- chunked match (`james_hardiman-pred-9`, score 4): You said booked load factor is within historical ranges at record APD — can you walk through the forward booking curve: where APD sits for Q3/Q4 relative to current booked APD, how many cabins remain to sell (in % of deployable inventory), …


### `brandt_montour-actual-0` — single=3, chunked=4

**ACTUAL:** Great. Thanks for taking my question. I just wanted to circle back on the third quarter and the Med, and just maybe if you could put a bit of a finer point on it. You know, how much do you have left to book at this point in the year? How mu…

- single-call match (`brandt_montour-pred-1`, score 3): Good morning — just to follow up on bookings cadence: can you quantify remaining open inventory for Q2/Q3 (in % of sailings or passenger nights), and what percent of current bookings were made within the last 90 days versus more than 90 day…

- chunked match (`james_hardiman-pred-3`, score 4): On the Mediterranean booking moderation and the rebound you referenced: can you quantify how many weeks that softer demand lasted, what percent of Mediterranean inventory/pricing was rerated or cancelled, and the approximate APD/yield drag …


### `james_hardiman-actual-0` — single=3, chunked=3

**ACTUAL:** Good morning, thanks for taking my questions. I wanted to sort of zoom in on the idea that we're turning the corner. Obviously, you know, the weeks following the initial geopolitical disruption were probably the worst, but maybe some indica…

- single-call match (`james_hardiman-pred-3`, score 3): On the Mediterranean booking moderation and the rebound you referenced: can you quantify how many weeks that softer demand lasted, what percent of Mediterranean inventory/pricing was rerated or cancelled, and the approximate APD/yield drag …

- chunked match (`james_hardiman-pred-9`, score 3): You said booked load factor is within historical ranges at record APD — can you walk through the forward booking curve: where APD sits for Q3/Q4 relative to current booked APD, how many cabins remain to sell (in % of deployable inventory), …


### `lizzie_dove-actual-0` — single=3, chunked=3

**ACTUAL:** Hi. Good morning. Thanks for taking the question. I was wondering if you could maybe give us a refresh on Perfect Day Mexico. You mentioned it's opening late 2027, ramping 2028. Could you maybe share some more details on the cadence of that…

- single-call match (`lizzie_dove-pred-6`, score 3): Hi there. Thanks for taking the question. You noted Royal Beach Club Santorini demand has been very strong and Cozumel now expected early 2028—can you quantify the incremental yield or APD lift you've seen from Paradise Island and what you …

- chunked match (`steven_wieczynski-pred-9`, score 3): Hey, guys. On Perfect Day and Royal Beach Clubs — you called out Santorini, Cozumel timing, and Perfect Day Mexico/Costa Maya ramping in early 2028; can you give a near-term numeric anchor for incremental APD or EBITDA uplift per guest (or …


### `robin_farley-actual-0` — single=0, chunked=2

**ACTUAL:** Thanks. I had a question on yields, but also just a quick follow-up. Michael's comment may have just answered it, but, you know, it sounded like Mexico there had been, like, a little bit of a pause in construction because of that environmen…

- single-call match (`None`, score 0): —

- chunked match (`robin_farley-pred-3`, score 2): Okay — Mediterranean and Mexico demand: you noted a short‑term moderation in Med bookings and some West Coast Mexico disruption that have since started to rebound. 1) what is the revenue‑at‑risk (or booked APD loss) from the weeks of softer…


### `robin_farley-actual-1` — single=4, chunked=3

**ACTUAL:** Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a mid-single digit sort…

- single-call match (`robin_farley-pred-1`, score 4): Okay — fuel sensitivity and reconcile. Jason said the outlook 'includes $0.74 per share from fuel headwinds' but you said the remaining year fuel headwind is ~$0.62 and fuel expense is $1.35bn with 59% hedged — 1) can you reconcile the $0.7…

- chunked match (`kevin_kopelman-pred-6`, score 3): Good morning — Q2 Net Yield guidance is only +0.2% with a ~200bp drag from dry docks and geopolitical timing; how should we think about the cadence — do you expect mid‑single to high‑single yield growth in H2 to reach the full‑year 1.5%–2.5…


### `vince_ciepiel-actual-0` — single=4, chunked=4

**ACTUAL:** Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new pr…

- single-call match (`vince_ciepiel-pred-0`, score 4): Naftali, Net Yields were up 2% in Q1 and you raised full-year guidance to +1.5%–2.5% — can you decompose that 2% figure for us into like‑for‑like ticket yield, onboard/mix, and the contribution from new hardware/destinations (e.g., Legend/I…

- chunked match (`james_hardiman-pred-0`, score 4): Hey, good morning — quick one on yields: you tightened full-year Net Yield to 1.5%-2.5% and called out both Mediterranean/Mexico impacts and product-led initiatives (Icons, Beach Clubs). Can you quantify, in $ or bps, how much of the FY yie…


### `sharon_zackfia-actual-0` — single=1, chunked=2

**ACTUAL:** Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there…

- single-call match (`andrew_didora-pred-15`, score 1): Crew travel and airline disruptions were flagged as cost drivers this quarter — are you negotiating long‑term airline or charter agreements to mitigate this, and should we model that as a recurring incremental cost or a transitory impact?

- chunked match (`steven_wieczynski-pred-8`, score 2): Hey, guys. Costs — Net Cruise Costs ex-fuel were better-than-expected in Q1 and you now expect them to be roughly flat or 50 basis points better for the full year: can you split the run-rate improvement between structural initiatives (techn…


### `andrew_didora-actual-0` — single=2, chunked=4  ⚠️ INFLATED

**ACTUAL:** Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a r…

- single-call match (`andrew_didora-pred-1`, score 2): On fuel — you flagged a roughly $0.62 per‑share headwind for the year and that you’re ~59–60% hedged: how should we think about the sensitivity of your EPS guide to a sustained spot environment versus the forward curve, and would you consid…

- chunked match (`vince_ciepiel-pred-3`, score 4): You noted fuel is driving roughly $0.62 of EPS headwind for the year with about 60% (later noted 59%) hedged — can you walk through the hedge profile (tenors, % locked per quarter), the $EPS sensitivity to a $10/mt move in fuel or $0.10/gal…


### `xian_siew-actual-0` — single=2, chunked=4  ⚠️ INFLATED

**ACTUAL:** Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of…

- single-call match (`vince_ciepiel-pred-12`, score 2): On loyalty and the Royal ONE card: cardholder accounts have doubled since 2019 and you think you can double again — what are the economics per cardholder (annual net revenue, take rate on bookings, incremental yield), the expected payback p…

- chunked match (`lizzie_dove-pred-19`, score 4): Hi there. Thanks for taking the question. Finally, given digital penetration has more than doubled and monthly active users are 5x 2019 levels, what incremental margin or yield uplift do you expect from higher pre‑cruise purchases and the R…


### `kevin_kopelman-actual-0` — single=1, chunked=2

**ACTUAL:** Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North America for your North …

- single-call match (`andrew_didora-pred-15`, score 1): Crew travel and airline disruptions were flagged as cost drivers this quarter — are you negotiating long‑term airline or charter agreements to mitigate this, and should we model that as a recurring incremental cost or a transitory impact?

- chunked match (`steven_wieczynski-pred-18`, score 2): Hey, guys. Operational risk and air disruption — given the comment that airline capacity reductions and flight disruptions impacted Mediterranean demand and crew travel raised costs, are you instituting any changes to guest air programs, pr…

