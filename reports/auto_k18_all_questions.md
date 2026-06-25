# auto K18 — chunked strict B4, all 12 questions (mini vs gpt-5 picks)

Config: `final_eval_18q_auto` (auto persona, K=18, seed-1). Pool = 198 candidates → 4 chunks of ≤50.
Method: strict rubric (`b4_eval_strict.md`), chunked, max match-score per actual across chunks; covered = score ≥ 3.

**chunked mini coverage = 1.000 (12/12) — gpt-5 coverage = 0.583 (7/12).**
mini hits 12/12 because, with 4 chunks per actual and a lenient judge, every actual gets at least one chunk that awards ≥3 to a topic-adjacent candidate. gpt-5 rejects 5 of these as topic-overlap, not substitution.

## Summary table

| # | actual | mini score | gpt-5 score | mini inflated? |
|---|---|---|---|---|
| 1 | `matthew_boss-actual-0` | 3 | 3 |  |
| 2 | `steven_wieczynski-actual-0` | 4 | 4 |  |
| 3 | `brandt_montour-actual-0` | 4 | 3 |  |
| 4 | `james_hardiman-actual-0` | 3 | 2 | ⚠️ yes |
| 5 | `lizzie_dove-actual-0` | 4 | 4 |  |
| 6 | `robin_farley-actual-0` | 3 | 1 | ⚠️ yes |
| 7 | `robin_farley-actual-1` | 4 | 2 | ⚠️ yes |
| 8 | `vince_ciepiel-actual-0` | 4 | 3 |  |
| 9 | `sharon_zackfia-actual-0` | 4 | 2 | ⚠️ yes |
| 10 | `andrew_didora-actual-0` | 4 | 3 |  |
| 11 | `xian_siew-actual-0` | 4 | 4 |  |
| 12 | `kevin_kopelman-actual-0` | 3 | 2 | ⚠️ yes |

---

## 1. `matthew_boss-actual-0` — mini=3, gpt-5=3

**ACTUAL QUESTION:**
> Great. Thanks. Jason, maybe if we take a step back. Despite geopolitical developments and the elevated industry capacity in the Caribbean, your yield guide at the high end this year stands at 2.5% constant currency. Maybe could you speak to the drivers of durable growth multi-year, which seem intact here regardless of the macro, and just how you see the company set up today relative to pre-pandemic?

**MINI best match** (`matthew_boss-pred-6`, score 3):
> On the Perfecta program and your 20% CAGR Adjusted EPS through 2027 / high‑teens ROIC target: what's the bridge — i.e., how many bps of margin expansion, APD lift, and cost savings are you assuming annually, and are there specific milestones where you expect that trajectory to accelerate?

**GPT-5 best match** (`andrew_didora-pred-11`, score 3):
> Naftali/Jason — Perfecta targets a 20% CAGR in Adjusted EPS through 2027 and ROIC in the high teens — what are the top three levers you assume (yield, cost, capital returns) in your internal model and what portion of the target is reliant on yield mix versus structural cost savings or buybacks?

---

## 2. `steven_wieczynski-actual-0` — mini=4, gpt-5=4

**ACTUAL QUESTION:**
> Yeah. Hey, guys. Good morning. Thanks for all the color so far. Jason, as we think about the rest of the year, we obviously have your second quarter yield guidance, and I have to assume based on Naftali's comments that your third quarter yields are gonna look somewhat similar to your second quarter given the exposure you have to Europe. You know, then if that's true, that would imply your fourth quarter yields are gonna be growing, you know, let's call it somewhere in that mid-single- digit range to kinda get you into that 2%, you know, midpoint. You know, wondering what gives you the confidence the fourth quarter could grow that much. I guess then that actually to me would imply, that without the European headwinds you guys encountered, you know, you guys would've actually been able to raise your full year yield guidance. Am I kinda thinking about that all the right way?

**MINI best match** (`matthew_boss-pred-11`, score 4):
> Q2 guidance shows only ~0.2% Net Yield growth while full year is 1.5%–2.5% — can you walk through the quarter‑by‑quarter cadence, how much of Q2 is transitory (drydock/crew travel/air disruption) versus permanent yield loss, and the sensitivity to Europe/Mediterranean recovery timing?

