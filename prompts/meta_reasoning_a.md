You are revising a SHARED EXTRACTION PROMPT used to build structured personas
of sell-side equity research analysts who cover Royal Caribbean (RCL). The
revised prompt will be applied to every analyst's question history to produce
their persona, which is then used by a separate simulator to predict their
questions on a held-out call.

Your job is to read the current prompt, see how its personas performed on the
calibration set, identify ONE GENERAL property of analyst behavior that the
current prompt is failing to extract, and propose a SUMMARY-LEVEL edit to the
prompt that fixes it. You will not see any test-set actuals; only the
calibration set actuals.

# Your input

You will be given:

1. CURRENT_PROMPT — the full text of the round t-1 extraction prompt.
2. CAL_FEEDBACK — for each analyst on calibration, the predicted question(s)
   under the current prompt, the actual question, the judge's match-level
   (exact / partial / miss), and the judge's reasoning.
3. DIFF_LOG — list of prior rounds' accepted edits, each with a one-sentence
   "rule", an "evidence_count" (how many analysts supported it), and a
   "diff_summary".
4. EDIT_BUDGET — strict constraints on what kind of edit you may propose.

# How to reason — three explicit stages

Produce your output in three stages BEFORE the JSON edit:

## Stage 1: What information did each analyst attend to?

For each analyst on CAL who MISSED or only PARTIAL'd, identify in ≤2 sentences
which signals from the management presentation they actually picked up on in
their actual question. Be specific to the signal type (a multi-year framing,
a single-quarter event, a margin bridge, a regional disruption, a hardware
ramp, etc.) — NOT the specific topic word.

Example: "Matthew Boss attended to the multi-year frame around the company's
own growth plan and pre-pandemic comparables; he set aside the most recent
regional disruption noted in the presentation."

## Stage 2: How did they reason from those signals to their question?

For each, ≤2 sentences on the cognitive move from the attended signal to the
question. What kind of inference did they make? (anchor against a baseline,
decompose a guide into drivers, bridge a near-term softness to a longer-term
narrative, etc.)

Example: "He used the pre-pandemic anchor as a fixed reference, then asked
whether durable drivers explain the gap between current guidance and that
reference."

## Stage 3: What general property of analyst behavior did the current persona / prompt MISS?

Synthesize across ≥2 analysts. Identify the general trait, lens, or
extraction instruction that — if added to the prompt — would make personas
capture this missed property going forward.

**WRITE AT THE SUMMARY LEVEL. Describe the missing trait or extraction
instruction, NOT the specific question, topic, or event.**

Bad (over-specific):
  - "Personas should mention the Mediterranean disruption."
  - "Personas should track WAVE-season booking strength."
  - "Add a `mediterranean_softness` field."

Good (summary-level):
  - "Personas should record whether the analyst tends to anchor against
    multi-year frames rather than react to single-quarter events."
  - "The `reasoning_style.anchoring_habits` field should be expanded to
    enumerate the 2-3 most frequent anchors the analyst uses across calls."
  - "Add a `framing_template` sub-field that captures the analyst's most
    consistent opener phrasing, derivable from any ticker's call."

# Output JSON

After the three reasoning stages (which you can output as plain text or
chain-of-thought BEFORE the JSON), produce a single JSON object as your
FINAL output (the orchestrator parses only the JSON):

```
{
  "what_attended": {
    "<analyst_name>": "<≤2 sentences>",
    ...
  },
  "how_reasoned": {
    "<analyst_name>": "<≤2 sentences>",
    ...
  },
  "rule": "<one-sentence general principle that motivated the edit; written at trait/lens/instruction level, NOT topic level>",
  "evidence_count": <int — number of distinct CAL analysts whose misses this rule would have helped>,
  "edit_type": "add_field" | "remove_field" | "rewrite_allocation" | "noop",
  "diff_summary": "<≤3 sentences summarising the change at trait level>",
  "new_prompt": "<full revised prompt text; if edit_type=noop, repeat the current prompt verbatim>"
}
```

# Hard rules — the orchestrator will REJECT your edit if any of these fail

1. `evidence_count` must be ≥2. Edits that help only one CAL analyst are
   over-niche.
2. `new_prompt` length must not exceed 1.25× the current prompt length
   (anti-bloat).
3. `new_prompt` must not contain any verbatim 4-gram that appears in any CAL
   actual question (you will not be shown TEST actuals, but the same check
   runs against them; never copy CAL actuals into the prompt).
4. `diff_summary` and `new_prompt` must not name a specific calibration-
   quarter topic or event (e.g., "Mediterranean", "WAVE season",
   "Perfecta plan") without simultaneously generalizing it ("regional
   disruption", "wave-of-bookings dynamic", "multi-year framework").

# What you may and may not edit in `new_prompt`

May:
  - Add / remove / rename sub-profile fields at Layer 1 (the BDE skeleton).
  - Reword the Layer 2 evidence-allocation instructions (which kinds of
    turns should fill which sub-profile fields).
  - Revise the peer-vs-RCL separation rule.
  - Add or revise the `framing_template` / anchoring instructions.

May NOT:
  - Write specific question templates or opener phrases.
  - Name specific analysts.
  - Refer to specific CAL or TEST actuals.

If the current prompt is already capturing the property well and no edit
would help, output `edit_type: "noop"` and copy the current prompt verbatim
into `new_prompt`.

---

CURRENT_PROMPT:
{current_prompt}

CAL_FEEDBACK:
{cal_feedback}

DIFF_LOG:
{diff_log}

EDIT_BUDGET:
{edit_budget}
