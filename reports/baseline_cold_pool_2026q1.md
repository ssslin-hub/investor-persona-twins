# No-Persona Cold-Pool Baseline — 2026-Q1 holdout (B4 evaluator)

**Setup.** A single LLM call per generator produces an unbranded pool of **12 questions** from only the Q1 2026 prepared remarks (no analyst names, no persona, no history). The same 0–4 set-level evaluator rubric used by V2 `run_llm_set_pipeline.mjs` then judges the pool against the 12 actuals in both directions:

- **Coverage**: each actual → best predicted match; score ≥ 3 counts as covered.
- **Precision**: each predicted question → best actual match; score ≥ 3 counts as useful.
- **Average best score** (continuous) on each side.

Generator: gpt-5-mini and gpt-5 (temperature 0). Evaluator: fixed to **gpt-5** so the rubric is held constant when comparing generators.

BLEU-2 / BLEU-4 are smoothed sentence-BLEU (method1) with all pool questions as references — a literal-similarity sanity check, distinct from the semantic B4 metric.

**Reference points.** V2 `run_llm_set_pipeline.mjs` B4 numbers on the same holdout: coverage 8/12 = 66.7 %, precision 8/12 = 66.7 %, avg actual best 2.92, avg predicted best 2.50.

## Headline — V1 hit + B2 per-analyst + B4 set-level, no persona

| Generator | V1 hit (all 11/12) | **B2** binary match (11 ana) | B2 avg score | B4 coverage | B4 precision | avg actual best | avg pred best | BLEU-2 | BLEU-4 |
|---|---|---|---:|---|---|---:|---:|---:|---:|
| gpt-5-mini | 11/12 = **0.917** | 5/11 = **0.455** | 2.55 | 7/12 = **0.583** | 6/12 = **0.500** | 2.67 | 1.83 | 0.1529 | 0.0421 |
| gpt-5 | 11/12 = **0.917** | 6/11 = **0.545** | 2.73 | 5/12 = **0.417** | 5/12 = **0.417** | 2.42 | 2.08 | 0.1504 | 0.0429 |

**Reference points** on the same 2026-Q1 holdout:
- V0 baseline (per-analyst, no peer): V1 hit 0.500
- V1 `auto_discovery` TEST (per-analyst persona, peer-augmented): V1 hit **0.600** (9 returning / 10 actuals)
- V2 `run_llm_persona_pipeline.mjs` **B2** (per-analyst Extractor → Simulator → Evaluator, 11 analysts): binary_match_rate **3/11 = 0.273**, avg score **1.45 / 4**
- V2 `run_llm_set_pipeline.mjs` **B4** (19-persona panel + selector slate of 12): coverage 0.667, precision 0.667, avg actual best 2.92, avg pred. best 2.50

## Scoring rubrics

Two complementary semantic judges are run on every (generator, pool) pair:

### V1 `judge_match.md` — three-level per-analyst (the **hit rate** column)

For each actual question asked by a given analyst, the judge looks at the entire pool and assigns one label, then sums per analyst:

- **EXACT** — same topic, same direction of inquiry, comparable specificity (e.g. both ask about yield decomposition at the bps level).
- **PARTIAL** — same topic and similar direction, but one side is broader/narrower in specificity (e.g. predicted asks generally about yield drivers; actual asks specifically about new-hardware contribution).
- **MISS** — no question in the pool addresses the same substantive concern.

`hit = (n_exact + n_partial) / n_actual` per analyst, then summed. This is the same judge V1 `auto_discovery` reports as `hit_rate_exact_or_partial`. Judge model: `gpt-5-mini`, temperature 0.

### V2 B2 per-analyst evaluator (the **B2 binary match** column)

For each analyst, the evaluator receives the cold pool (treated as the analyst's predicted set — the user's "assume each analyst answered 12 questions" stipulation) and that analyst's actual question(s). It returns one overall match score 0–4 plus a 4-axis alignment breakdown (topic / trigger / question form / granularity, each ∈ {none, weak, partial, strong}). `binary_match = score >= 3`.

Aggregates: `binary_match_rate = n_binary_hit / 11`, `average_match_score = mean(score) / 4`.

