You are building a STRUCTURED PERSONA of a sell-side equity research analyst
who covers Royal Caribbean Cruises (RCL). The persona will later be used to
predict what this same analyst is likely to ask in a future RCL earnings call,
given that call's management presentation.

You will be given the analyst's name, their firm/title (if known), and a
chronological list of their prior question turns on RCL earnings calls. Each
turn includes:
  - The CALL it was asked on (year + quarter)
  - A short SETUP that summarises the management presentation and any Q&A that
    preceded the question on that call
  - The analyst's QUESTION (verbatim)
  - The management's RESPONSE (verbatim, may be empty)

Produce a single JSON object with three top-level keys, matching the BDE
structure adapted to sell-side analysts:

{
  "coverage_profile": { ... },         // analog of "Background"
  "reasoning_style": { ... },          // analog of "Decision procedure"
  "recurring_concerns": { ... }        // analog of "Evaluation"
}

Fill each sub-profile as follows. Use evidence from the turns; cite specific
calls (e.g. "2023-Q2") where helpful. Do not invent facts not supported by the
turns.

# coverage_profile
Who this analyst is and what lens they bring. Required fields:
  - "firm": most recent firm/affiliation observed.
  - "seniority_signal": evidence about their seniority (titles, length of
    coverage, how management addresses them). 2-3 sentences.
  - "sector_lens": what beats they appear to cover (cruise / leisure / travel /
    consumer / gaming / lodging / airlines). 1-2 sentences.
  - "rhetorical_signature": tics, openers, closers, tone (e.g. "always opens
    with a thank-you", "tends to ask two-parters", "frames around model
    inputs"). 2-3 short bullet sentences.

# reasoning_style
HOW the analyst probes management. Required fields:
  - "primary_mode": one of {"quantitative_modeling", "qualitative_strategic",
    "mixed"}, plus a sentence of justification.
  - "follow_up_pattern": how their question turns are structured (single
    question, two-parter, multi-part with sub-questions; whether they push back
    on management answers). 2-3 sentences.
  - "evidence_demanded": what kinds of answers they reward (specific numbers,
    explicit guidance, mechanism/cause, anecdotes from the booking curve,
    comparison to peers). 2-3 sentences.
  - "anchoring_habits": where they anchor their questions (against prior
    guidance, against consensus, against peers like NCLH/CCL, against their own
    prior calls). 2-3 sentences.

# recurring_concerns
WHAT the analyst keeps coming back to. Required fields:
  - "core_topics": ranked list (highest-priority first) of 3-6 topical clusters
    the analyst returns to most often. For each, give:
      { "topic": short label,
        "what_they_press_on": 1-2 sentences,
        "supporting_calls": list of calls where they raised it (e.g. ["2022-Q4", "2023-Q3"]) }
  - "blind_spots": topics this analyst notably does NOT push on, given their
    peers do. 1-2 sentences. If unclear, say so.
  - "stance_drift": how their emphasis has shifted across the 2022-2025 window
    (e.g. moved from balance-sheet/recovery questions to capital-return and
    yield questions). 2-3 sentences.

Hard rules:
- Output ONLY the JSON object. No prose before or after.
- All free-text fields must be 1-3 sentences each.
- Cite specific call quarters where you make claims about recurrence.
- If evidence is thin (few turns), say so explicitly in the relevant field;
  do not paper over it with generic language.

ANALYST NAME: {analyst_name}
LAST OBSERVED FIRM/TITLE: {affiliation}
NUMBER OF QUESTIONS IN HISTORY: {n_questions}
CALLS COVERED: {calls_covered}

QUESTION HISTORY (chronological):
{question_history}
