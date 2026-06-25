"""B4 set-level evaluator on Auto K=10 pool with gpt-5 (stability upgrade
over the prior gpt-5-mini B4 run).

Reads:
  data_auto/final_eval_10q_auto/summary.json  per_analyst.predictions.predicted_questions
  data_auto/test.json                          per_analyst_actual_questions

Writes:
  data_auto/final_eval_10q_auto/b4_gpt5/b4.json
  data_auto/final_eval_10q_auto/b4_gpt5/b4_prompt.txt
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
K10_DIR = os.path.join(DATA_AUTO, "final_eval_10q_auto")
OUT_DIR = os.path.join(K10_DIR, "b4_gpt5")
B4_PROMPT_PATH = os.path.join(PROMPTS, "b4_eval.md")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora", "xian siew", "kevin kopelman",
]


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    summary = json.load(open(os.path.join(K10_DIR, "summary.json")))
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]

    predicted: list[dict] = []
    actuals: list[dict] = []

    for name in TEST_RETURNING:
        pa = summary.get("per_analyst", {}).get(name) or {}
        for i, q in enumerate((pa.get("predictions") or {}).get("predicted_questions", [])):
            predicted.append({
                "candidate_id": f"{_safe(name)}-pred-{i}",
                "source_analyst": name,
                "question": q.get("question_text", ""),
                "topic_label": q.get("topic_label", ""),
            })
        for i, a in enumerate(actuals_by.get(name, [])):
            actuals.append({
                "actual_id": f"{_safe(name)}-actual-{i}",
                "source_analyst": name,
                "question": a.get("question", ""),
            })

    print(f"predicted set size: {len(predicted)};  actual set size: {len(actuals)}")

    tpl = open(B4_PROMPT_PATH).read()
    prompt = (tpl
              .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(predicted, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
    log = os.path.join(OUT_DIR, "b4_prompt.txt")
    out = call_llm(prompt, model="gpt-5", expect_json=True, log_to=log)
    ev = parse_json_strict(out)

    with open(os.path.join(OUT_DIR, "b4.json"), "w") as f:
        json.dump(ev, f, indent=2)

    m = ev.get("set_metrics", {})
    print(f"\nB4 set_metrics (gpt-5, K=10):")
    print(f"  coverage:  {m.get('coverage_count','?')}/{ev.get('actual_question_count','?')} = {m.get('coverage_rate','?')}")
    print(f"  precision: {m.get('useful_prediction_count','?')}/{ev.get('predicted_question_count','?')} = {m.get('precision_rate','?')}")
    print(f"  avg actual best:    {m.get('average_actual_best_score','?')}")
    print(f"  avg predicted best: {m.get('average_predicted_best_score','?')}")

    # Identity-matched coverage
    pred_by_id = {p["candidate_id"]: p for p in predicted}
    act_by_id = {a["actual_id"]: a for a in actuals}
    id_match = 0
    for c in ev.get("actual_coverage", []):
        if not c.get("covered"):
            continue
        bp = c.get("best_predicted_candidate_id")
        aid = c.get("actual_id")
        if not bp or not aid:
            continue
        if pred_by_id.get(bp, {}).get("source_analyst") == act_by_id.get(aid, {}).get("source_analyst"):
            id_match += 1
    print(f"  identity-matched coverage: {id_match}/{ev.get('actual_question_count','?')}")

    # Strong variants (score == 4)
    cov_strong = sum(1 for c in ev.get("actual_coverage", [])
                     if c.get("match_score_0_to_4", 0) >= 4)
    prec_strong = sum(1 for p in ev.get("predicted_precision", [])
                      if p.get("match_score_0_to_4", 0) >= 4)
    print(f"  coverage (strong ≥4):  {cov_strong}/{ev.get('actual_question_count','?')}")
    print(f"  precision (strong ≥4): {prec_strong}/{ev.get('predicted_question_count','?')}")


if __name__ == "__main__":
    main()
