"""Chunked B4 precision re-evaluation: split candidates into chunks of CHUNK_SIZE,
call B4 on each chunk independently, merge predicted_precision rows.

Fixes the K>=16 evaluator-truncation problem where a single 200+ candidate
prompt makes gpt-5 silently drop most precision rows.

Usage:
  python3 src/b4_chunked_precision.py --in-summary <path> --out-dir <path> [--chunk-size 50]

Output:
  <out-dir>/b4_precision_chunked.json
    - per_chunk: list of {chunk_idx, candidates, predicted_precision_rows, useful_count, strong_count}
    - merged: {evaluated_count, useful_count, useful_rate, strong_count, strong_rate, total_predicted, ...}
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

PROMPTS = os.path.join(ROOT, "prompts")
TEST_JSON = os.path.join(ROOT, "data_auto", "test.json")
B4_PROMPT_PATH = os.path.join(PROMPTS, "b4_eval.md")
MODEL = os.environ.get("EVAL_MODEL", "gpt-5")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]
COLD_START = ["xian siew", "kevin kopelman"]
ALL_11 = TEST_RETURNING + COLD_START


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def build_pool(summary: dict, actuals_by: dict) -> tuple[list[dict], list[dict]]:
    predicted = []
    actuals = []
    for name in ALL_11:
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
    return predicted, actuals


def run(in_summary: str, out_dir: str, chunk_size: int) -> None:
    os.makedirs(out_dir, exist_ok=True)
    log_dir = os.path.join(out_dir, "chunked_logs")
    os.makedirs(log_dir, exist_ok=True)
    summary = json.load(open(in_summary))
    test = json.load(open(TEST_JSON))
    actuals_by = test["per_analyst_actual_questions"]
    predicted, actuals = build_pool(summary, actuals_by)

    n_total = len(predicted)
    n_chunks = (n_total + chunk_size - 1) // chunk_size
    print(f"Chunked B4 precision: {n_total} candidates → {n_chunks} chunks of ≤{chunk_size}")
    print(f"Evaluator: {MODEL}, actuals={len(actuals)}")

    tpl = open(B4_PROMPT_PATH).read()
    per_chunk = []
    merged_rows = []
    seen_ids = set()

    for chunk_idx in range(n_chunks):
        start = chunk_idx * chunk_size
        end = min(start + chunk_size, n_total)
        chunk = predicted[start:end]
        print(f"\n--- chunk {chunk_idx+1}/{n_chunks}: candidates [{start}:{end}] (n={len(chunk)}) ---")
        prompt = (tpl
                  .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(chunk, indent=2))
                  .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
        log = os.path.join(log_dir, f"chunk_{chunk_idx+1}_prompt.txt")
        try:
            out = call_llm(prompt, model=MODEL, expect_json=True, log_to=log)
            ev = parse_json_strict(out)
        except Exception as e:
            print(f"  ! chunk {chunk_idx+1} failed: {type(e).__name__}: {str(e)[:150]}")
            ev = {"predicted_precision": []}

        rows = ev.get("predicted_precision", []) or []
        chunk_useful = sum(1 for r in rows if (r.get("match_score_0_to_4") or 0) >= 3)
        chunk_strong = sum(1 for r in rows if (r.get("match_score_0_to_4") or 0) >= 4)
        print(f"  returned {len(rows)} rows ({len(rows)}/{len(chunk)} coverage), "
              f"useful={chunk_useful}, strong={chunk_strong}")
        # Deduplicate by candidate_id in case LLM repeats
        for r in rows:
            cid = r.get("candidate_id")
            if cid and cid not in seen_ids:
                merged_rows.append(r)
                seen_ids.add(cid)
        per_chunk.append({
            "chunk_idx": chunk_idx + 1,
            "candidate_range": [start, end],
            "candidates_in_chunk": len(chunk),
            "precision_rows_returned": len(rows),
            "useful_count": chunk_useful,
            "strong_count": chunk_strong,
            "raw_set_metrics": ev.get("set_metrics"),
        })

    # Aggregate
    n_eval = len(merged_rows)
    useful = sum(1 for r in merged_rows if (r.get("match_score_0_to_4") or 0) >= 3)
    strong = sum(1 for r in merged_rows if (r.get("match_score_0_to_4") or 0) >= 4)
    out = {
        "in_summary": in_summary,
        "model": MODEL,
        "chunk_size": chunk_size,
        "n_total_candidates": n_total,
        "n_chunks": n_chunks,
        "n_evaluated_candidates": n_eval,
        "useful_count": useful,
        "useful_rate_on_all": useful / n_total if n_total else 0,
        "useful_rate_on_eval": useful / n_eval if n_eval else 0,
        "strong_count": strong,
        "strong_rate_on_all": strong / n_total if n_total else 0,
        "strong_rate_on_eval": strong / n_eval if n_eval else 0,
        "per_chunk": per_chunk,
        "merged_precision_rows": merged_rows,
    }
    with open(os.path.join(out_dir, "b4_precision_chunked.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n=== MERGED ===")
    print(f"  evaluated: {n_eval}/{n_total} ({100*n_eval/max(1,n_total):.1f}%)")
    print(f"  useful ≥3: {useful}/{n_total} = {useful/max(1,n_total):.3f}  "
          f"(on-eval: {useful}/{n_eval} = {useful/max(1,n_eval):.3f})")
    print(f"  strong ≥4: {strong}/{n_total} = {strong/max(1,n_total):.3f}  "
          f"(on-eval: {strong}/{n_eval} = {strong/max(1,n_eval):.3f})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-summary", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--chunk-size", type=int, default=50)
    args = ap.parse_args()
    run(args.in_summary, args.out_dir, args.chunk_size)


if __name__ == "__main__":
    main()