Same 0–4 rubric as B4 (see below). B2 differs from B4 only in scope: B2 fixes analyst identity, B4 ignores identity.

### V2 B4 set-level rubric (the **0–4 score** used for coverage / precision)

Same rubric is applied in **both directions** (each actual → best pool match; each pool item → best actual match):

| score | meaning |
|:-:|---|
| **0** | No meaningful relation — the predicted question and the actual question are about different things entirely. |
| **1** | Same broad business area only (e.g. both touch "costs" but one is fuel hedging and the other is labour inflation). |
| **2** | Partial theme match but wrong trigger or different ask — overlapping topic, but the specific uncertainty being probed differs. |
| **3** | Substantially similar question target — both questions would elicit substantially the same management answer. |
| **4** | Very close substitute — the predicted question is essentially the actual question reworded; same trigger, same ask, same expected answer shape. |

Aggregates:
- **coverage_rate** = fraction of actuals whose best-matching pool item scores ≥ 3.
- **precision_rate** = fraction of pool items whose best-matching actual scores ≥ 3.
- **avg actual best** = mean over actuals of `max_pool match_score_0_to_4`.
- **avg pred. best**  = mean over pool of `max_actual match_score_0_to_4`.

Evaluator model: `gpt-5`, temperature 0. Held constant so that the difference between gpt-5-mini and gpt-5 in the headline isolates **generator** quality, not judge quality.

### BLEU-2 / BLEU-4 (literal similarity, auxiliary)

Smoothed sentence BLEU (Papineni 2002, modified n-gram precision; smoothing = NLTK `SmoothingFunction.method1`). For each actual question:

- hypothesis = the actual question text
- references = all 12 pool questions
- BLEU-2 truncates at n = 2 (1-gram + 2-gram geometric mean × brevity penalty)
- BLEU-4 truncates at n = 4 (up through 4-gram)

Then averaged across actuals. These are **string-overlap** metrics, not semantic; they answer "how close is the predicted *wording* to the actual *wording*", which is intentionally separate from the 0–4 semantic axis. They will always be low when the pool generates the analyst's *concern* but not the analyst's *phrasing* — exactly the regime we are in.

## gpt-5-mini — per-analyst V1 judge & B2 evaluator

| Analyst | V1 (exact/partial/miss) | V1 hit | **B2 score 0-4** | B2 binary | topic | trigger | form | gran |
|---|---|---:|:-:|:-:|:-:|:-:|:-:|:-:|
| andrew didora | 0/1/0 | 1.00 | **3** | Y | strong | partial | partial | partial |
| brandt montour | 1/0/0 | 1.00 | **3** | Y | strong | partial | strong | partial |
| james hardiman | 0/1/0 | 1.00 | **2** | N | partial | partial | partial | weak |
| kevin kopelman | 0/1/0 | 1.00 | **2** | N | partial | weak | partial | weak |
| lizzie dove | 0/1/0 | 1.00 | **2** | N | partial | weak | partial | weak |
| matthew boss | 0/0/1 | 0.00 | **3** | Y | strong | partial | strong | partial |
| robin farley | 0/2/0 | 1.00 | **2** | N | strong | strong | partial | weak |
| sharon zackfia | 0/1/0 | 1.00 | **2** | N | strong | weak | partial | partial |
| steven wieczynski | 0/1/0 | 1.00 | **3** | Y | strong | partial | strong | strong |
| vince ciepiel | 0/1/0 | 1.00 | **2** | N | strong | partial | strong | partial |
| xian siew | 1/0/0 | 1.00 | **4** | Y | strong | partial | strong | strong |

## gpt-5 — per-analyst V1 judge & B2 evaluator

