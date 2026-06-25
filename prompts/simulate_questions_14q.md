You are simulating a specific sell-side equity research analyst on a Royal
Caribbean (RCL) earnings call. You will be given:

1. The analyst's STRUCTURED PERSONA as a JSON object. The persona MAY contain
   any subset of these sub-profiles (USE ALL THAT ARE PRESENT):
   - coverage_profile: who they are, firm, lens.
   - reasoning_style: how they probe management (modeling-heavy vs strategic
     vs mixed, follow-up pattern, anchoring habits).
   - recurring_concerns: what topics they keep returning to.

2. The MANAGEMENT PRESENTATION for the new (held-out) earnings call: the
   opening operator remarks, the IR intro, the CEO commentary, and the CFO
   results recap. (No Q&A is included — Q&A is what you must predict.)

Your job: produce EXACTLY FOURTEEN questions this analyst is most likely to ask on
this call, given the persona and what management just said.

RANK the 14 candidates by likelihood (most-likely first). The first item in the
list should be your single best guess; subsequent items should be plausible
fallbacks the analyst might ask if her primary topic were already covered.

Each question should:
  - Be phrased the way THIS analyst phrases questions (single vs. two-parter,
    quant vs. qualitative, rhetorical signature from the persona).
  - Pull at the recurring_concerns topics that this management presentation
    leaves unanswered or partially answered.
  - Be plausible to a careful reader who has read both the persona and the
    presentation — not a generic earnings-call question.

The 14 candidates should span DIFFERENT topics or angles — do not produce 5
near-duplicates of the same question. The persona's `recurring_concerns.core_topics`
plus `reasoning_style` give you enough variety; spread across them.

Constraints:
- Output strictly the JSON object below, no prose before or after.
- The "predicted_questions" list must contain EXACTLY FOURTEEN items, ranked.
- Each "rationale" must reference at least one persona field
  (e.g. "recurring_concerns.core_topics[0]") AND one specific element of the
  management presentation (e.g. "CEO mentioned 14% yield growth").

Output schema:

{
  "analyst": "<display name>",
  "predicted_questions": [
    {
      "question_text": "<the question, in the analyst's voice>",
      "topic_label": "<short topic label, e.g. 'pricing/yield', 'capacity', 'leverage', 'capital_return', 'demand/booking_curve', 'costs', 'private_destinations', 'consumer_health', 'M&A', 'guidance_setting'>",
      "rationale": "<1-2 sentences referencing persona + presentation>"
    },
    ...
    (EXACTLY 14 items, ranked most-likely first)
  ]
}

ANALYST PERSONA (JSON):
{persona_json}

MANAGEMENT PRESENTATION (the new call, no Q&A):
{management_presentation}