**GPT-5 best match** (`matthew_boss-pred-11`, score 4) (SAME candidate as mini):
> Q2 guidance shows only ~0.2% Net Yield growth while full year is 1.5%–2.5% — can you walk through the quarter‑by‑quarter cadence, how much of Q2 is transitory (drydock/crew travel/air disruption) versus permanent yield loss, and the sensitivity to Europe/Mediterranean recovery timing?

---

## 3. `brandt_montour-actual-0` — mini=4, gpt-5=3

**ACTUAL QUESTION:**
> Great. Thanks for taking my question. I just wanted to circle back on the third quarter and the Med, and just maybe if you could put a bit of a finer point on it. You know, how much do you have left to book at this point in the year? How much damage do you think was done over the last few weeks? What are you sort of baking into your forward guidance in terms of how the conflict plays out and how bookings play out from here?

**MINI best match** (`james_hardiman-pred-6`, score 4):
> Good morning — regarding the Mediterranean and West Coast Mexico demand disruption: can you quantify the magnitude of the booking moderation (bps of APD or absolute $s), the duration, whether it was cancellations or just slower new bookings, and what specific commercial levers you used to accelerate the rebound you described?

**GPT-5 best match** (`steven_wieczynski-pred-2`, score 3):
> You flagged a moderation in Mediterranean and West Coast Mexico bookings that has since begun to rebound — can you quantify the magnitude of the pullback (ppt of load factor or $ APD) and tell us how much of the 'recent weeks' rebound is realized in current booked APD/prices?

---

## 4. `james_hardiman-actual-0` — mini=3, gpt-5=2 — ⚠️ MINI INFLATED

**ACTUAL QUESTION:**
> Good morning, thanks for taking my questions. I wanted to sort of zoom in on the idea that we're turning the corner. Obviously, you know, the weeks following the initial geopolitical disruption were probably the worst, but maybe some indication of where we stand today in terms of the booking trajectory versus where we were in February before a lot of this started. I don't know if we're fully back or we're just heading in that direction. As we think about sort of the 2Q and 3Q, we're saying that's most pronounced. I'm just curious if that's because those are what's next or whether consumers are comfortable booking beyond the third quarter and into 2027, assuming that, you know, this disruption will go away or we'll sort of worry about that when we get to that point in time. Thanks.

**MINI best match** (`steven_wieczynski-pred-2`, score 3):
> You flagged a moderation in Mediterranean and West Coast Mexico bookings that has since begun to rebound — can you quantify the magnitude of the pullback (ppt of load factor or $ APD) and tell us how much of the 'recent weeks' rebound is realized in current booked APD/prices?

**GPT-5 best match** (`brandt_montour-pred-1`, score 2):
> Thanks — on booking curves: you noted bookings for Mediterranean moderated then have rebounded and commented that you’re seeing improved demand for limited inventory; can you quantify how close‑in bookings (0‑30 days) versus forward bookings (90+ days) trended versus last year and how that’s affecting your ability to manage APD and deploy pricing actions?

---

## 5. `lizzie_dove-actual-0` — mini=4, gpt-5=4

**ACTUAL QUESTION:**
> Hi. Good morning. Thanks for taking the question. I was wondering if you could maybe give us a refresh on Perfect Day Mexico. You mentioned it's opening late 2027, ramping 2028. Could you maybe share some more details on the cadence of that ramp? You know, just bigger picture, your latest thinking around the long-term, you know, structural yield growth opportunity there in the Western Caribbean market and particularly around, you know, the Galveston, Texas penetration opportunity.

**MINI best match** (`steven_wieczynski-pred-12`, score 4):
> You mentioned Royal Beach Club Santorini demand is very strong and that Cozumel is now expected in early 2028 with Perfect Day Mexico/Costa Maya ramping in 2028 — can you quantify the expected APD/yield uplift from these private‑destination assets at maturity and the cadence of their earnings contribution between 2026–2028?

**GPT-5 best match** (`matthew_boss-pred-10`, score 4):
> You continue to invest in private destinations (Santorini, Cozumel, Perfect Day Mexico/Costa Maya) — two parts: what are your ramp assumptions for APD and occupancy/yield uplift for each site through the first three years, and what capital spend and margin profile should we assume for these assets?

---

## 6. `robin_farley-actual-0` — mini=3, gpt-5=1 — ⚠️ MINI INFLATED

