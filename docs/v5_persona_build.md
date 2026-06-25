# v5 Persona Construction

This doc explains how the 16 v5 analyst personas at `data/personas_v5/*.json` were built. Source code: `src/run_pipeline.py` and `prompts/extract_bde_v5.md`.

## TL;DR

- **Input**: chronological Q&A turns of each analyst on RCL earnings calls (RCL only — peer transcripts are NOT used here).
- **Extractor model**: `gpt-5-mini`.
- **Prompt**: `prompts/extract_bde_v5.md` — produces a JSON object with 5 top-level fields, including two NEW vs V1: `queue_behavior` and `cross_analyst_reactivity`.
- **What's new in v5 vs V1**: per-turn metadata in the question history (queue position, names of analysts who spoke before, Q&A-so-far excerpt) — this gives the extractor enough context to characterize the analyst's behavior under different queue positions and reaction to peer questions.
- **Output**: 16 JSON files at `data/personas_v5/<analyst_safe>.json`.

## Inputs

### Transcript corpus

- **TRAIN** (used for extraction): `data/analysts.json` — RCL earnings calls 2021-Q1 through 2025-Q4 (~18 calls). Per analyst, a list of `records`, each containing the turn's call, position metadata, context excerpt, the analyst's question, and the management response.
- **HOLDOUT** (used only for downstream verification, never for extraction): `data/analysts_test.json` — RCL 2026-Q1.
- **Peer data is NOT used in v5 extraction**. The "peer-augmented" framing applies to Phase 1's `Auto` pipeline (which trained from `data_auto/train_combined.json` containing CCL/NCLH/MAR/HLT/H peer turns). v5 personas are built from RCL-only Q&A history but augmented with per-turn queue and reactivity metadata.

### Eligibility filter

Only analysts with **≥ `MIN_QUESTIONS` (=5) prior turns** in TRAIN are extracted, OR who appear in the 2026-Q1 HOLDOUT. This yields 16 personas:

```
andrew_didora, benjamin_chaiken, brandt_montour, conor_cunningham,
daniel_politzer, fred_wightman, ivan_feinseth, james_hardiman,
lizzie_dove, matthew_boss, patrick_scholes, paul_golding,
robin_farley, sharon_zackfia, steven_wieczynski, vince_ciepiel
```

11 of these are TEST returning analysts (overlap with HOLDOUT). 2 cold-start analysts (xian siew, kevin kopelman) appear in HOLDOUT but have insufficient TRAIN history, so they fall back to `data_auto/final_personas/_fallback.json` at simulation time.

## Pipeline

The driver is `src/run_pipeline.py`, called with v5-specific flags:

```
python3 src/run_pipeline.py \
    --extraction-prompt extract_bde_v5.md \
    --persona-out-subdir personas_v5 \
    --log-out-subdir prompt_logs_v5 \
    --skip-simulate-and-judge
```

### Step 1 — Build question history block per analyst

For each eligible analyst, `build_question_history_block()` iterates through their `records` (capped at `MAX_HISTORY_TURNS=60` most recent). For each turn, the v5 history block includes:

1. **Queue position metadata**: `[Queue position] This analyst was #N to speak on this call.`
2. **Peer presence on the call**: `[Analysts who spoke before them on this call] <comma-joined names or "(none — they were first)">` — parsed via `parse_qa_so_far()` regex on the prior context.
3. **Setup excerpt**: management presentation truncated to `MGMT_EXCERPT_CHARS=1200`.
4. **Q&A so far**: `[Q&A SO FAR — what prior analysts asked, truncated]` — the verbatim prior Q&A from the operator queue, capped at last 2000 chars (this is NEW in v5).
5. **Operator intro** to this analyst, if present.
6. **The analyst's question** (verbatim).
7. **Management response** excerpt.

Items 1, 2, and 4 are the v5-specific additions vs V1. They give the extractor enough context to populate the two new persona fields.

### Step 2 — Construct the v5 extraction prompt

`load_text('prompts/extract_bde_v5.md')` is the template. The history block from Step 1 is substituted into `{question_history}`, with `{analyst_name}`, `{affiliation}`, `{n_questions}`, `{calls_covered}` filled in.

### Step 3 — Call LLM

`call_llm(prompt, expect_json=True, ...)` with `OPENAI_MODEL=gpt-5-mini` (default in `src/llm_client.py:15`). The model is asked to return strict JSON.

### Step 4 — Persist

`parse_json_strict()` validates the output. The resulting persona JSON is written to `data/personas_v5/<name_with_underscores>.json`. The full LLM input prompt is also saved to `data/prompt_logs_v5/extract_<name>.txt` for reproducibility.

## v5 persona schema

Each `data/personas_v5/<analyst>.json` has 5 top-level fields:

| Field | Purpose | V1? |
|---|---|---|
| `coverage_profile` | firm, seniority signal, sector lens, rhetorical signature | ✓ |
| `reasoning_style` | primary_mode (quant/qual/mixed), follow_up_pattern, evidence_demanded, anchoring_habits | ✓ |
| `recurring_concerns` | `core_topics` (ranked by n_turns), `blind_spots`, `stance_drift` | ✓ |
| `queue_behavior` | typical_position, default_first_pick, adaptation_when_favorites_taken, white_space_topics | **NEW in v5** |
| `cross_analyst_reactivity` | explicit_peer_references, management_line_anchoring, operator_or_followup_signal | **NEW in v5** |

### `queue_behavior` rationale

The extraction prompt enumerates 6 tagged behaviors the analyst can exhibit when their preferred topics have been taken:

- `reframe_deeper` — re-ask the same topic at a deeper modeling angle
- `white_space` — pivot to a topic few peers cover
- `cross_narrative_reconcile` — reconcile two earlier Q&A threads
- `peer_or_industry_meta` — ask about peer/industry behavior
- `reactive_followup` — piggyback on a specific phrase
- `stay_on_topic_anyway` — re-ask the popular topic regardless

For each tag chosen, the extractor cites ≥1 call and quotes ≤12 verbatim words.

### `cross_analyst_reactivity` rationale

Three sub-fields:
- `explicit_peer_references` — count of turns and example phrases (e.g., "following up on Steven's question")
- `management_line_anchoring` — count of turns anchoring on a specific number management just delivered
- `operator_or_followup_signal` — whether they take their second turn and what for

## Topic-count audit (returning TEST analysts)

The 11 analysts evaluated on HOLDOUT, with their v5 `recurring_concerns.core_topics` counts:

| Analyst | v5 topic count | Persona source | Notes |
|---|---|---|---|
| matthew boss | 7 | v5 | healthy |
| steven wieczynski | 8 | v5 | healthy |
| brandt montour | 7 | v5 | healthy |
| james hardiman | 6 | v5 | healthy |
| robin farley | 8 | v5 | healthy |
| vince ciepiel | 7 | v5 | healthy |
| andrew didora | **0** | v5 | thin (1 RCL Q); only queue/reactivity signal |
| lizzie dove | 2 | v5 | thin |
| sharon zackfia | 2 | v5 | thin |
| xian siew (cold-start) | — | auto-fallback | uses `_fallback.json` |
| kevin kopelman (cold-start) | — | auto-fallback | uses `_fallback.json` |

This audit explains the K=14 per-analyst K-curve finding (Phase 26):
- v5 wins decisively on `sharon` (69% vs V1=0%) and `andrew` (69% vs V1=57%) — exactly the thin-history analysts where the V1 schema has no signal but v5's `queue_behavior` and `cross_analyst_reactivity` can still characterize behavior.
- v5 wins on `james` (89%) and `lizzie` (83%) — moderate-history analysts that benefit from the richer history block.
- V1 wins on `brandt` (100% perfect) and `xian` (89%, cold-start fluke) where its hand-curated core_topics happen to be perfectly aligned.

## Critical files referenced

| File | Role |
|---|---|
| `prompts/extract_bde_v5.md` | Extraction prompt |
| `src/run_pipeline.py:build_question_history_block` | Per-turn history block constructor (v5 version with queue position + Q&A so far) |
| `src/run_pipeline.py:parse_qa_so_far` | Splits transcript context to extract Q&A-so-far excerpt and prior analyst names |
| `src/llm_client.py:call_llm` | LLM client; `OPENAI_MODEL=gpt-5-mini` by default |
| `data/personas_v5/*.json` | 16 output persona files |
| `data/prompt_logs_v5/extract_*.txt` | Full extraction prompts saved per analyst (for reproducibility) |

## Comparison to V1

| Dimension | V1 | v5 |
|---|---|---|
| Prompt file | `prompts/extract_bde.md` | `prompts/extract_bde_v5.md` |
| Per-turn metadata | Setup + question + response | + Queue position + prior analysts + Q&A so far |
| Schema top-level fields | 3 (coverage, reasoning, recurring) | 5 (+ queue_behavior + cross_analyst_reactivity) |
| Extracts behavior under queue order | No | Yes |
| Extracts reactivity to peer Q&A | No | Yes |
| Avg persona JSON size | 7-10 KB | 4-7 KB (v5 also drops some V1 fields that overlapped) |
| Wall time per extraction | ~5s | ~5s (same model, similar history length) |

## Known limitations

1. **Thin-history analysts have empty/thin v5 `recurring_concerns.core_topics`** — andrew=0, lizzie/sharon=2. The `queue_behavior` + `cross_analyst_reactivity` fields partially compensate but cannot fully replace topic priors.
2. **No peer-transcript signal in v5 extraction** — the Auto pipeline does use peer data via auto-discovery, but v5 does not. Could be added in a v6 by extending TRAIN to `data_auto/train_combined.json` with `peer_ticker` annotations preserved.
3. **Cold-start fallback is identical to Auto's fallback** — both xian and kevin use `data_auto/final_personas/_fallback.json`, so v5 has no advantage over V1 or Auto on cold-start cells.