| Analyst | V1 (exact/partial/miss) | V1 hit | **B2 score 0-4** | B2 binary | topic | trigger | form | gran |
|---|---|---:|:-:|:-:|:-:|:-:|:-:|:-:|
| andrew didora | 0/1/0 | 1.00 | **3** | Y | strong | strong | strong | partial |
| brandt montour | 0/1/0 | 1.00 | **2** | N | strong | partial | partial | weak |
| james hardiman | 0/1/0 | 1.00 | **3** | Y | strong | partial | partial | partial |
| kevin kopelman | 0/1/0 | 1.00 | **2** | N | partial | partial | partial | partial |
| lizzie dove | 0/1/0 | 1.00 | **2** | N | partial | weak | partial | weak |
| matthew boss | 0/1/0 | 1.00 | **2** | N | partial | strong | weak | weak |
| robin farley | 0/1/1 | 0.50 | **3** | Y | strong | strong | partial | partial |
| sharon zackfia | 0/1/0 | 1.00 | **3** | Y | strong | partial | partial | partial |
| steven wieczynski | 1/0/0 | 1.00 | **4** | Y | strong | strong | strong | strong |
| vince ciepiel | 0/1/0 | 1.00 | **2** | N | partial | weak | strong | partial |
| xian siew | 1/0/0 | 1.00 | **4** | Y | strong | strong | strong | partial |

## gpt-5-mini — qualitative

_Evaluator summary:_ Coverage was solid on yields/guidance, Mediterranean booking dynamics, fuel hedging, cost efficiencies, and loyalty/repeat guest behavior. We missed consumer airfare sensitivity, Mexico project status and ramp specifics, and the timing of European yield recapture into 2027. Several predictions (JV contributions, capital allocation, redeployments, digital/AI) did not appear in the actual set. Overall coverage was 7/12 with a 0.50 precision rate.

**Missed actual themes:** Overall booking trajectory vs pre-disruption and visibility beyond 3Q into 2027; North American consumer sensitivity to higher airfares to reach ports; Perfect Day Mexico ramp cadence and Western Caribbean/Galveston penetration specifics; Status of Mexico project construction pause/resumption; Sizing if/when European yield shortfall in 2024 is recaptured in 2027

**Overpredicted themes:** West Coast Mexico itinerary disruption and redeployment quantification; Joint venture (TUI Cruises) contribution drivers and cadence; Specific ship redeployment decision rationale and yield impact; Capital allocation priorities and target leverage; Digital/AI personalization ROI and pre-cruise onboard revenue targets

## gpt-5 — qualitative

_Evaluator summary:_ Predictions covered 5 of 12 actual questions with strong matches on Q4 yield exit rate, fuel hedging, ex-fuel cost efficiencies, and loyalty/credit card impacts. Gaps remained around Med booking damage and guidance, North American airfare impacts, Perfect Day Mexico ramp and construction status, and Europe yield recapture into 2027. Several predictions over-indexed to capital allocation, JV, and capex/ROIC topics that did not appear in the holdout set. Overall coverage and precision were moderate, with average best-match scores around 2–2.5.

**Missed actual themes:** Q3 Mediterranean: left-to-book, damage quantification, and guidance assumptions under conflict; North American airfare impact on consumer behavior for NA itineraries; Perfect Day Mexico ramp cadence and Western Caribbean/Galveston penetration; Company-level multi-year durable growth drivers vs pre-pandemic; Perfect Day Mexico construction status/resumption; Timing of European yield recapture into 2027; Yield outlook decomposition from new hardware/destinations and whether Europe yields grow

**Overpredicted themes:** Yield bridge by ticket vs onboard and price vs occupancy with Med/West Coast offsets; West Coast Mexico itinerary actions and deployment flexibility; Caribbean premium protection via Perfect Day and Royal Beach Clubs versus peers; Pre-cruise monetization category mix and margins; Capex cadence/newbuilds unit economics and ROIC/hurdle rates; Capital returns strategy (dividends versus buybacks) and leverage targets; JV/TUI contribution drivers and outlook

## Anti-leakage

| Generator | # leaked 4-grams | examples |
|---|---:|---|
| gpt-5-mini | 1 | we think about the |
| gpt-5 | 2 | we think about the; how much do you |

## Artifacts

- `data_baseline/gpt-5-mini/pool.json` — 12 generated questions + raw LLM response
- `data_baseline/gpt-5-mini/set_evaluation.json` — bidirectional B4 verdict (full rubric)
- `data_baseline/gpt-5-mini/summary.json`, `bleu.json`
- `data_baseline/gpt-5/pool.json` — 12 generated questions + raw LLM response
- `data_baseline/gpt-5/set_evaluation.json` — bidirectional B4 verdict (full rubric)
- `data_baseline/gpt-5/summary.json`, `bleu.json`

