You are building a STRUCTURED PERSONA of a sell-side equity research analyst
who covers Royal Caribbean Cruises (RCL). The persona will later be used to
predict what this same analyst is likely to ask in a future RCL earnings call,
given that call's management presentation.

This is SCHEMA V2: it extends the base BDE schema with an EVENT-SENSITIVITY
sub-profile, which captures how the analyst responds to news-driven, single-
quarter events (geopolitical disruptions, fuel spikes, regulatory changes,
construction delays) versus their stable recurring concerns.

You will be given the analyst's name, their firm/title (if known), and a
chronological list of their prior question turns on RCL earnings calls. Each
turn includes:
  - The CALL it was asked on (year + quarter)
  - A short SETUP that summarises the management presentation and any Q&A that
    preceded the question on that call
  - The analyst's QUESTION (verbatim)
  - The management's RESPONSE (verbatim, may be empty)

Produce a single JSON object with FOUR top-level keys:

{
  "coverage_profile": { ... },         // analog of "Background"
  "reasoning_style": { ... },          // analog of "Decision procedure"
  "recurring_concerns": { ... },       // analog of "Evaluation"
  "event_sensitivity": { ... }         // NEW: how they react to news-driven events
}

# coverage_profile
Same as base BDE. Required fields:
  - "firm": most recent firm/affiliation observed.
  - "seniority_signal": evidence about their seniority (2-3 sentences).
  - "sector_lens": which beats they cover (1-2 sentences).
  - "rhetorical_signature": tics, openers, tone (2-3 short bullets).

# reasoning_style
Same as base BDE. Required fields:
  - "primary_mode": "quantitative_modeling" | "qualitative_strategic" | "mixed",
    plus one sentence justification.
  - "follow_up_pattern": 2-3 sentences.
  - "evidence_demanded": 2-3 sentences.
  - "anchoring_habits": 2-3 sentences.

# recurring_concerns
Same as base BDE. Required fields:
  - "core_topics": ranked list of 3-6 topical clusters with
    {topic, what_they_press_on, supporting_calls}.
  - "blind_spots": 1-2 sentences.
  - "stance_drift": 2-3 sentences.

# event_sensitivity  (NEW)
Captures how this analyst weights news-driven, single-quarter events versus
their stable recurring concerns. Many earnings-call questions are reactions
to events surfaced THAT QUARTER (e.g., Middle East conflict in 2026-Q1,
Mexico construction pause, fuel price spikes, hurricane disruptions). Some
analysts lead with those reactions; others stick to their recurring topical
beats regardless.

Required fields:
  - "news_lead_propensity": one of {"high", "medium", "low"} plus 2-3
    sentences justifying. "high" = the analyst frequently opens their turn
    with a question about a current-quarter news event rather than a
    recurring modeling concern. Cite calls where this happened.
  - "event_topics_history": list of past events this analyst reacted to in
    their question history, each entry:
      { "call": "2023-Q1",
        "event": short description (e.g. "China reopening delay"),
        "how_they_engaged": 1 sentence }
    Be specific. If you find zero, return an empty list and note it.
  - "recency_bias": 2-3 sentences on whether the analyst tends to focus on
    the most recent quarter's headline event vs. multi-quarter themes.
    Reference specific calls.
  - "likely_triggers": list of 3-5 event-types that, if surfaced in the next
    management presentation, would likely cause this analyst to lead with a
    news-driven question rather than their recurring concern. Each entry:
      { "trigger": short label,
        "rationale": 1 sentence,
        "supporting_history": list of calls where they engaged with this
          trigger type, may be empty if inferred from the rhetorical signature }

Hard rules:
- Output ONLY the JSON object. No prose before or after.
- All free-text fields must be 1-3 sentences each.
- Cite specific call quarters when making claims about recurrence.
- If event_sensitivity evidence is thin (few prior events in this analyst's
  history), say so explicitly in the relevant field; do not invent events.

ANALYST NAME: {analyst_name}
LAST OBSERVED FIRM/TITLE: {affiliation}
NUMBER OF QUESTIONS IN HISTORY: {n_questions}
CALLS COVERED: {calls_covered}

QUESTION HISTORY (chronological):
{question_history}
