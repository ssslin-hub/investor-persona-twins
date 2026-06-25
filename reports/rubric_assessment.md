# Rubric Assessment — Is the 0-4 B4 Scoring Reasonable for Analyst Question Prediction?

After reading 20 examples each of scores 1, 2, 3 (60 evaluator outputs total) from gpt-5 B4 runs on v5 K=10 holdout evals, here is my analytical assessment.

Full example dump: `reports/rubric_quality_review.md` (64 KB, all 60 examples with reasoning).

## TL;DR

The rubric is **structurally sound but operationally inconsistent**. The 5-level taxonomy (0/1/2/3/4) maps cleanly to plausible categories ("no relation" → "very close substitute"), but:

1. **Score 3 is over-broad** — covers both "would substitute" (true ✓) and "same broad topic but different question" (should be 2).
2. **Same (candidate, actual) pair can flip 1 ↔ 3 across runs** — at least one such case found in our 60-example dump (Brandt's Q1 yield split → Vince's new hardware question: rated 3 in one run, 1 in another).
3. **The "wrong trigger" criterion for score 2 is doing real work** — a clear majority of score-2 cases legitimately have right topic / wrong trigger.
4. **Score 1 is the cleanest level** — these are mostly defensible "same business area, different question."
5. **The covered-at-3 cutoff is too generous for our application** — many score 3s are "topically adjacent, won't actually substitute." If Ozan's downstream user is the IR team preparing answers, a generous cutoff over-promises coverage.

---

## Score-by-Score Analysis

### Score 3 — "substantially similar question target with some phrasing/granularity diff" (binary=True ✓)

**My verdict**: roughly **half of score 3s are defensible substitutes**, the other half are **stretches** that probably should be 2.

#### Defensible 3s (would actually substitute)
- **3.10** (vince → brandt, Med disruption): "Quantify peak APD/load impact in Q2/Q3 from Med/W.Coast" vs "How much do you have left to book... how much damage was done" — both ask for Med disruption quantification. Strong 3, possibly 4. ✓
- **3.3** (vince → andrew, fuel hedging): predicted asks for hedge coverage + EPS sensitivity; actual asks "how do you think about rolling new hedges?" Different framing, same target. ✓
- **3.6** (robin → andrew, same): same pattern, defensible 3. ✓
- **3.14** (brandt → robin, Med size of yield reduction): predicted quantifies Med/Mex on yield range; actual asks "is the 100bps change a mid-single-digit Euro shift". Both reach for size of Med impact on yield. ✓

#### Stretches that should be 2
- **3.1** (kevin → sharon, cost): predicted asks "Q2 cost timing vs structural"; actual asks "are you making itinerary changes given higher fuel? Have you pulled back spend?" — only word "cost" overlaps. The actual is about strategic responses to fuel; the predicted is about Q2 cost cadence. **Different ask.** Should be 2.
- **3.5** (steven → lizzie, Beach Club): predicted asks "incremental yield/EBITDA per pax + capex cadence"; actual asks "ramp cadence + Western Caribbean structural yield + Galveston/Texas catchment". Topically adjacent (both about Perfect Day Mexico ramp), but the actual is a regional/macro question and the predicted is a unit-economics question. Borderline 2/3.
- **3.7** (kevin → james, booking): predicted asks "current booked LF + APD vs close-in"; actual asks "where are we today vs February?" — actual is direction/trajectory, predicted is point-in-time levels. Should be 2.
- **3.15** (james → matthew, Perfecta): predicted asks specific Perfecta 20% CAGR decomp by lever; actual asks "drivers of durable multi-year growth vs pre-pandemic". The actual is conceptual/qualitative; predicted is quantitative decomposition. Both touch durable growth but ask very different things. Should be 2.
- **3.18** (lizzie → vince, new ship pricing): predicted asks "quantify Legend/Icon APD premium vs like-for-like"; actual asks "how new hardware contributes to yield + does Europe yield grow?" Both touch new hardware contribution but actual has a major regional sub-question the predicted doesn't address. Borderline.

**Pattern**: many score 3s are "predicted is overly specific compared to actual broad question" — they share a topic but the predicted wouldn't actually be asked in the conversation that produced the actual. From an IR-coverage POV they don't substitute.

### Score 2 — "partial theme match but wrong trigger or different ask" (binary=False)

**My verdict**: **mostly well-judged**. Score 2 is the rubric's hardest-working level and the LLM uses it correctly in ~80% of cases.

#### Clean 2s
- **2.1** sharon cost timing vs sharon itinerary-fuel changes: same broad cost topic but actual asks strategic responses to fuel, predicted asks Q2 cost cadence. Clear 2. ✓
- **2.7** sharon demographics → xian loyalty/repeat: predicted asks "millennial vs older cohort spend"; actual asks "loyalty implications on yield/onboard". Both customer-mix theme but very different ask. ✓
- **2.17** vince Med/W.Coast change vs January → brandt "how much left to book": both Med-related but predicted asks delta vs January guide; actual asks current level/trajectory. Defensibly 2. ✓
- **2.19** lizzie digital lift → xian loyalty: predicted asks digital/AI quantitative lift; actual asks loyalty impact. Same yield theme, different lever. ✓

