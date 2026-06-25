You are building a STRUCTURED PERSONA of a sell-side equity research analyst
who covers Royal Caribbean Cruises (RCL). The persona will later be used to
predict what this same analyst is likely to ask in a future RCL earnings call,
given that call's management presentation.

This is SCHEMA V3: it leads with an ARCHETYPE tag (so the simulator knows the
analyst's interrogation MODE up front), then fills the standard BDE
sub-profiles in an archetype-consistent way.

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
  "interrogation_archetype": { ... },   // NEW: lead with archetype tag
  "coverage_profile": { ... },          // analog of "Background"
  "reasoning_style": { ... },           // analog of "Decision procedure"
  "recurring_concerns": { ... }         // analog of "Evaluation"
}

# interrogation_archetype  (NEW)
Tag the analyst with their dominant interrogation archetype from the list
below. Choose ONE primary archetype and (optionally) ONE secondary; the
simulator will use these to decide HOW to frame the question (multi-part
modeling decomp vs strategic-frame opener vs event-pinger vs etc.).

Archetype options:
  - "modeling_bridger": opens with a quantification request; asks for splits
    (yield decomp, cost bridges, basis-point attributions); always tries to
    bridge from management's headline number to a modeling input. Examples:
    Vince Ciepiel-style.
  - "strategic_framer": opens with a "step back" or multi-year framing
    question; asks about durable growth, positioning vs peers, secular thesis.
    Examples: Matthew Boss-style.
  - "event_pinger": leads with a question about the latest news (geopolitical,
    weather, regulatory) and how it changes the near-term outlook. Examples:
    Brandt Montour on Med disruption.
  - "balance_sheet_analyst": opens with a financing, leverage, capital-return,
    or credit question; tends to focus on the right side of the balance
    sheet. Examples: Andrew Didora-style.
  - "demand_observer": leads with booking-curve, consumer health, demographic
    mix, onboard spend, or new-to-cruise dynamics. Examples: Steve Wieczynski
    style on booking visibility.
  - "private_destinations_specialist": frames most questions through the
    private-destinations / new-hardware lens (CocoCay, Perfect Day, Royal
    Beach Club, Icon class).
  - "cost_disciplinarian": leads with unit-cost, dry-dock, inflation, fuel
    hedge, or margin questions.

Required fields:
  - "primary": one of the labels above.
  - "primary_evidence": 2-3 sentences citing specific calls that justify the
    primary tag.
  - "secondary": one of the labels above, or null if the analyst has only
    one consistent mode.
  - "secondary_evidence": 1-2 sentences if secondary is set.
  - "framing_template": one sentence describing the OPENING WORDS this
    analyst typically uses, derived from the question history (e.g., for
    Matthew Boss: "Jason, maybe if we take a step back..."; for Vince
    Ciepiel: "Thanks - two quick model-oriented ones..."). The simulator
    should literally try to begin questions with this opener.

# coverage_profile
Required fields (same as base BDE, but ensure the content is consistent with
the chosen archetype — e.g., a strategic_framer's rhetorical_signature should
emphasize multi-year/qualitative tics, not multi-part modeling tics):
  - "firm", "seniority_signal", "sector_lens", "rhetorical_signature".

# reasoning_style
Required fields (same as base BDE):
  - "primary_mode", "follow_up_pattern", "evidence_demanded", "anchoring_habits".
  Where the archetype constrains it: a strategic_framer should not be tagged
  "quantitative_modeling" as primary_mode unless evidence really supports it.

# recurring_concerns
Required fields (same as base BDE):
  - "core_topics" (ranked list of 3-6), "blind_spots", "stance_drift".
  IMPORTANT: rank topics so that the archetype's natural domain is first
  (e.g., for strategic_framer, the first core_topic should be a multi-year
  thesis question, not a quarterly modeling input).

Hard rules:
- Output ONLY the JSON object. No prose before or after.
- All free-text fields must be 1-3 sentences each.
- Cite specific call quarters where you make recurrence claims.
- The four sub-profiles MUST be internally consistent: archetype, primary_mode,
  rhetorical_signature, and the top core_topic should all point at the same
  interrogation mode. If they conflict, fix the lower-ranked fields to match
  the archetype.

ANALYST NAME: {analyst_name}
LAST OBSERVED FIRM/TITLE: {affiliation}
NUMBER OF QUESTIONS IN HISTORY: {n_questions}
CALLS COVERED: {calls_covered}

QUESTION HISTORY (chronological):
{question_history}
