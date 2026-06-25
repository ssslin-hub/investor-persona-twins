# Claude Code instruction: regenerate personas with extract_bde_v5

Paste the block below verbatim into Claude Code. It is fully self-contained
and will not touch the existing `data/personas/`, `prompts/extract_bde.md`,
or any other v1–v4 artifact.

---

You are working in the repo `invest-call-twins/investorPersona/`. The goal is
to regenerate all analyst personas using the new prompt at
`prompts/extract_bde_v5.md`, writing results to `data/personas_v5/` so the
existing `data/personas/` directory is preserved untouched.

The new prompt requires the LLM to see two pieces of per-turn metadata that
the current pipeline strips out before sending to the model:

1. The analyst's **position in the call's Q&A queue** (e.g. "#5 of 8 unique
   analysts on this call") plus the **names of analysts who spoke earlier on
   that same call**.
2. A **truncated [Q&A SO FAR] excerpt** showing what those prior analysts
   actually asked, so the model can judge whether this analyst is reframing,
   piggybacking, picking white space, etc.

Both pieces of information are already present in `data/analysts.json` —
specifically in each record's `context` field, which contains a
`[Q&A SO FAR]` section that `build_question_history_block` currently discards.
Your job is to surface them without altering the existing v1 pipeline.

## Step 1 — make the minimal code changes

Modify `src/run_pipeline.py` as follows. Do NOT rename or delete any existing
function; only add new behavior and a CLI flag.

(a) Add a helper `parse_qa_so_far(context: str) -> tuple[list[str], str]` that
    splits a `context` string at the `[Q&A SO FAR]` marker, then within the
    Q&A-so-far block extracts:
      - the ordered list of unique analyst speaker names (from lines that
        look like `Name (Title, Firm):` or that follow an `Operator: ... line
        ... will come from the line of NAME with FIRM` cue),
      - a truncated excerpt of the Q&A-so-far text (cap at 2000 characters,
        keeping the last 2000 chars so the most recent questions survive
        truncation).
    Be defensive — if the marker is absent, return `([], "")`.

(b) Modify `build_question_history_block` so that for each turn it ALSO
    computes:
      - `prior_analysts` = list of unique analyst names extracted from that
        turn's `context` Q&A-so-far section,
      - `position_in_call` = `len(prior_analysts) + 1`,
      - `qa_so_far_excerpt` = the truncated excerpt (or `"(this analyst spoke first)"`
        if empty).
    The per-turn block emitted to the prompt should now look like:

        --- TURN {i} | CALL: {call} | TICKER: {ticker} | SECTOR: {sector} | FIRM: {firm} ---
        [Queue position] This analyst was #{position_in_call} to speak on this call.
        [Analysts who spoke before them on this call]
        {comma-joined prior_analysts, or "(none — they were first)"}

        [Setup: management presentation excerpt]
        {existing presentation excerpt, unchanged}

        [Q&A SO FAR — what prior analysts asked, truncated]
        {qa_so_far_excerpt}

        [Operator intro to analyst, if any]
        {existing operator_intro, unchanged}

        [Analyst question]
        {existing question, unchanged}

        [Management response excerpt]
        {existing response, unchanged}

    Keep the existing `_truncate`, `MGMT_EXCERPT_CHARS`, and
    `MAX_HISTORY_TURNS` constants. Do not lower `MAX_HISTORY_TURNS`.

(c) Add a CLI flag `--persona-out-subdir` (default `"personas"`) to
    `run_pipeline.py` and thread it through `run(...)`. Replace the hardcoded
    `persona_dir = os.path.join(data_dir, "personas")` line with
    `persona_dir = os.path.join(data_dir, persona_out_subdir)`. Do the same
    threading for the `prompt_logs` directory by adding
    `--log-out-subdir` (default `"prompt_logs"`) so v5 logs do not overwrite
    v1 logs. Predictions and scores should stay at their default paths for
    now — we only want to regenerate personas in this run.

(d) Add a `--skip-simulate-and-judge` flag (default False) to
    `run_pipeline.py`. When set, run only Step 1 (persona extraction) and
    skip Steps 2–4. This lets us regenerate personas without burning tokens
    on prediction / judging until we have inspected the new personas.

## Step 2 — run the regeneration

Make sure `OPENAI_API_KEY` is set in the environment. Then from
`invest-call-twins/investorPersona/`, run:

    python3 src/run_pipeline.py \
        --extraction-prompt extract_bde_v5.md \
        --persona-out-subdir personas_v5 \
        --log-out-subdir prompt_logs_v5 \
        --skip-simulate-and-judge

This must:
- Read `data/analysts.json` and `data/analysts_test.json` (existing inputs,
  unchanged).
- Produce `data/personas_v5/<analyst_name>.json` for every analyst with
  ≥ 5 prior turns OR who appears in the 2026-Q1 hold-out (same target rule
  as the v1 pipeline — do not change `MIN_QUESTIONS`).
- Write per-analyst prompt logs to `data/prompt_logs_v5/extract_*.txt`.
- NOT touch `data/personas/`, `data/predictions/`, `data/scores/`,
  `data/prompt_logs/`, or any v1–v4 prompt file.

If `OPENAI_API_KEY` is not set, run the same command with `DRY_RUN=1` first
to dump prompts only, then confirm with the user before live-running.

## Step 3 — spot-check three personas

After the run, inspect `data/personas_v5/brandt_montour.json`,
`data/personas_v5/robin_farley.json`, and
`data/personas_v5/patrick_scholes.json`. For each, verify the JSON contains
all five top-level keys (`coverage_profile`, `reasoning_style`,
`recurring_concerns`, `queue_behavior`, `cross_analyst_reactivity`) and that:

- `recurring_concerns.core_topics` is ranked by `n_turns` descending and each
  topic has integer `n_turns`, `n_calls`, and float `share_of_calls`.
- `queue_behavior.adaptation_when_favorites_taken` contains at least one of
  the tags listed in the v5 prompt with a quoted ≤ 12-word verbatim phrase
  and a cited call.
- `cross_analyst_reactivity.explicit_peer_references` reports an integer
  count of turns (may be 0 — that's fine, just must be an integer).

Then print a short diff against the v1 version of the same persona — for
each analyst, list:
  - top-5 topics in v1 (in v1's order) vs top-5 topics in v5 (with n_turns).
  - whether v5 added any topic that was absent from v1.
  - whether v5 demoted any topic that was top-3 in v1.

Do NOT run the simulator or judge yet. We will inspect the v5 personas
first and decide whether to also bump the simulator prompt before
regenerating predictions.

## Step 4 — report back

Reply with:
  (i)   the list of analyst files written, with file sizes;
  (ii)  the three-persona spot check from Step 3;
  (iii) any analyst where the LLM refused to emit one of the new sections
        (`queue_behavior` or `cross_analyst_reactivity`) so we know which
        ones need a manual re-run.

Do not modify any other file in the repo. Do not commit. Do not run the
simulator or judge. Stop after Step 4.
