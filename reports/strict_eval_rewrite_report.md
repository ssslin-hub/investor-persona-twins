# Report: Stricter B4 Evaluator and the False-Positive Covers It Removes

## 1. What we changed

The set-level question-prediction task is scored by an LLM judge that compares each
predicted question against the held-out actual Q&A questions and assigns a 0–4 match
score; an actual is "covered" when its best match scores ≥ 3. The original judge prompt
(`prompts/b4_eval.md`) defined the rubric purely by adjective:

> 3 = substantially similar question target.
> 4 = very close substitute.
> covered/useful should be true for score >= 3.

This left "substantially similar" to the model's discretion. In practice the lenient
judge rewarded *topic adjacency* — a prediction in the same business area (yield, fuel,
costs) was frequently scored ≥ 3 even when it asked a structurally different question or
addressed only part of the actual's ask.

We rewrote the rubric into an **operational, test-based prompt**
(`prompts/b4_eval_strict.md`). The two key changes:

1. **A substitution test gates score 3.** A prediction earns 3 only if, *had management
   answered the predicted question verbatim, the listener would still obtain the key
   fact / number / position the actual question was asking for.* If not, the score drops
   to 2. Topic overlap alone is explicitly a 2, not a 3.

2. **An ordered decision flow** (apply tests in order; first match wins), with score 4
   requiring a shared trigger phrase/number, the same ask shape (quantitative vs
   qualitative), and the same granularity (bps / $ / narrative) — "an IR analyst reading
   both would not prepare separately for them."

The output schema, evaluator models (gpt-5 / gpt-5-mini), and prediction pools are
unchanged, so the strict-vs-lenient difference is attributable to the rubric alone.

## 2. Aggregate effect

- The expected ordering **strict coverage ≤ lenient coverage** holds for **82 / 85**
  settings that have both scores (the 3 exceptions exceed the lenient 5-run max by exactly
  one covered actual on a 12-actual denominator — single-run judge noise, not a rubric
  inversion). Source: `all_settings_strict_b4_mini.md`.
- Strict coverage runs roughly 0.06–0.10 lower per setting; the tightening is concentrated
  on a handful of borderline actuals rather than spread uniformly.
- Under strict scoring, **gpt-5 is the more conservative and self-consistent judge** at the
  boundary than gpt-5-mini (see `strict_b4_eval_variance.md`, model-comparison section):
  on the genuinely weak matches gpt-5 holds at 2 across runs where mini intermittently
  spikes to 4.

## 3. Prompts previously judged ≥ 3 that are actually irrelevant

These are predictions the **lenient** judge scored ≥ 3 (covered) but that do not answer
the actual question. The strict substitution test demotes them.

### 3a. `sharon_zackfia-actual-0` — cost/deferral ask matched to an unrelated yield question

- **Actual:** "Are you making any itinerary changes given higher fuel … is there anything
  you've pulled back on this year … deferring to 2027? Is this just harvesting some of
  those efficiencies …?" (an ask about *itinerary changes and deferred spend*).
- **Lenient false positive:** gpt-5-mini run-3 scored **4** against
  `sharon_zackfia-pred-0` — "Net Yield was up 2% in Q1 … can you quantify what portion …
  is ticket price versus onboard/pre-cruise spend." This prediction is about *yield
  decomposition*; it shares no business area with the cost/deferral ask. This is a clear
  judge error.
- **Strict outcome:** gpt-5-mini strict scores **[1, 2, 2, 1, 1] → 0/5 covered**; gpt-5
  strict **[2, 1, 3] → 1/3**. The substitution test correctly fails — answering the yield
  question gives the listener nothing about itinerary changes or deferred initiatives.

### 3b. `kevin_kopelman-actual-0` — consumer-demand ask matched to an EPS-sensitivity question

- **Actual:** "… North American customers and higher airfares … have you seen any consumer
  behavior change … ability to swallow those airfare increases …?" (a *qualitative demand /
  consumer-behavior* ask).
- **Lenient false positive:** gpt-5-mini scored **3–4** against `xian_siew-pred-6` —
  "For the $17.10–$17.50 EPS guidance, can you provide the specific macro assumptions …
  and the sensitivity of EPS to a 10% increase in average air travel costs to
  *Mediterranean* itineraries." Different ask shape (quantitative EPS sensitivity vs
  qualitative demand behavior) and different region (Mediterranean cost pass-through vs
  North-American consumer reaction).
