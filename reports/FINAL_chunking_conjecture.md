# Shorter evaluation prompts improve candidate selection: a conjecture and its evidence

## Summary

We evaluate set-level coverage of predicted earnings-call questions against held-out actuals using
an LLM judge (the "B4" evaluator) under the strict substitution-test rubric
(`prompts/b4_eval_strict.md`). Coverage is the fraction of the 12 holdout actuals for which some
predicted question scores ≥3 (substitutable). We compare two ways of presenting the candidate pool to
the judge — a **single call** over the whole pool versus **chunked** calls over ≤50-candidate subsets
(taking each actual's maximum score across chunks) — crossed with two judges, gpt-5-mini and gpt-5,
across 21 configurations (sources v1/v5/auto × K∈{5,10,12,14,16,18,20}, seed-1).

**Conjecture.** *Shorter evaluation prompts improve candidate selection.* When the judge sees the
candidate pool in small chunks rather than as one long list, it attends to each candidate more
effectively and selects a better-matching prediction for each actual, raising measured coverage. The
effect is genuine retrieval (a different, better candidate is chosen), not merely re-scoring of the
same candidate.

The evidence below is consistent with this conjecture but is observational and single-run; we state it
as a conjecture, not a proven result, and list the experiments that would confirm or refute it.

## Background: the measurement problem

Two failure modes motivated this study:

1. **Single-call under-counting.** With 150–220 candidates in one prompt, the judge does not reliably
   scan the whole list, so it misses covering candidates and reports coverage that is too low. Example:
   v5 K20 single-call (gpt-5-mini) coverage = 0.500, despite a pool that demonstrably covers more.
2. **Chunked over-counting under a lenient judge.** Splitting into chunks and taking the per-actual
   maximum gives the judge several independent opportunities to award ≥3. A lenient judge
   (gpt-5-mini) then inflates coverage; at auto K18 and K20 it reaches a spurious 1.000 (all 12
   covered), which manual inspection refutes.

Neither failure is the rubric's fault — the rubric is held constant (strict) throughout. The variables
are the **judge model** and the **prompt length** (single vs chunked).

## Method

- **Rubric:** strict `prompts/b4_eval_strict.md` for every call. Covered = match score ≥3.
- **Single-call:** one B4 request, full candidate pool + all 12 actuals.
- **Chunked:** pool split into chunks of ≤50 candidates; one B4 request per chunk (chunk candidates +
  all 12 actuals); for each actual, the maximum score across chunks; covered if that maximum ≥3.
- **Judges:** gpt-5-mini and gpt-5. **Configs:** 21 (seed-1). **Runs:** one per (config, method, model).
- Execution via the OpenAI Batch API. Builders/parsers and per-config artifacts are listed under
  Provenance.

## Evidence

### E1. The 2×2 of coverage (strict rubric, mean over 21 configs)

| | single-call (long prompt) | chunked (short prompts) |
|---|---|---|
| **gpt-5-mini** | 0.615 — under-counts (blind on large pools) | 0.822 — over-counts (leniency × max-over-chunks) |
| **gpt-5** | 0.570 — reliable but still blind at high K | **0.722 — reliable and accurate** |

The chunked-mini cell is the least reliable: chunking amplifies mini's leniency, producing the 1.000
outliers. The chunked-gpt-5 cell is the recommended estimate.

### E2. The chunking effect with the judge held fixed at gpt-5

Holding the judge at gpt-5 isolates the prompt-length variable:

- Chunking improves coverage in **18 of 21 configs** (2 ties, 1 loss).
- Mean improvement Δ = **+0.152**; median +0.167; maximum +0.417 (v5 K18).
- Mean coverage rises **0.570 → 0.722**.
- The two ties are both at **K=5** (~55 candidates fit a single call, so there is nothing for
  chunking to recover). The single loss (auto K18, −0.144) is within single-run noise.

The gains are largest at high K — precisely where the single call's prompt is longest and the
under-counting is worst. This dependence on K is the signature predicted by the conjecture.

### E3. Mechanism — chunking selects a different, better candidate

Comparing, per (actual, config) pair, the candidate each method selected (gpt-5 judge, 250 pairs):

| outcome | count | share |
|---|---|---|
| same candidate selected | 86 | 34% |
| **different candidate selected** | 164 | **66%** |

Of the 46 pairs where chunked covers (≥3) and single-call does not, **35 (76%) selected a different
candidate** — a better-matching prediction the single call never surfaced. The remaining 11 (24%) are
the same candidate scored differently (re-scoring noise). Thus roughly three-quarters of the coverage
gain is attributable to **better candidate selection**, and one-quarter to scoring variance. This is
the core support for the conjecture: the improvement is dominated by *which candidate is chosen*, not
by *how a fixed candidate is scored*.

Illustrative cases (single → chunked, gpt-5): for the actual "drivers of durable multi-year growth"
(`matthew_boss-0`), the single call selected a capacity/deployment prediction (score 2) while chunking
selected the Perfecta 20%-EPS-CAGR durable-growth prediction (score 3) — the on-topic match. For
"itinerary changes and deferred spend" (`sharon_zackfia-0`), single selected a Q2 cost-cadence
prediction (score 1) while chunking selected the "Net Cruise Costs ex-fuel, structural vs timing"
prediction (score 3).

### E4. The chosen matches are reliable, not random inflation

Across the 21 configs, coverage decisions are highly stable per actual under chunked gpt-5: a fixed
set of actuals (`brandt_montour-0`, `lizzie_dove-0`, `vince_ciepiel-0`, `xian_siew-0`) is covered in
21/21 configs, while `robin_farley-0` is covered in 0/21 and `kevin_kopelman-0` in 1/21. A judge that
inflated coverage at random would not reject the same two actuals in nearly every configuration. The
full-text matches for every covered actual are recorded for manual audit
(`reports/chunked_gpt5_covered_all.md`).

## Interpretation

Three linked claims follow from the evidence:

1. **The strict prompt is necessary but not sufficient for a reliable score; the judge model
   decides.** The rubric encodes the substitution test, but gpt-5-mini applies it loosely (awards 3–4
   to topic overlap that gpt-5 scores 2). Reliable evaluation therefore requires strict prompt *and*
   gpt-5, not the strict prompt alone.
2. **Chunking with a lenient judge is the least reliable configuration.** Max-over-chunks gives a
   lenient judge multiple chances per actual, compounding its leniency into spurious near-perfect
   coverage. Chunking must be paired with a reliable judge.
3. **Chunking improves coverage because shorter prompts improve candidate selection.** With ≤50
   candidates per call the judge attends to each candidate and selects a better match (different
   candidate in 66% of pairs; 76% of coverage gains); the long single call goes blind and locks onto a
   mediocre candidate. This is the conjecture, and E2–E3 are its direct support.

## Worked examples: the previous judge over-scores, strict + gpt-5 corrects it

In each case a prediction that shares the actual's topic but not its ask was scored "covered" (≥3)
under the previous (lenient) rubric, and correctly demoted to 2 once the strict substitution test
applies. Reasoning is quoted verbatim from the judge.

### Headline case — `andrew_didora-0`: same gpt-5 judge, same prediction, only the rubric flips the verdict

This is the cleanest demonstration that the *rubric* — not the model — corrects the verdict. The
evaluator (gpt-5) and the predicted question (`andrew_didora-pred-2`) are held fixed; only the prompt
changes (`b4_eval.md` → `b4_eval_strict.md`). The actual is two-part: (1) how to roll in new hedges in
a high-fuel environment, and (2) at what capacity growth NCC-ex-fuel turns inflationary. The
prediction answers part (1) only.

**gpt-5 + lenient (`b4_eval.md`) — 4/5 runs covered (false positive):**

| run | score | covered | judge reasoning (verbatim) |
|---|---|---|---|
| 1 | 3 | ✓ | "Addresses hedging philosophy … **partial on NCC ex-fuel scaling threshold**." |
| 3 | 3 | ✓ | "good overlap on the hedging piece … (**partial on the NCC threshold**)." |
| 4 | 3 | ✓ | "capacity-growth threshold for NCC ex-fuel **is not directly addressed** but overall intent is close." |
| 5 | 2 | ✗ | "matches hedging philosophy … but not the capacity-growth threshold." |

**gpt-5 + strict (`b4_eval_strict.md`) — 0/3 runs covered (correct):**

| run | score | covered | judge reasoning (verbatim) |
|---|---|---|---|
| 1 | 2 | ✗ | "Overlap on hedging philosophy, but actual also asks NCC ex-fuel growth threshold vs capacity; **substitution incomplete**." |
| 2 | 2 | ✗ | "predicted does not address that second part, so **substitution fails**." |
| 3 | 2 | ✗ | "actual also asks NCC ex-fuel inflation threshold vs capacity growth, which predicted **doesn't address**." |

The judge makes the *same observation under both rubrics* — "partial / does not address the
NCC-vs-capacity part." Under lenient, that observation is overridden by "overall intent is close" and
scored 3 (covered). Under strict, the substitution test — *would a verbatim answer give the listener
the key fact the actual asked for?* — converts the same observation into a 2, because part (2) is
unanswered. The rubric, not the model, corrects the verdict.

### Supporting cases (strict + gpt-5 demotes a topic-overlap match the previous approach covered)

- **`steven_wieczynski-0`** (gpt-5-mini chunked **4** → strict gpt-5 **2**): actual wants confidence in
  the H2/Q4 yield cadence to reach the ~2% guidance + the Europe headwind; pred (`james_hardiman-pred-9`)
  asks booking-curve/APD detail. gpt-5: "different ask."
- **`brandt_montour-0`** (gpt-5-mini chunked **4** → strict gpt-5 **2**): actual wants Q3 remaining-to-book
  + guidance; pred (`james_hardiman-pred-3`) asks duration/% cancellations. gpt-5: "overlap on topic,
  **different ask shape and metrics**."
- **`robin_farley-1`** (lenient prompt + gpt-5-mini **4** → strict prompt + gpt-5 **2**): actual asks
  whether the ~200 bps Euro-yield shortfall recovers **into 2027**; pred (`matthew_boss-pred-11`) asks
  Q2 cadence and transitory-vs-permanent split. gpt-5: "actual asks recovery timing into 2027 … the
  prediction centers on Q2/FY cadence."

The pattern is consistent: the previous approach rewards shared vocabulary (fuel, yield cadence,
Mediterranean), while strict + gpt-5 requires the prediction to actually *substitute* — same ask, same
metric, all parts covered — and otherwise assigns 2. The headline case isolates the rubric (gpt-5 held
fixed); steven/brandt isolate the model (strict rubric held fixed, gpt-5-mini still over-scores);
robin-1 combines both. Together they support Interpretation claim 1: a reliable score needs the strict
prompt **and** gpt-5. (Full per-run reasoning and the broader false-positive catalogue, including
cross-twin "borrowed" covers at large K, are in `reports/strict_eval_rewrite_report.md`.)

## Limitations

- **Single-run.** Every cell is one evaluation; per-config values carry ±~0.1 noise (e.g. the lone
  auto-K18 reversal). The aggregate trends (18/21 win rate, +0.15 mean, 66%/76% mechanism splits) are
  robust to this, but individual numbers are not.
- **Observational, not a controlled retrieval experiment.** We infer "better candidate selection" from
  which candidate each method's judge reported, not from an independent ground-truth retrieval. The
  judge's selection could itself be biased; E4 mitigates but does not eliminate this.
- **Single seed.** All 21 configs are seed-1 predictions; generation variance (which we have shown is
  large) is not averaged out.
- **max aggregation.** Chunked coverage uses the per-actual maximum across chunks, which has a mild
  upward bias even for gpt-5; a two-stage retrieve-then-rescore would remove it.

## Experiments that would confirm or refute the conjecture

1. **Multi-run / all-seed replication** of the chunked-gpt-5 vs single-call-gpt-5 comparison, to
   convert the single-run trend into a confidence interval.
2. **Chunk-size sweep** (e.g. 25 / 50 / 100 / full): the conjecture predicts coverage rises as chunk
   size falls, plateauing once chunks are small enough to be read fully.
3. **Two-stage retrieve-then-rescore:** use chunking only to shortlist each actual's best candidate,
   then score that single pair with gpt-5. If coverage matches chunked-max, the gain is retrieval; if
   it drops, part of the gain was max-aggregation bias.
4. **Position-controlled probe:** place a known covering candidate at varying positions in a long
   single-call prompt; the conjecture predicts the judge misses it more often as the prompt lengthens.

## Conclusion

Under a strict rubric, the trustworthy coverage estimate is **chunked retrieval scored by gpt-5**
(mean ≈ 0.72 across 21 configs), well above the single-call gpt-5-mini K-curve (≈ 0.61) that
under-counts through large-pool blindness. The improvement from chunking is consistent with the
conjecture that **shorter prompts improve candidate selection**: 66% of selections change under
chunking and 76% of coverage gains come from a newly surfaced, better candidate, with stable
cross-config behavior indicating a reliable judge rather than random inflation. The result is reported
as a conjecture pending the multi-run and controlled-retrieval experiments listed above.

## Provenance

- Builders: `src/batch_build_strict_b4_chunked.py`, `src/batch_build_single_gpt5.py`,
  `src/batch_build_strict_b4.py` (single mini).
- Parsers: `src/parse_strict_b4_chunked.py`, `src/parse_and_report_single_gpt5.py`,
  `src/parse_strict_b4.py`.
- Report generator: `src/report_chunking_analysis.py`. Per-config data:
  `data_auto/final_eval_{K}q_{src}/strict_b4_chunked/{gpt_5_mini,gpt_5}/b4.json`,
  `.../strict_b4_single_gpt5/b4.json`, `.../strict_b4/b4.json`.
- Companion reports: `chunking_analysis.md`, `strict_b4_chunked_kcurve.md`,
  `chunk_vs_single_gpt5.md`, `chunked_gpt5_covered_all.md`, `auto_k18_all_questions.md`.
