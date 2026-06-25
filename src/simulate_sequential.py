"""Sequential K-call simulator: per twin, call LLM K times, each call sees
all PRIOR predictions for that twin and produces ONE new distinct question.

Usage: python3 src/simulate_sequential.py --K <int> --source v1|auto

Output: data_auto/final_eval_seq_{K}q_{source}/summary.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import _fill, load_text  # noqa: E402

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
V1_PERSONAS = os.path.join(ROOT, "data", "personas")
AUTO_PERSONAS = os.path.join(DATA_AUTO, "final_personas")
SIM_PROMPT = os.path.join(PROMPTS, "simulate_questions_sequential.md")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]
COLD_START = ["xian siew", "kevin kopelman"]
ALL_11 = TEST_RETURNING + COLD_START


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def _load_persona(name: str, source: str) -> dict | None:
    if source == "v1":
        if name in COLD_START:
            p = os.path.join(AUTO_PERSONAS, "_fallback.json")
        else:
            p = os.path.join(V1_PERSONAS, f"{_safe(name)}.json")
    else:
        if name in COLD_START:
            p = os.path.join(AUTO_PERSONAS, "_fallback.json")
        else:
            p = os.path.join(AUTO_PERSONAS, f"{_safe(name)}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def _build_prompt(tpl: str, persona: dict, mgmt: str, prior: list[dict]) -> str:
    if "[Q&A SO FAR]" in mgmt:
        mgmt = mgmt.split("[Q&A SO FAR]", 1)[0].rstrip()
    return _fill(
        tpl,
        persona_json=json.dumps(persona, indent=2),
        management_presentation=mgmt,
        prior_questions_json=json.dumps(prior, indent=2),
    )


def run(K: int, source: str) -> None:
    out_dir = os.path.join(DATA_AUTO, f"final_eval_seq_{K}q_{source}")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]
    actuals_by = test["per_analyst_actual_questions"]
    tpl = load_text(SIM_PROMPT)

    per_analyst: dict[str, dict] = {}
    total = 0
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals:
            continue
        persona = _load_persona(name, source)
        if persona is None:
            print(f"  ! {name}: no persona; skip")
            continue
        prior: list[dict] = []
        for i in range(K):
            prompt = _build_prompt(tpl, persona, mgmt, prior)
            stub = {"question_text": f"DRY_RUN q{i+1}", "topic_label": "demand/booking_curve",
                    "rationale": "DRY"}
            log = os.path.join(log_dir, f"sim_{_safe(name)}_iter{i+1}.txt")
            try:
                out = call_llm(prompt, expect_json=True, dry_run_stub=stub, log_to=log)
                q = parse_json_strict(out)
            except Exception as e:
                print(f"  ! {name} iter {i+1}: {type(e).__name__}: {str(e)[:120]}")
                q = {"question_text": f"[ERROR iter {i+1}]", "topic_label": "unknown",
                     "rationale": f"error: {str(e)[:100]}"}
            # Defensive: accept either single-object or array (some models wrap)
            if isinstance(q, list) and q:
                q = q[0]
            # Drop any nested predicted_questions wrapper
            if "predicted_questions" in q and isinstance(q["predicted_questions"], list) and q["predicted_questions"]:
                q = q["predicted_questions"][0]
            prior.append({
                "question_text": q.get("question_text", ""),
                "topic_label": q.get("topic_label", ""),
                "rationale": q.get("rationale", ""),
            })
        per_analyst[name] = {
            "n_actual": len(actuals),
            "predictions": {"predicted_questions": prior},
            "persona_source": source if name in TEST_RETURNING else "auto-fallback",
        }
        total += len(prior)
        topics = [p["topic_label"] for p in prior]
        print(f"  {name:25s} K={len(prior)}  topics={topics[:5]}{'...' if len(topics)>5 else ''}")

    summary = {
        "n_analysts_scored": len(per_analyst),
        "K": K,
        "source": source,
        "mode": "sequential",
        "total_predicted_questions": total,
        "per_analyst": per_analyst,
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_dir}/summary.json ({total} questions, {len(per_analyst)} analysts)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, required=True)
    ap.add_argument("--source", choices=["v1", "auto"], required=True)
    args = ap.parse_args()
    run(args.K, args.source)


if __name__ == "__main__":
    main()
