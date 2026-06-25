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

Your job: produce EXACTLY ONE question this analyst is most likely to ask on
this call, given the persona and what management just said. The question
should:
  - Be phrased the way THIS analyst phrases questions (single vs. two-parter,
    quant vs. qualitative, rhetorical signature from the persona).
  - Pull at the recurring_concerns topics that this management presentation
    leaves unanswered or partially answered.
  - Be plausible to a careful reader who has read both the persona and the
    presentation — not a generic earnings-call question.

If the analyst's pattern is consistently a two-parter, fold both parts into
one `question_text` string. Do NOT produce more than one item in the list.

Constraints:
- Output strictly the JSON object below, no prose before or after.
- The "predicted_questions" list must contain EXACTLY ONE item.
- The "rationale" must reference at least one persona field
  (e.g. "recurring_concerns.core_topics[0]") AND one specific element of the
  management presentation (e.g. "CEO mentioned 14% yield growth").

Output schema:

{
  "analyst": "<display name>",
  "predicted_questions": [
    {
      "question_text": "<the single best question, in the analyst's voice>",
      "topic_label": "<short topic label, e.g. 'pricing/yield', 'capacity', 'leverage', 'capital_return', 'demand/booking_curve', 'costs', 'private_destinations', 'consumer_health', 'M&A', 'guidance_setting'>",
      "rationale": "<1-2 sentences referencing persona + presentation>"
    }
  ]
}

ANALYST PERSONA (JSON):
{persona_json}

MANAGEMENT PRESENTATION (the new call, no Q&A):
{management_presentation}
