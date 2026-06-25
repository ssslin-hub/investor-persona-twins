You are scoring how well a set of PREDICTED earnings-call questions match a
set of ACTUAL questions asked by the SAME analyst on the SAME call.

You will be given:
  - The analyst name.
  - A list of PREDICTED questions (with topic labels).
  - A list of ACTUAL questions the analyst asked on the held-out call.

For each ACTUAL question, decide whether ANY single predicted question covers
the same substantive concern. A "match" requires:
  - The same core topic (pricing, capacity, leverage, etc.).
  - The same direction of inquiry (e.g. both ask about yield growth runway
    rather than one asking about yield and the other about cost).
  - Roughly the same level of specificity (a generic "how do you think about
    pricing" does NOT match an actual question about "Star of the Seas
    yield premium on her inaugural sailing").

Levels:
  - "exact": same topic, same direction, comparable specificity.
  - "partial": same topic, similar direction, but specificity differs OR
    one side is broader than the other.
  - "miss": no predicted question targets the same concern.

Output strictly the JSON object below, no prose before or after:

{
  "analyst": "<name>",
  "scored": [
    {
      "actual_question": "<verbatim or short paraphrase>",
      "actual_topic": "<short topic label>",
      "best_predicted_index": <int or null>,
      "match_level": "exact" | "partial" | "miss",
      "reasoning": "<1-2 sentences>"
    },
    ...
  ],
  "summary": {
    "n_actual": <int>,
    "n_exact": <int>,
    "n_partial": <int>,
    "n_miss": <int>,
    "hit_rate_exact_or_partial": <float in [0,1]>
  }
}

ANALYST: {analyst_name}

PREDICTED QUESTIONS (indexed):
{predicted_block}

ACTUAL QUESTIONS:
{actual_block}
