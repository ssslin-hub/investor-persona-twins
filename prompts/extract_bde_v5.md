You are building a STRUCTURED PERSONA of a sell-side equity research analyst
who covers Royal Caribbean Cruises (RCL). The persona will later be used to
predict what this same analyst is likely to ask in a FUTURE RCL earnings call,
given (a) that call's management presentation and (b) which other analysts have
already spoken on that call.

You will be given the analyst's name, their firm/title (if known), and a
chronological list of their prior question turns. For each turn you receive:
  - The CALL it was asked on (year + quarter)
  - POSITION metadata: this analyst was the Nth analyst to speak on that call,
    out of M total unique analysts. The names of the analysts who spoke BEFORE
    them on the same call are listed explicitly.
  - A short SETUP excerpt of the management presentation.
  - The verbatim [Q&A SO FAR] excerpt — what the prior analysts asked BEFORE
    this analyst took their turn. This is critical: use it to judge whether
    this analyst is reframing a topic that was already raised, picking
    untouched white space, or reacting to something a peer just asked.
  - The analyst's QUESTION (verbatim).
  - The management's RESPONSE excerpt (verbatim, may be empty).

Produce a single JSON object with FIVE top-level keys:

{
  "coverage_profile":          { ... },   // analog of "Background"
  "reasoning_style":           { ... },   // analog of "Decision procedure"
  "recurring_concerns":        { ... },   // analog of "Evaluation"
  "queue_behavior":            { ... },   // NEW — adaptation under queue order
  "cross_analyst_reactivity":  { ... }    // NEW — explicit references to peers / management
}

Fill each sub-profile as follows. Use evidence from the turns; cite specific
calls (e.g. "2023-Q2") and quote short verbatim phrases (≤ 12 words) where
helpful. Do not invent facts not supported by the turns.

# coverage_profile
Who this analyst is and what lens they bring. Required fields:
  - "firm": most recent firm/affiliation observed.
  - "seniority_signal": evidence about their seniority (titles, length of
    coverage, how management addresses them). 2-3 sentences.
  - "sector_lens": what beats they cover (cruise / leisure / travel /
    consumer / gaming / lodging / airlines). 1-2 sentences.
  - "rhetorical_signature": tics, openers, closers, tone. 2-3 short bullets.
    If a fixed opener phrase recurs in ≥ 30% of calls, quote it verbatim and
    give the frequency (e.g. "opens with 'Great. Thanks' in 13 of 17 calls").

# reasoning_style
HOW the analyst probes management. Required fields:
  - "primary_mode": one of {"quantitative_modeling", "qualitative_strategic",
    "mixed"}, plus one sentence of justification grounded in the turns.
  - "follow_up_pattern": within-turn structure (single question, two-parter,
    multi-part), and whether they push back. 2-3 sentences. Quantify with
    rough fraction (e.g. "≈ 18% of turns contain ≥ 2 question marks").
  - "evidence_demanded": what answers they reward — specific numbers (bps, %,
    $), explicit guidance, mechanism, peer comparison. 2-3 sentences. If you
    claim they "demand bps", state the actual count of turns using bps.
  - "anchoring_habits": where they anchor — prior guidance, 2019 baseline,
    specific management line just delivered, peers (NCLH/CCL), industry
    supply, their own prior questions. 2-3 sentences. If they anchor against
    peers, cite the calls.