**ACTUAL QUESTION:**
> Thanks. I had a question on yields, but also just a quick follow-up. Michael's comment may have just answered it, but, you know, it sounded like Mexico there had been, like, a little bit of a pause in construction because of that environmental stuff. Just wanna clarify if Michael's comment means that construction is, you know, resumed in Mexico there.

**MINI best match** (`robin_farley-pred-11`, score 3):
> Royal Beach Club / destinations — Santorini demand is ‘very strong’ and Paradise Island is benefitting yields: how much incremental APD or margin contribution does a mature Beach Club site deliver versus a standard port call, and when do you model Cozumel and Perfect Day Mexico/Costa Maya reaching steady state contribution?

**GPT-5 best match** (`steven_wieczynski-pred-12`, score 1):
> You mentioned Royal Beach Club Santorini demand is very strong and that Cozumel is now expected in early 2028 with Perfect Day Mexico/Costa Maya ramping in 2028 — can you quantify the expected APD/yield uplift from these private‑destination assets at maturity and the cadence of their earnings contribution between 2026–2028?

---

## 7. `robin_farley-actual-1` — mini=4, gpt-5=2 — ⚠️ MINI INFLATED

**ACTUAL QUESTION:**
> Great. Thank you. Thank you. The other question was just sort of thinking about next year and, you know, if it's the 200 basis points impact in Q2, Q3 sounds like, you know, the entire 100 basis point change is maybe a mid-single digit sort of shift in where you had expected European yields to come, to come in this year. Is it fair to assume that you would kind of fully expect that to come back in 2027 when we're kind of thinking ahead to, you know, the impact this year being kind of, you know, not necessarily coming out of next year? Just help us to size that. Thank you.

**MINI best match** (`matthew_boss-pred-11`, score 4):
> Q2 guidance shows only ~0.2% Net Yield growth while full year is 1.5%–2.5% — can you walk through the quarter‑by‑quarter cadence, how much of Q2 is transitory (drydock/crew travel/air disruption) versus permanent yield loss, and the sensitivity to Europe/Mediterranean recovery timing?

**GPT-5 best match** (`matthew_boss-pred-11`, score 2) (SAME candidate as mini):
> Q2 guidance shows only ~0.2% Net Yield growth while full year is 1.5%–2.5% — can you walk through the quarter‑by‑quarter cadence, how much of Q2 is transitory (drydock/crew travel/air disruption) versus permanent yield loss, and the sensitivity to Europe/Mediterranean recovery timing?

---

## 8. `vince_ciepiel-actual-0` — mini=4, gpt-5=3

**ACTUAL QUESTION:**
> Thanks. Just wanted to dig a little bit more into yield outlook for the year. Could you maybe comment on how you think new hardware, you have Star , Xcel contribution, Paradise Island, RBC Santorini, like a lot of, you know, exciting new products out there, how they might be contributing to the yield growth overall versus the like- for-L ike impact. Also on a regional basis, I think you had mentioned or used the term that Europe was doing well, I think was the quote. Is it fair to assume that Europe yields will grow this year? What does the guide assume? Thanks.

**MINI best match** (`lizzie_dove-pred-0`, score 4):
> Hi, good morning — a two-parter on yields: first, can you decompose the Q1 net yield beat (Q1 net yields +2%) between like‑for‑like pricing/onboard mix versus contributions from new hardware and private‑destination premiums (points or % APD)? And second, how much of the 2026 net yield guidance (1.5%–2.5%) explicitly assumes the incremental yield from Legend/Beach Clubs and Icon deployment versus underlying like‑for‑like pricing?

**GPT-5 best match** (`brandt_montour-pred-0`, score 3):
> Good morning, and congrats on the quarter — quick one on yields: you finished Q1 with Net Yield +2% and you’re guiding 2026 Net Yield to +1.5%-2.5%. Can you walk us through a clear puts‑and‑takes bridge from the Q1 momentum to the full‑year midpoint (APD/pricing vs load, regional mix, Royal Beach Club/Icon pricing, and the specific drag from Mediterranean & W. Mexico)?

---

## 9. `sharon_zackfia-actual-0` — mini=4, gpt-5=2 — ⚠️ MINI INFLATED

**ACTUAL QUESTION:**
> Hi. Thanks for taking the question. I guess I wanted to follow up on cost. Are you making any itinerary changes given higher fuel either currently or looking out to 2027, 2028? Obviously, Net Cruise Costs are coming in a bit lower. Is there anything you've pulled back on this year in terms of initiatives or spend that we should think of as deferring to 2027? Is this just harvesting some of those efficiencies that you just referred to? Thank you.

