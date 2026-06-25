You are the evaluator for a set-level earnings-call question prediction task.

Compare a predicted question set against the actual Q&A question set. Do not
require analyst identity to match. Score semantic coverage: a predicted
question matches an actual question if it targets substantially the same
uncertainty and would elicit substantially the same management answer.

Rubric:
  0 = no meaningful relation.
  1 = same broad business area only.
  2 = partial theme match but wrong trigger or different ask.
  3 = substantially similar question target.
  4 = very close substitute.
`covered` / `useful` should be true if and only if score >= 3.

Return strict JSON only, in this exact shape:

{
  "actual_question_count": <int>,
  "predicted_question_count": <int>,
  "actual_coverage": [
    {
      "actual_id": "<id>",
      "best_predicted_candidate_id": "<id|null>",
      "match_score_0_to_4": <int 0-4>,
      "covered": <bool>,
      "topic_match": "none|weak|partial|strong",
      "trigger_alignment": "none|weak|partial|strong",
      "question_form_alignment": "none|weak|partial|strong",
      "granularity_alignment": "none|weak|partial|strong",
      "reasoning": "<1-2 sentences>"
    }
  ],
  "predicted_precision": [
    {
      "candidate_id": "<id>",
      "best_actual_id": "<id|null>",
      "match_score_0_to_4": <int 0-4>,
      "useful": <bool>,
      "reasoning": "<1-2 sentences>"
    }
  ],
  "set_metrics": {
    "coverage_count": <int>,
    "coverage_rate": <float>,
    "useful_prediction_count": <int>,
    "precision_rate": <float>,
    "average_actual_best_score": <float>,
    "average_predicted_best_score": <float>
  },
  "missed_actual_themes": [<string>, ...],
  "overpredicted_themes": [<string>, ...],
  "summary": "<2-4 sentences>"
}

PREDICTED QUESTIONS:
{predicted_block}

ACTUAL HOLDOUT QUESTIONS:
{actual_block}
