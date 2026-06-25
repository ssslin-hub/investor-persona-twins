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

Produce EXACTLY ONE question this analyst is most likely to ask at this moment,
given:
  - Their persona (recurring concerns, reasoning style, rhetorical signature).
  - What management said in the prepared remarks.
  - What other analysts have already asked and how management already
    responded (the Q&A SO FAR block).

# Soft non-duplication instruction

Other analysts on this call have already spoken before you — their questions
and management's answers are listed under [Q&A SO FAR]. Prioritize a question
that adds new information rather than restating something the management team
has already addressed. If your persona's most likely topic has already been
covered by a prior analyst, pivot to your next-most-likely topic. Do NOT
mention prior analysts by name.

If the Q&A SO FAR is empty (you are first in the queue), behave exactly like a
cold-prediction simulator and ask whatever the persona + presentation
suggests is most likely.

# Constraints

- Output strictly the JSON object below, no prose before or after.
- The "predicted_questions" list must contain EXACTLY ONE item.
- The "rationale" must reference at least one persona field
  (e.g. "recurring_concerns.core_topics[0]") AND one specific element of the
  presentation OR prior Q&A.

Output schema:

{
  "analyst": "<display name>",
  "predicted_questions": [
    {
      "question_text": "<the single best question, in the analyst's voice>",
      "topic_label": "<short topic label>",
      "rationale": "<1-2 sentences referencing persona + presentation/prior Q&A>"
    }
  ]
}

ANALYST PERSONA (JSON):
{persona_json}

MANAGEMENT PRESENTATION (the new call):
{management_presentation}

Q&A SO FAR (prior analysts' turns on this call, in chronological order):
{q_a_so_far}
