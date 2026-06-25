"""B2 evaluator stability check.

Re-run B2 per-actual 3 times on Auto K=10 with a stronger model (gpt-5).
Compare per-cell scores across runs to quantify evaluator variance.

For each of 3 runs:
  - 12 cells (analyst × actual, Robin split into 2)
  - call B2 evaluator with model='gpt-5'
  - persist per-cell output

Then compute cross-run comparison:
  - per cell: 3 scores + range + all-equal flag
  - aggregate: cells stable / cells flipped binary / sub-dim consistency
  - per-run binary/strong rates

Writes:
  data_auto/final_eval_10q_auto/b2_stability/run_<i>/<cell>.json (36 files)
  data_auto/final_eval_10q_auto/b2_stability/comparison.json
  data_auto/final_eval_10q_auto/b2_stability/per_run_summary.json
  reports/b2_stability_gpt5.md
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from statistics import mean, stdev

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import load_text  # noqa: E402

DATA_AUTO = os.path.join(ROOT, "data_auto")
PROMPTS = os.path.join(ROOT, "prompts")
SRC_DIR = os.path.join(DATA_AUTO, "final_eval_10q_auto")
_B2_PROMPT_PATH = os.environ.get("B2_PROMPT_PATH", os.path.join(PROMPTS, "b2_eval.md"))
if not os.path.isabs(_B2_PROMPT_PATH):
    _B2_PROMPT_PATH = os.path.join(ROOT, _B2_PROMPT_PATH)
B2_TPL = load_text(_B2_PROMPT_PATH)
B2_MODEL = os.environ.get("B2_STABILITY_MODEL", "gpt-5")
OUT_DIR_NAME = os.environ.get("B2_STABILITY_OUTDIR", "b2_stability")
_seed_env = os.environ.get("B2_SEED")
B2_SEED = int(_seed_env) if _seed_env else None
OUT_DIR = os.path.join(SRC_DIR, OUT_DIR_NAME)
N_RUNS = 3


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def b2_per_actual_call(analyst: str, candidates: list, actual: dict, log_to: str) -> dict:
    sim_block = {"analyst_name": analyst, "predicted_questions": candidates}
    actuals_b2 = [{
        "tuple_id": f"{analyst}-actual-single",
        "analyst_name": analyst,
        "call": actual.get("call"),
        "question": actual.get("question"),
    }]
    stub = {"analyst_name": analyst, "match_score_0_to_4": 0, "binary_match": False,
            "topic_match": "none", "trigger_alignment": "none",
            "question_form_alignment": "none", "granularity_alignment": "none",
            "reasoning": "DRY", "miss_or_gap": "DRY"}
    prompt = (B2_TPL
              .replace("{{SIMULATION_JSON}}", json.dumps(sim_block, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals_b2, indent=2)))
    try:
        out = call_llm(prompt, model=B2_MODEL, expect_json=True, dry_run_stub=stub, log_to=log_to, seed=B2_SEED)
        return parse_json_strict(out)
    except Exception as e:
        print(f"    ! B2 call failed: {type(e).__name__}: {str(e)[:120]}")
        return stub


def run_once(run_idx: int) -> list[dict]:
    """Run B2 per-actual on all 12 cells. Returns list of cell dicts."""
    run_dir = os.path.join(OUT_DIR, f"run_{run_idx}")
    log_dir = os.path.join(run_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    summary = json.load(open(os.path.join(SRC_DIR, "summary.json")))
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]

    cells = []
    print(f"\n=== Run {run_idx} ({B2_MODEL}) ===")
    for name in sorted(actuals_by.keys()):
        actuals = actuals_by.get(name, [])
        cell_data = summary["per_analyst"].get(name) or {}
        candidates = (cell_data.get("predictions") or {}).get("predicted_questions", [])
        if not actuals or not candidates:
            continue
        for i, actual in enumerate(actuals):
            cell_id = f"{_safe(name)}_a{i}"
            ev = b2_per_actual_call(name, candidates, actual,
                                     log_to=os.path.join(log_dir, f"{cell_id}.txt"))
            ev["analyst_name"] = name
            ev["actual_index"] = i
            ev["cell_id"] = cell_id
            cells.append(ev)
            # Persist per-cell file
            with open(os.path.join(run_dir, f"{cell_id}.json"), "w") as f:
                json.dump(ev, f, indent=2)
            score = ev.get("match_score_0_to_4", 0)
            bin_ = ev.get("binary_match", False)
            print(f"  {cell_id:32s} score={score} binary={bin_}")

    n = len(cells)
    bin_count = sum(1 for c in cells if c.get("binary_match"))
    strong_count = sum(1 for c in cells if (c.get("match_score_0_to_4") or 0) >= 4)
    avg_score = sum(c.get("match_score_0_to_4", 0) for c in cells) / max(1, n)
    run_summary = {
        "run": run_idx,
        "model": B2_MODEL,
        "evaluated_count": n,
        "binary_match_count": bin_count,
        "binary_match_rate": bin_count / max(1, n),
        "strong_match_count": strong_count,
        "strong_match_rate": strong_count / max(1, n),
        "average_match_score_0_to_4": avg_score,
        "cells": cells,
    }
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(run_summary, f, indent=2)
    print(f"  Run {run_idx}: bin>=3 {bin_count}/{n}={bin_count/n:.3f}  "
          f"strong>=4 {strong_count}/{n}={strong_count/n:.3f}  avg={avg_score:.3f}")
    return cells


def compare_runs(all_runs: list[list[dict]]) -> dict:
    """Cross-run comparison per cell. all_runs[i] = list of cells for run i+1."""
    n_runs = len(all_runs)
    n_cells = len(all_runs[0]) if all_runs else 0
    # Build cell-level table: cell_id -> [score_run1, score_run2, score_run3]
    table = {}
    for run_cells in all_runs:
        for c in run_cells:
            cid = c["cell_id"]
            table.setdefault(cid, []).append({
                "score": c.get("match_score_0_to_4", 0),
                "binary": c.get("binary_match", False),
                "topic_match": c.get("topic_match"),
                "trigger_alignment": c.get("trigger_alignment"),
                "question_form_alignment": c.get("question_form_alignment"),
                "granularity_alignment": c.get("granularity_alignment"),
            })

    cells_stable = 0
    cells_flipped_binary = 0
    cells_flipped_any = 0
    cell_details = {}
    sub_dim_flips = Counter()

    for cid, runs_data in table.items():
        scores = [r["score"] for r in runs_data]
        bins = [r["binary"] for r in runs_data]
        all_same_score = len(set(scores)) == 1
        binary_consistent = len(set(bins)) == 1
        if all_same_score:
            cells_stable += 1
        else:
            cells_flipped_any += 1
        if not binary_consistent:
            cells_flipped_binary += 1
        # Sub-dim flips
        for dim in ("topic_match", "trigger_alignment", "question_form_alignment", "granularity_alignment"):
            vals = [r[dim] for r in runs_data]
            if len(set(vals)) > 1:
                sub_dim_flips[dim] += 1
        cell_details[cid] = {
            "scores": scores,
            "score_min": min(scores),
            "score_max": max(scores),
            "score_range": max(scores) - min(scores),
            "all_equal": all_same_score,
            "binary": bins,
            "binary_consistent": binary_consistent,
            "topic_match": [r["topic_match"] for r in runs_data],
            "trigger_alignment": [r["trigger_alignment"] for r in runs_data],
            "question_form_alignment": [r["question_form_alignment"] for r in runs_data],
            "granularity_alignment": [r["granularity_alignment"] for r in runs_data],
        }

    # Aggregate
    return {
        "n_runs": n_runs,
        "n_cells": n_cells,
        "model": B2_MODEL,
        "cells_stable_count": cells_stable,
        "cells_stable_rate": cells_stable / max(1, n_cells),
        "cells_flipped_any_count": cells_flipped_any,
        "cells_flipped_binary_count": cells_flipped_binary,
        "sub_dim_flips": dict(sub_dim_flips),
        "cell_details": cell_details,
    }


def write_report(comparison: dict, per_run: list[dict]):
    lines = [
        f"# B2 evaluator stability check ({comparison['model']}, {comparison['n_runs']} runs)",
        "",
        f"**Data**: Auto K=10 predictions × 12 actuals (Robin split into 2 cells). "
        f"Same `prompts/b2_eval.md`, same data, only LLM call repeated.",
        "",
        "## Headline",
        "",
        f"- **Cells with identical score across all 3 runs**: "
        f"{comparison['cells_stable_count']}/{comparison['n_cells']} = "
        f"{comparison['cells_stable_rate']:.3f}",
        f"- **Cells that flipped binary (≥3) boundary**: "
        f"{comparison['cells_flipped_binary_count']}/{comparison['n_cells']}",
        f"- **Cells with any score variance**: "
        f"{comparison['cells_flipped_any_count']}/{comparison['n_cells']}",
        "",
        "## Per-run aggregates",
        "",
        f"| Run | binary≥3 | strong≥4 | avg score |",
        f"|---|---|---|---|",
    ]
    for r in per_run:
        lines.append(
            f"| Run {r['run']} | {r['binary_match_count']}/{r['evaluated_count']} = {r['binary_match_rate']:.3f} | "
            f"{r['strong_match_count']}/{r['evaluated_count']} = {r['strong_match_rate']:.3f} | "
            f"{r['average_match_score_0_to_4']:.3f} |"
        )
    lines.extend([
        "",
        "## Per-cell score variance",
        "",
        "| Cell | Run 1 | Run 2 | Run 3 | range | stable? |",
        "|---|---|---|---|---|---|",
    ])
    for cid, d in sorted(comparison["cell_details"].items()):
        s = d["scores"]
        stable_mark = "✓" if d["all_equal"] else "✗"
        lines.append(f"| {cid} | {s[0]} | {s[1]} | {s[2]} | {d['score_range']} | {stable_mark} |")

    lines.extend([
        "",
        "## Sub-dimension flip counts",
        "",
        "| Sub-dim | # cells where this sub-dim changed across runs |",
        "|---|---|",
    ])
    for dim in ("topic_match", "trigger_alignment", "question_form_alignment", "granularity_alignment"):
        lines.append(f"| {dim} | {comparison['sub_dim_flips'].get(dim, 0)} / {comparison['n_cells']} |")

    lines.extend([
        "",
        "## Decision rule",
        "",
        "- ≥10/12 cells identical → evaluator stable, use gpt-5 going forward",
        "- 7-9/12 stable → moderate, average across 3 runs",
        "- <7/12 stable → revise `prompts/b2_eval.md`",
        "",
    ])

    if comparison["cells_stable_count"] >= 10:
        verdict = "**Evaluator is STABLE** at gpt-5. Recommend switching the canonical B2 evaluator to gpt-5."
    elif comparison["cells_stable_count"] >= 7:
        verdict = "**Moderate instability.** Recommend reporting 3-run averages in the paper."
    else:
        verdict = "**Unstable even at gpt-5.** Next step: revise prompt for more deterministic scoring."
    lines.append(f"### Verdict: {verdict}")

    safe_model = B2_MODEL.replace("/", "_").replace(".", "_")
    out_path = os.path.join(ROOT, "reports", f"b2_stability_{safe_model}.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"\nwrote {out_path}")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    all_runs = []
    per_run_summary = []
    for i in range(1, N_RUNS + 1):
        cells = run_once(i)
        all_runs.append(cells)
        run_summary_path = os.path.join(OUT_DIR, f"run_{i}", "summary.json")
        per_run_summary.append(json.load(open(run_summary_path)))

    comparison = compare_runs(all_runs)
    with open(os.path.join(OUT_DIR, "comparison.json"), "w") as f:
        json.dump(comparison, f, indent=2)
    with open(os.path.join(OUT_DIR, "per_run_summary.json"), "w") as f:
        json.dump(per_run_summary, f, indent=2)

    write_report(comparison, per_run_summary)

    print(f"\n=== HEADLINE ===")
    print(f"  Cells stable: {comparison['cells_stable_count']}/{comparison['n_cells']}")
    print(f"  Cells flipped binary boundary: {comparison['cells_flipped_binary_count']}/{comparison['n_cells']}")
    for r in per_run_summary:
        print(f"  Run {r['run']}: binary={r['binary_match_rate']:.3f} strong={r['strong_match_rate']:.3f} avg={r['average_match_score_0_to_4']:.3f}")


if __name__ == "__main__":
    main()
