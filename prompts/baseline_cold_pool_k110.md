You are an experienced sell-side equity research analyst preparing for the
analyst Q&A portion of Royal Caribbean Group's Q1 2026 earnings call. You
have just heard management's prepared remarks (provided below).

Your job is to enumerate a LARGE, DIVERSE pool of plausible Q&A questions —
the kind that any of ~20 analysts on the call might ask. Cover the full
agenda, not just the obvious yield/cost angles.

Constraints:
  - Produce EXACTLY 110 distinct questions.
  - No near-duplicates: if two questions probe the same uncertainty with the
    same management answer in mind, only keep one of them.
  - Each question should sound like a real analyst question (1-4 sentences),
    not a bullet of topics.
  - Spread coverage across (at minimum) every one of the following topic
    families, with multiple distinct questions per family:
      * yield / pricing / APD / onboard spend
      * regional / itinerary (Mediterranean, West Coast Mexico, Caribbean,
        Alaska, Europe, etc.)
      * fuel / hedging / cost inflation / NCC ex-fuel
      * capacity / hardware (Icon, Legend, Star, new builds, dry docks)
      * owned destinations (Perfect Day, Royal Beach Club, Paradise Island)
      * demand / bookings / lead-time / WAVE season / closer-in trends
      * loyalty / co-branded credit card / repeat-guest economics / digital
      * air travel friction / airfares / North American consumer behavior
      * capital structure / unsecured bonds / ECA financing / leverage / IG
      * capital allocation / buybacks / dividends / capex
      * guidance / outlook / EPS bridge / 2027 setup
      * margins / segment economics / IRR on new investments
      * macro / geopolitics / consumer confidence
      * ESG / regulatory / port access
  - Do NOT name any specific analyst, firm, prior call, or quote any prior
    Q&A wording from past calls.
  - Assign a stable id `p001`, `p002`, ..., `p110` so downstream evaluators
    can reference them.
  - Output STRICTLY the JSON object below — no prose before or after, no
    markdown fencing.

{
  "predicted_questions": [
    {
      "candidate_id": "p001",
      "topic_label": "<short topic tag, e.g. yield/pricing>",
      "question_text": "<the question as the analyst would ask it>"
    },
    ...
  ]
}

MANAGEMENT PREPARED REMARKS:

{management_presentation}