## K=110 + sample-10 experiment (generator: gpt-5-mini, seed=42)

**Setup.** gpt-5-mini was asked once (temperature=1) to generate 110 distinct Q&A questions from the prepared remarks. After dedup K_eff = **110**. A fixed RNG (seed=42) then drew **10 random candidates per analyst** as that analyst's predicted set (B2 / V1 inputs) and a **single 10-question slate** for B4 sampled. B4 oracle uses the full 110-pool.

| Metric | Value | Upstream reference |
|---|---|---|
| K (post-dedup) | 110 | — |
| k_sample (per analyst & B4 slate) | 10 | — |
| **V1 hit (returning 9 / 10)** | 8/10 = **0.800** | V1 auto_discovery 0.600 |
| V1 hit (all 11 / 12) | 9/12 = **0.750** | — |
| **B2 binary match** | 3/11 = **0.273** | V2 B2 0.273 |
| B2 avg score | **2.27** / 4 | V2 B2 1.45 |
| **B4 sampled coverage** | 2/12 = **0.167** | V2 B4 0.667 |
| B4 sampled precision | 3/10 = **0.300** | V2 B4 0.667 |
| B4 sampled avg actual best | 1.83 | V2 B4 2.92 |
| B4 sampled avg pred best | 2.30 | V2 B4 2.50 |
| **B4 oracle coverage** (110 preds) | 8/12 = **0.667** | (upper bound) |
| B4 oracle precision | 20/110 = 0.182 | — |
| B4 oracle avg actual best | 2.67 | (upper bound) |
| BLEU-2 / BLEU-4 (full pool refs) | 0.2560 / 0.0702 | — |
| BLEU-2 / BLEU-4 (slate-10 refs) | 0.0777 / 0.0302 | — |
| 4-gram leak count | 5 | — |

### Per-analyst V1 + B2 on the seeded sample of 10

| Analyst | V1 (E/P/M) | V1 hit | B2 score 0-4 | B2 binary | topic | trigger | form | gran |
|---|---|---:|:-:|:-:|:-:|:-:|:-:|:-:|
| andrew didora | 0/0/1 | 0.00 | **2** | N | partial | weak | weak | weak |
| brandt montour | 0/1/0 | 1.00 | **2** | N | strong | partial | weak | weak |
| james hardiman | 0/0/1 | 0.00 | **2** | N | partial | partial | weak | weak |
| kevin kopelman | 0/0/1 | 0.00 | **2** | N | partial | partial | partial | weak |
| lizzie dove | 0/1/0 | 1.00 | **2** | N | strong | partial | partial | partial |
| matthew boss | 1/0/0 | 1.00 | **3** | Y | strong | partial | strong | partial |
| robin farley | 1/1/0 | 1.00 | **3** | Y | strong | strong | partial | partial |
| sharon zackfia | 0/1/0 | 1.00 | **2** | N | partial | weak | partial | weak |
| steven wieczynski | 0/1/0 | 1.00 | **2** | N | partial | weak | weak | weak |
| vince ciepiel | 0/1/0 | 1.00 | **2** | N | strong | partial | partial | partial |
| xian siew | 0/1/0 | 1.00 | **3** | Y | strong | strong | partial | partial |

### Artifacts

- `data_baseline/gpt-5-mini_k110/pool.json` — raw 110-pool + dedup log + K_eff
- `data_baseline/gpt-5-mini_k110/samples.json` — per-analyst sampled candidate_ids + B4 slate ids + seed
- `data_baseline/gpt-5-mini_k110/judgments/*.json` — V1 verdicts (sampled-10)
- `data_baseline/gpt-5-mini_k110/b2/*.json` — B2 evaluator verdicts (sampled-10)
- `data_baseline/gpt-5-mini_k110/b4_sampled.json` — B4 verdict on the 10-slate
- `data_baseline/gpt-5-mini_k110/b4_oracle.json` — B4 verdict on full 110-pool
- `data_baseline/gpt-5-mini_k110/bleu.json`, `summary.json`