**MINI best match** (`vince_ciepiel-pred-11`, score 4):
> Thanks — on fuel you said FY fuel expense of $1.35bn and that remaining 2026 consumption is ~59% hedged, yet guidance is based on spot; can you give the EPS sensitivity per $10 change in Brent or per $0.10/gal marine fuel, confirm the $0.62/$0.74 per‑share headwind math, and your near‑term hedging intentions?

**GPT-5 best match** (`matthew_boss-pred-2`, score 2):
> Nice execution on costs this quarter — can you unpack Net Cruise Costs ex‑fuel for the year: what are the specific line‑item drivers you expect to be flat (labor, stores, food, tech), and quantify the bps improvement you expect from efficiency/AI initiatives versus one‑time timing effects like drydocks?

---

## 10. `andrew_didora-actual-0` — mini=4, gpt-5=3

**ACTUAL QUESTION:**
> Hi, good morning, everyone. T wo quick questions on costs, you know, so I guess for Naftali. I guess, one, you know, how do you think of rolling in new hedges in this high fuel environment? Second, just on unit costs. You continue to do a really nice job here. I guess my question is, at what level of capacity growth would we start to see maybe more inflationary type, you know, NCC ex-fuel growth and say, I don't know, 2%-3% range? Just curious your thoughts up there. Thank you.

**MINI best match** (`andrew_didora-pred-1`, score 4):
> Naftali, on fuel — you said ~59% (CFO) / ~60% (Jason) hedged for the remainder of 2026 and that fuel is a ~$0.62 headwind (and $0.74 when including JV impact); what is the mix of hedges (swaps vs options), what strike/tenor profile are you carrying, and do you have a trigger or plan to add incremental hedges given current spot levels?

**GPT-5 best match** (`matthew_boss-pred-17`, score 3):
> Last one — given you said fuel expense would be ~4% lower if priced off the forward curve, do you intend to alter your hedging stance for the remainder of 2026/2027, and can you outline the policy (percent hedged by quarter and decision triggers) so we can model fuel volatility?

---

## 11. `xian_siew-actual-0` — mini=4, gpt-5=4

**ACTUAL QUESTION:**
> Hi, guys. Thanks for the question. You talked about the co-branded credit card and several changes to the loyalty program, also how repeat guests are kind of stepped up. I'm kind of wondering what do you think is kind of the implications of that in terms of how they could impact net yield growth, maybe repeat guests are booking further ahead, maybe they spend more on onboard. Kind of any learnings on how, you know, higher repeat penetration could be. Thank you.

**MINI best match** (`matthew_boss-pred-16`, score 4):
> Two quick numbers on the Royal ONE card and loyalty: you said cardholder accounts doubled since 2019 and you think you can double again — what's the assumed incremental APD/annualized spend per cardholder you bake into your TAM, and what economics (take rate / breakage) drive that doubling assumption?

**GPT-5 best match** (`brandt_montour-pred-8`, score 4):
> You noted an increase in younger guests (millennials and younger) and more repeat guests — are these cohorts booking earlier or later, spending more per night, and how does their behavior differ across channels (app vs web vs travel agent) — any implications for your yield curve and merchandising strategy?

---

## 12. `kevin_kopelman-actual-0` — mini=3, gpt-5=2 — ⚠️ MINI INFLATED

**ACTUAL QUESTION:**
> Great. Thanks a lot. I had a question on North American customers and higher airfares. Can you talk at all, you know, have you seen any consumer behavior change at all kind of reacting to the higher airfares in North America for your North America itineraries? How do you see consumers' ability to kind of swallow those airfare increases as they're getting to ports as the year goes on? Thanks.

**MINI best match** (`matthew_boss-pred-15`, score 3):
> You called out airline capacity reductions and higher air costs as a driver of Mediterranean softness — how are you integrating air connectivity into pricing and marketing decisions (e.g., packaged vs. unbundled), and how much of ticket yield is at risk if airline headwinds persist?

**GPT-5 best match** (`matthew_boss-pred-15`, score 2) (SAME candidate as mini):
> You called out airline capacity reductions and higher air costs as a driver of Mediterranean softness — how are you integrating air connectivity into pricing and marketing decisions (e.g., packaged vs. unbundled), and how much of ticket yield is at risk if airline headwinds persist?

---

