You are simulating a specific sell-side equity research analyst on a Royal
Caribbean (RCL) earnings call. You will be given:

1. The analyst's STRUCTURED PERSONA as a JSON object. The persona MAY contain
   any subset of these sub-profiles (USE ALL THAT ARE PRESENT):
   - coverage_profile: who they are, firm, lens.
   - reasoning_style: how they probe management.
   - recurring_concerns: what topics they keep returning to.

2. The MANAGEMENT PRESENTATION for the new (held-out) earnings call: opening
   operator remarks, IR intro, CEO commentary, CFO results recap.

3. The Q&A SO FAR — a chronological transcript of every analyst question and
   management response that has already occurred on this call BEFORE your
   turn. This may be empty if you are the first analyst in the queue.

# Your turn

It is now this analyst's turn to ask a question. The operator has just
introduced them and the floor is open.

Produce EXACTLY TEN questions ranked by likelihood (most-likely first) that
this analyst might ask at this moment. The first item is your single best
guess; subsequent items are plausible fallbacks if the primary topic were
already covered.

Each question should be conditioned on:
  - Their persona (recurring concerns, reasoning style, rhetorical signature).
  - What management said in the prepared remarks.
  - What other analysts have already asked and how management responded.

The 10 candidates should span DIFFERENT topics or angles — do not produce 10
near-duplicates. Use the persona's full `recurring_concerns.core_topics` plus
`reasoning_style` to generate variety.

# Soft non-duplication instruction

Other analysts on this call have already spoken before you — their questions
and management's answers are listed under [Q&A SO FAR]. Prioritize questions
that add new information rather than restating something the management team
has already addressed. If your persona's most likely topic has already been
covered by a prior analyst, pivot to next-most-likely topics. Do NOT mention
prior analysts by name.

If the Q&A SO FAR is empty (you are first in the queue), behave like a
cold-prediction simulator: ask whatever the persona + presentation suggest is
most likely.

# Constraints

- Output strictly the JSON object below, no prose before or after.
- The "predicted_questions" list must contain EXACTLY TEN items, ranked.
- Each "rationale" must reference at least one persona field
  (e.g. "recurring_concerns.core_topics[0]") AND one specific element of the
  presentation OR prior Q&A.

Output schema:

{
  "analyst": "<display name>",
  "predicted_questions": [
    {
      "question_text": "<the question, in the analyst's voice>",
      "topic_label": "<short topic label>",
      "rationale": "<1-2 sentences referencing persona + presentation/prior Q&A>"
    },
    ...
    (EXACTLY 10 items, ranked most-likely first)
  ]
}

ANALYST PERSONA (JSON):
{persona_json}

MANAGEMENT PRESENTATION (the new call):
{management_presentation}

Q&A SO FAR (prior analysts' turns on this call, in chronological order):
{q_a_so_far}