# recurring_concerns
WHAT the analyst keeps coming back to. Required fields:
  - "core_topics": ranked list of 5-8 topical clusters, RANKED BY n_turns
    DESCENDING (not by perceived importance). For each topic, give:
      {
        "topic": "short label (snake_case or short phrase)",
        "n_turns": <integer, count of question turns touching this topic>,
        "n_calls": <integer, count of distinct calls where it was raised>,
        "share_of_calls": <float, n_calls divided by total calls covered, rounded to 2 decimals>,
        "what_they_press_on": "1-2 sentences",
        "supporting_calls": ["2022-Q4", "2023-Q3", ...]
      }
    A topic must have n_turns ≥ 2 to be listed. If fewer than 5 topics meet
    that threshold, list as many as do and say so explicitly in "blind_spots".
  - "blind_spots": topics this analyst notably does NOT push on, given peers
    do. Be concrete (e.g. "0 turns on fuel hedging despite peers asking in
    every Q3 call"). 2-3 sentences.
  - "stance_drift": how emphasis has shifted across the window. Cite at least
    two specific quarter-pairs (e.g. "in 2022-Q1/Q2 he asked about testing
    requirements; by 2024 these dropped to zero turns"). 2-3 sentences.

# queue_behavior   (NEW)
How this analyst behaves depending on WHERE in the call they speak. Required:
  - "typical_position": rough range observed (e.g. "#3–#5 of ≈8 analysts; was
    #1 on 2 of 16 calls, #13+ on 6 of 16").
  - "default_first_pick": when they are first/early to speak (no topics taken
    yet), what topic do they typically open with? Cite the calls where they
    were first.
  - "adaptation_when_favorites_taken": when their top-3 core_topics have
    already been raised by prior analysts, what do they do? Choose ONE OR MORE
    of the following tags AND quote evidence per tag:
      * "reframe_deeper"           — re-ask the same topic at a deeper modeling
                                     angle (e.g. asking for like-for-like
                                     decomposition after headline yield was
                                     covered).
      * "white_space"              — pivot to a topic few or no peers cover
                                     (e.g. loyalty program data, agent feedback,
                                     specific destination ramp).
      * "cross_narrative_reconcile"— ask management to reconcile two threads
                                     that emerged earlier in the Q&A.
      * "peer_or_industry_meta"    — ask about peer/industry behavior rather
                                     than the company directly.
      * "reactive_followup"        — piggyback on a specific phrase a prior
                                     analyst or management used.
      * "stay_on_topic_anyway"     — re-ask the popular topic regardless.
    For each tag chosen, cite ≥ 1 call and quote ≤ 12 verbatim words.
  - "white_space_topics": list of topic labels this analyst raises that few
    peers do (with supporting_calls). Empty list if none.

# cross_analyst_reactivity   (NEW)
How this analyst integrates in-call context that is not in the management
presentation. Required:
  - "explicit_peer_references": how often (count of turns and example phrases)
    they explicitly cite another analyst's question. Examples to look for:
    "following up on Steven's question", "to Robin's earlier point",
    "one of your larger peers". Quote ≤ 12 words per example.
  - "management_line_anchoring": how often they anchor on a SPECIFIC number
    or phrase management just delivered in this call ("the 90 basis points
    you laid out", "the 5% implied yield guidance"). Count + 1-2 examples.
  - "operator_or_followup_signal": whether they tend to take their second turn
    (when allowed) and what for — clarification, deeper drill, or new topic.

Hard rules:
- Output ONLY the JSON object. No prose before or after.
- All free-text fields are 1-3 sentences each.
- Cite specific call quarters whenever you make a claim about recurrence.
- Quantify with integer counts (n_turns, n_calls) wherever the schema asks.
  Do NOT use vague intensifiers ("often", "frequently") without an integer
  count or fraction next to them.
- If evidence for a field is thin or absent, write the field with an explicit
  note such as "no evidence in history" or "n_turns < 2; insufficient to
  characterise". Do not paper over thin evidence with generic language.
- Ranking of core_topics is by n_turns descending. If two topics tie, break
  by n_calls descending, then alphabetical.
- All quoted verbatim phrases must be ≤ 12 words and appear in the question
  history you were given.

ANALYST NAME: {analyst_name}
LAST OBSERVED FIRM/TITLE: {affiliation}
NUMBER OF QUESTIONS IN HISTORY: {n_questions}
CALLS COVERED: {calls_covered}

QUESTION HISTORY (chronological):
{question_history}
