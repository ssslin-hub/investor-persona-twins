You are revising ONE analyst's STRUCTURED PERSONA so that a downstream
simulator predicts their next questions on a held-out call more accurately.

The persona is a JSON object with sub-profiles like `coverage_profile`,
`reasoning_style`, `recurring_concerns`, and (in some rounds) extra fields
introduced by the shared prompt. You will edit ONE field of the persona at
a time, at a SUMMARY level (trait / habit / lens), NOT at the question or
topic level.

# Your input

1. ANALYST_NAME — the name of the analyst.
2. CURRENT_PERSONA — the analyst's current persona JSON.
3. CAL_ACTUALS — the analyst's actual question(s) on the calibration call(s)
   they participated in, plus the management presentation context.
4. CURRENT_PREDICTIONS — what the simulator predicted under the current
   persona.
5. JUDGE_REASONING — the judge's match-level and reasoning per actual.
6. FORBIDDEN_NGRAMS — verbatim 4-grams from CAL actuals that you must NOT
   paste into the persona.

# How to reason — three explicit stages

## Stage 1: What information did this analyst attend to in their actual question?

≤2 sentences. Identify the signal TYPE (multi-year frame, single-quarter
event, margin bridge, etc.), not the topic word.

## Stage 2: How did they reason from that signal to their question?

≤2 sentences. Describe the cognitive move (anchor against a baseline,
decompose a number, bridge a near-term observation to a longer-term narrative,
etc.).

## Stage 3: What summary-level trait did the current persona miss?

The trait that, if added or rewritten in the persona, would have made the
simulator's prediction closer to the actual.

**Phrase the trait at the LENS / HABIT level, NOT at the TOPIC level.**

Bad (over-specific, will be REJECTED):
  - "Add to `recurring_concerns.core_topics`: 'Mediterranean disruption'."
  - "Mention 'Trifecta plan' in `anchoring_habits`."
  - "Predicted question should ask about WAVE bookings."

Good (summary-level):
  - "Expand `reasoning_style.anchoring_habits` to note that this analyst
    consistently re-frames near-term events against multi-year guidance,
    rather than treating them as standalone."
  - "Add to `reasoning_style.follow_up_pattern` that this analyst tends to
    open with a strategic 'step back' frame before drilling into numeric
    decomposition."
  - "Revise `coverage_profile.rhetorical_signature` to include the pattern
    of opening with a congratulatory line followed by a paired
    strategic+numeric question."

# Output JSON

Produce a single JSON object as your FINAL output (the orchestrator parses
only the JSON; you may print the three reasoning stages BEFORE the JSON):

```
{
  "what_attended": "<≤2 sentences>",
  "how_reasoned": "<≤2 sentences>",
  "trait_edit": "<which sub-profile field is being revised and what general trait is being added or rewritten — at lens/habit level>",
  "rule": "<one-sentence general principle>",
  "new_persona": <complete revised persona JSON; preserve all existing fields, modify only those required>
}
```

# Hard rules — the orchestrator will REJECT your edit if any of these fail

1. `new_persona` must not contain any verbatim 4-gram from FORBIDDEN_NGRAMS
   (anti-leakage).
2. `trait_edit` must reference a sub-profile FIELD (e.g.,
   `reasoning_style.anchoring_habits`), not a question template.
3. `trait_edit` must NOT name a specific topic or event word from CAL_ACTUALS
   (e.g., "Mediterranean", "fuel hedge", "Trifecta", "WAVE season") unless it
   is simultaneously generalized ("regional disruption", "cost line",
   "company growth plan").
4. `new_persona` total length must not exceed 1.30× the current persona length.

If the current persona is already capturing the missed trait and no edit
would help, return `trait_edit: "noop"` and copy CURRENT_PERSONA verbatim
into `new_persona`.

---

ANALYST_NAME: {analyst_name}

CURRENT_PERSONA:
{current_persona}

CAL_ACTUALS:
{cal_actuals}

CURRENT_PREDICTIONS:
{current_predictions}

JUDGE_REASONING:
{judge_reasoning}

FORBIDDEN_NGRAMS (4-grams from CAL actuals — do NOT paste into new_persona):
{forbidden_ngrams}