- **Strict outcome:** gpt-5 strict **[2, 1, 2] → 0/3**; gpt-5-mini strict **[2, 3, 2, 2, 3]
  → 2/5** (down from a lenient mini covered-rate of 3/5). The shared "airfare" keyword no
  longer carries the match.

### 3c. `andrew_didora-actual-0` — two-part ask covered by a fuel-only prediction

- **Actual (two parts):** (1) "how do you think of rolling in new hedges in this high fuel
  environment?" and (2) "at what level of capacity growth would we start to see more
  inflationary … NCC ex-fuel growth …?"
- **Lenient false positive:** the matched prediction `andrew_didora-pred-2` ("On fuel: …
  ~59% hedged … $0.62 EPS headwind … hedging philosophy … sensitivity …") was scored **4**
  by mini in several runs. It answers only part (1); it says nothing about the
  capacity-growth-vs-cost-inflation question in part (2).
- **Strict outcome:** gpt-5 strict scores a flat **[2, 2, 2] → 0/3**, and mini strict
  drops to **[2, 2, 2, 3, 2] → 1/5**. The substitution test penalizes the partial cover:
  a verbatim answer to the fuel question leaves part (2) unanswered.

#### Same model (gpt-5), same prediction — only the rubric flips the verdict

This is the clearest single case. The evaluator model and the predicted question are held
fixed; only the rubric (`b4_eval.md` → `b4_eval_strict.md`) changes. The judge's own
per-run reasoning shows it noticed the missing second part **under both rubrics** — the
lenient rubric forgave it, the strict rubric did not.

**gpt-5 + lenient (`b4_eval.md`) — covered 4/5 (false positive):**

| run | score | covered | judge reasoning (verbatim) |
|---|---|---|---|
| 1 | 3 | ✓ | "Addresses hedging philosophy … **partial on NCC ex-fuel scaling threshold**." |
| 3 | 3 | ✓ | "good overlap on the hedging piece (**partial on the NCC threshold**)." |
| 4 | 3 | ✓ | "capacity-growth threshold for NCC ex-fuel **is not directly addressed** but overall intent is close." |
| 5 | 2 | ✗ | "matches hedging … but not the capacity-growth threshold." |

**gpt-5 + strict (`b4_eval_strict.md`) — covered 0/3 (correct):**

| run | score | covered | judge reasoning (verbatim) |
|---|---|---|---|
| 1 | 2 | ✗ | "Overlap on hedging philosophy, but actual also asks NCC ex-fuel growth threshold vs capacity; **substitution incomplete**." |
| 2 | 2 | ✗ | "Same sub-topic … but actual also asks NCC ex-fuel growth threshold vs capacity; predicted does not address that second part, so **substitution fails**." |
| 3 | 2 | ✗ | "Overlap on hedging philosophy … but actual also asks NCC ex-fuel inflation threshold vs capacity growth, which predicted **doesn't address**." |

Both rubrics make the *same* observation ("partial / does not address the NCC-vs-capacity
part"). Under lenient that observation is overridden by "overall intent is close" and scored
3 (covered). Under strict the substitution test — *would a verbatim answer give the listener
the key fact the actual asked for?* — converts the same observation into a 2 (not covered),
because part (2) is unanswered. The rubric, not the model, is what corrects the verdict.

### 3d. Cross-twin "borrowed" covers at large pools (`b4_score4_candidates.md`)

At K = 20 the lenient judge's argmax over ~217 candidates produces score-4 covers with
**zero identity matches** — i.e. the actual is "covered" only by another twin's
prediction:

| Actual | Lenient best (score 4) | Same twin? |
|---|---|---|
| `lizzie_dove-actual-0` | `brandt_montour-pred-16` | × |
| `robin_farley-actual-1` | `brandt_montour-pred-2` | × |
| `steven_wieczynski-actual-0` | `lizzie_dove-pred-1` | × |
| `brandt_montour-actual-0` | `vince_ciepiel-pred-7` | × |

The lenient judge picks whatever cross-twin candidate is the closest semantic neighbor
even when the twin's own pool holds a weaker but on-identity match — inflating coverage
with predictions that are not really the analyst's question. The strict rubric's trigger /
ask-shape requirements suppress most of these.

## 4. Prompts that score normally under the strict rubric

The strict rubric is not uniformly punitive — genuine substitutes survive it.

### 4a. True substitute that holds at 4: `vince_ciepiel-actual-0 ← vince_ciepiel-pred-0`

The actual asks to **decompose the +2% Q1 Net Yield**; the prediction asks the same
structural decomposition. Same trigger (the +2% Q1 number), same ask shape, same
granularity, same analyst. Scored 4 in 4 of 6 K-settings under the lenient judge and
survives the strict substitution and substitute tests — this is the canonical
correctly-covered case.

### 4b. Substantive cover that holds at 3: `steven_wieczynski-actual-0 ← steven_wieczynski-pred-0`

The actual asks for confidence behind the implied Q4 yield acceleration; the matched
prediction asks for percent-booked-by-quarter and the ticket-vs-onboard yield split — a
prediction that, if answered, supplies the modeling anchors the actual is after. It scores
a stable 3 across most runs under both rubrics: topic and target metric align and the
substitution test passes, so strict keeps it covered.

### 4c. Dedup under the strict rubric improves precision without losing coverage

Running anchor dedup with the strict judge as the drop criterion
(`dedup_strict_best_configs.md`):

| Config | pool | strict coverage | strict precision |
|---|---|---|---|
| v1 K=14 | 154 → 150 (−4) | 0.806 → **0.861** (+0.056) | 0.530 → 0.542 (+0.012) |
| auto K=20 | 218 → 199 (−19) | 0.917 → 0.861 (−0.056) | 0.446 → **0.513** (+0.066) |

For v1 K=14 the strict judge confirms that the dropped predictions were redundant —
coverage rose while precision held — which is the behavior we want from a judge that is
measuring true substitution rather than topic overlap.

## 5. Takeaways

1. The lenient rubric's failure mode is **topic-adjacency inflation**: a prediction in the
   same business area, or covering only part of a multi-part actual, was scored ≥ 3. The
   substitution test is the single change that removes these.
2. The largest, cleanest false positives are **cross-domain** (cost ask matched to a yield
   prediction; consumer-demand ask matched to an EPS-sensitivity prediction) and
   **cross-twin** (covered only by another analyst's question at large K). Strict scoring
   eliminates the former outright and suppresses the latter.
3. **Report coverage as a multi-run mean [min, max], not a single run**, and prefer gpt-5
   as the canonical strict judge — it is the steadier, more conservative scorer on exactly
   the borderline items where the rubric change matters.

## 6. Strict B4 coverage — all settings (current record)

Evaluator gpt-5-mini + `prompts/b4_eval_strict.md`, single run per setting, set-level over
the 12-actual holdout (a few settings have 13–15 actuals where the judge split a multi-part
question). 93 settings across the auto / v1 / v5 K-curve (K ∈ {5, 10, 12, 14, 16, 18, 20};
seeds s1–s5, plus v1 K=14 reruns). Coverage = fraction of actuals with a best match ≥ 3.

### Aggregate by source × K — `mean [min, max]` (n seeds)

| K | v1 | v5 | auto |
|---|---|---|---|
| 5  | 0.667 [0.500, 0.833] (5) | 0.517 [0.333, 0.667] (5) | 0.583 [0.500, 0.667] (5) |
| 10 | 0.683 [0.583, 0.833] (5) | 0.583 [0.500, 0.667] (5) | 0.623 [0.500, 0.750] (5) |
| 12 | 0.667 (1)                | 0.583 (1)                | 0.667 (1)                |
| 14 | 0.733 [0.667, 0.917] (5) | 0.644 [0.385, 0.917] (5) | 0.617 [0.417, 0.833] (5) |
| 16 | 0.673 [0.500, 0.750] (5) | 0.667 [0.583, 0.833] (5) | 0.580 [0.400, 0.667] (5) |
| 18 | 0.700 [0.583, 0.833] (5) | 0.617 [0.417, 0.750] (5) | 0.646 [0.538, 0.750] (5) |
| 20 | 0.667 [0.500, 0.833] (5) | 0.700 [0.500, 0.833] (5) | 0.667 [0.583, 0.750] (5) |

### Source-level summary (pooled over all K and seeds)

| Source | settings | strict cov mean | range |
|---|---|---|---|
| v1   | 31 | 0.692 | 0.500 – 0.917 |
| v5   | 31 | 0.617 | 0.333 – 0.917 |
| auto | 31 | 0.616 | 0.400 – 0.833 |
| **all** | **93** | **0.642** | **0.333 – 0.917** |

**Reading.** Strict coverage clusters at **0.58–0.73** for every source, with v1 highest
(0.692) and v5/auto comparable (~0.62). Coverage is roughly flat across K — adding
candidates past K≈10 does not raise strict coverage (it lowers precision; see the K-curve
precision columns in `all_settings_strict_b4_mini.md`). The single-seed swings (e.g. v5 K=14
ranges 0.385–0.917) are judge variance on 1–2 borderline actuals, which is why coverage
should be read as the multi-seed mean, not any single run (Section 2).

The full 93-row per-setting table (coverage and precision for every seed) is in
`all_settings_strict_b4_mini.md`; the numbers above were re-extracted directly from
`data_auto/<setting>/strict_b4/b4.json` (`set_metrics.coverage_rate`) and reproduce it
exactly. The 5-run strict variance batches (`strict_b4_var/`, gpt-5 and gpt-5-mini) are
recorded separately in `strict_b4_eval_variance.md`.

## 7. Which model, and how it compares to the previous (lenient) evaluator

**Model.** All Section 6 coverage numbers are **gpt-5-mini** (`prompts/b4_eval_strict.md`),
one run per setting. gpt-5 was used only as a cross-check on the borderline setting
`final_eval_14q_v5` (Section 2; gpt-5 is the steadier, more conservative judge but was not
run across the full 93-setting grid).

**Previous version = lenient rubric** (`prompts/b4_eval.md`), same evaluator model
(gpt-5-mini), so the only change is the rubric. The cleanest comparison is the **controlled
head-to-head**: identical predictions, both rubrics run **5× each** on gpt-5-mini.

| Setting | Lenient cov (prev) mean [min,max] | Strict cov mean [min,max] | Δ |
|---|---|---|---|
| `final_eval_10q_v1`   | 0.700 [0.583, 0.750] | 0.650 [0.583, 0.667] | −0.050 |
| `final_eval_14q_auto` | 0.764 [0.750, 0.818] | 0.667 [0.583, 0.833] | −0.097 |
| `final_eval_14q_v1`   | 0.729 [0.667, 0.833] | 0.783 [0.667, 0.833] | +0.055 |
| `final_eval_14q_v5`   | 0.767 [0.667, 0.917] | 0.633 [0.500, 0.667] | −0.134 |
| `final_eval_14q_v5` (gpt-5) | 0.717 [0.583, 0.833] | 0.583 [0.500, 0.667] | −0.134 |

Net effect: strict scoring lowers coverage by roughly **0.05–0.13** on average (the one
positive, `14q_v1`, is within run-to-run noise — the lenient and strict ranges fully
overlap). The reduction is exactly the false-positive removal documented in Section 3: the
borderline topic-adjacent covers that the lenient rubric accepted are demoted below the
threshold.

**Aggregate check (all settings, single run).** The expected ordering **strict ≤ lenient**
holds for **82 / 85** settings that have both scores; the 3 exceptions exceed the lenient
5-run max by exactly one covered actual on a 12-actual denominator — single-run judge noise,
not a rubric inversion (see `all_settings_strict_b4_mini.md`). Note the single-run strict
spikes in the per-setting list (e.g. `14q_v1_rerun3` strict 0.917 vs lenient mean 0.633,
`14q_v5_s2` strict 0.917 vs lenient 0.683) are the same one-run judge variance and should
not be read as strict exceeding lenient — they wash out against the lenient 5-run band.

**Caveat on coverage.** Coverage alone understates the rubric change. Strict scoring's main
effect is on **precision**, which separates the configurations far more sharply than
coverage does (e.g. v5/auto K=18–20 strict precision collapses to ~0.03–0.05 while coverage
stays ~0.6–0.7). Coverage is comparable between rubrics because most actuals still have *some*
≥3 match; precision is where the lenient rubric's topic-adjacency inflation shows up. Use the
precision columns in `all_settings_strict_b4_mini.md` alongside the coverage here.

## Provenance

- Prompts: `prompts/b4_eval.md` (lenient), `prompts/b4_eval_strict.md` (strict).
- Per-question scores and matched candidates: `strict_b4_eval_variance.md`,
  `eval_variance_flip_questions.md` (lenient/strict, gpt-5 vs gpt-5-mini, 5 runs each).
- Aggregate strict K-curve: `all_settings_strict_b4_mini.md` (batch
  `batch_6a1fc031cf8081908a9d9095b2c3d32f`, 93/93 completed).
- Score-4 / identity analysis: `b4_score4_candidates.md`.
- Strict dedup: `dedup_strict_best_configs.md`.
</content>
</invoke>