#### Questionable 2s
- **2.4** steven cost timing vs sharon itinerary-fuel: nearly identical to **2.1** which the evaluator also called 2. Consistent.
- **2.13** kevin dry-dock EBITDA drag → andrew NCC ex-fuel inflation threshold: both NCC topic but predicted is dry-dock-specific, actual is "what level of capacity growth triggers NCC ex-fuel inflation." Might be 1 (different sub-topic).

### Score 1 — "same broad business area only" (binary=False)

**My verdict**: **the cleanest level — almost all defensible**.

#### Clean 1s
- **1.8** brandt capital allocation thresholds → matthew "durable multi-year growth" — different domain entirely. ✓
- **1.9, 1.19** TUI/JV specifics → costs/hedging questions — different sub-area within "financials." ✓
- **1.20** steven balance sheet/leverage targets → matthew growth durability — different domain. ✓
- **1.10, 1.11, 1.12, 1.17** AI/digital quantification → loyalty (xian) or durable growth (matthew) — adjacent themes, different asks. ✓

#### Inconsistencies (same content scored differently elsewhere)
- **1.6** (brandt Q1 yield split + 2019 gap → vince new hardware/regional) is rated **1**, but **3.4** is the exact same prediction → same actual rated **3**. Δ = 2 across runs on the same (predicted, actual) pair.

  This is a **critical finding**: the evaluator's gpt-5 output on this borderline case flips between "broadly related" (score 1) and "substantially similar" (score 3) depending on the sampling realization. Our other variance analyses show this pattern at lower frequency, but two diametrically opposite scores on the same pair is more than typical noise.

---

## Three Structural Issues With the Rubric

### 1. Score 3 is two distinct things conflated
The rubric definition for 3 reads "substantially similar question target with some phrasing/granularity differences." In practice, the evaluator applies it to two different situations:
- **Real substitutability**: predicted question, when answered, would address the actual's information need (e.g., 3.10 Med quantification).
- **Topic adjacency**: predicted shares topic vocabulary but answers a different question (e.g., 3.1 cost timing vs strategic fuel response).

The second case isn't really "substantially similar question target" — it's "same business area + different ask," which by rubric is score 2. Yet the evaluator routinely scores these as 3 because they're "about cost" or "about Med" at the topic level.

**Fix proposal**: tighten score 3 wording to "would substitute for the actual question in a downstream Q&A summary." This raises the bar and lowers cov rates, but means score≥3 becomes a more honest binary.

### 2. The 2↔3 boundary is the noise-source
Phase 6 already measured this: ~3/12 cells flip across runs under gpt-5. The 1.6 vs 3.4 case shows the worst is 1↔3 (skips a level entirely). Mini is even worse here (Phase 28).

**Fix proposal**: report B4 cov as both "score≥3 cov" (current) AND "score=4 cov" (strict). The score=4 cov is much more stable across runs because the rubric anchor "very close match; would substitute" is harder to mistake.

### 3. The "wrong trigger" criterion in score 2 is overloaded
Score 2 says "partial theme match but wrong trigger OR different ask." But "wrong trigger" and "different ask" are two distinct concepts:
- **Wrong trigger**: predicted question is about Mediterranean disruption, actual is also about Mediterranean disruption, but predicted asks about September inventory while actual asks about June bookings — same trigger, different sub-detail.
- **Different ask**: predicted asks for quantification, actual asks for qualitative narrative — same trigger, different question shape.

Both get score 2 today, but they're qualitatively different misses. Splitting them might help diagnose simulator failures.

---

## Is the rubric "reasonable for analyst question prediction"?

**Yes, with caveats**:

1. ✓ **The 5-level taxonomy is intuitive** and maps to plausible decision points.
2. ✓ **The "covered = score ≥ 3" cutoff is a sensible default** for "did we catch this actual?" — but it's lenient enough that ~30-40% of score 3s are topic-adjacent rather than truly substitutable. Consider also reporting score≥4 ("strict cov") for high-stakes use cases.
3. ⚠ **Cross-run consistency on the 2↔3 boundary is the main weakness**. Multiple runs + mean is needed; single-run cov has ~±0.15 noise from this alone.
4. ⚠ **Same-pair flip 1↔3 (case 1.6/3.4) suggests gpt-5 occasionally jumps two levels** — extreme but documented. A pair-wise sanity check (re-rate the lowest-scored 5-10% of cells to find outliers) could catch these.
5. ❌ **For Ozan's "the set of questions matters more than who asks them" framing**, score 3 is too generous. If the downstream user is IR teams that need to prepare specific answers, "topic adjacent" doesn't help them — only true substitutes do. Recommend defaulting to score≥4 as the "useful for IR" threshold and score≥3 as "topic-aware coverage."

## Recommendations

| Use case | Recommended threshold |
|---|---|
| **Research metric (current default)** | score ≥ 3 (cov rate) |
| **Production IR-team output** | score ≥ 4 (strict substitute) |
| **Diagnostic (find borderline)** | score = 3 cells only — these are the "topic adjacent" set |
| **Stability** | always report 5-run mean with min/max range, not single-run |

If we ship a number to Ozan, report both `cov≥3` and `cov≥4` so he can see the gap between "we touched the topic" and "we predicted a substitute."
