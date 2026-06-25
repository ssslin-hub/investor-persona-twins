"""Within-twin pairwise B2 similarity over top-3 sets across 6 settings.
For each twin × each pair of settings (A, B): treat top-3 of A as the simulation
candidates, the first-rank question of B as the actual; B2 returns best-pair
score. Single direction (asymmetry documented).

Output: data_auto/top_picks/within_twin_pairwise.json
"""

from __future__ import annotations

import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402

PROMPTS = os.path.join(ROOT, "prompts")
TOP_PICKS = os.path.join(ROOT, "data_auto", "top_picks")
B2_TPL = open(os.path.join(PROMPTS, "b2_eval.md")).read()
MODEL = "gpt-5"

ALL_11 = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora", "xian siew", "kevin kopelman",
]
SETTINGS = ["parallel_K10_v1", "parallel_K10_auto",
            "parallel_K14_v1", "parallel_K14_auto",
            "parallel_K20_v1", "parallel_K20_auto"]


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def b2_pair(analyst: str, top3_a: list[dict], anchor_b: dict, log_to: str) -> int:
    """Call B2 with A's top-3 as candidates, B's first question as the actual."""
    sim = {"analyst_name": analyst, "predicted_questions": top3_a}
    actuals = [{"tuple_id": f"{analyst}-top1-of-B",
                "analyst_name": analyst,
                "call": "2026-Q1 top-pick comparison",
                "question": anchor_b.get("question_text", "")}]
    prompt = (B2_TPL
              .replace("{{SIMULATION_JSON}}", json.dumps(sim, indent=2))
              .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(actuals, indent=2)))
    try:
        out = call_llm(prompt, model=MODEL, expect_json=True,
                       dry_run_stub={"match_score_0_to_4": 0}, log_to=log_to)
        ev = parse_json_strict(out)
        return int(ev.get("match_score_0_to_4") or 0)
    except Exception as e:
        print(f"  ! {analyst}: {type(e).__name__}: {str(e)[:120]}")
        return -1


def main() -> None:
    out = {"analysts": {}}
    log_dir = os.path.join(TOP_PICKS, "pairwise_logs")
    os.makedirs(log_dir, exist_ok=True)

    for name in ALL_11:
        # Load top-3 for each setting
        picks = {}
        for s in SETTINGS:
            p = os.path.join(TOP_PICKS, _safe(name), f"{s}.json")
            if os.path.exists(p):
                picks[s] = json.load(open(p))["top3"]
        if not picks:
            continue
        avail = list(picks.keys())
        # NxN matrix: pair (A, B) → score of A's top3 vs B's top1
        matrix = {a: {b: None for b in avail} for a in avail}
        for a, b in itertools.combinations(avail, 2):
            if not picks[a] or not picks[b]:
                continue
            log = os.path.join(log_dir, f"{_safe(name)}__{a}__vs__{b}.txt")
            score_ab = b2_pair(name, picks[a], picks[b][0], log)
            log2 = os.path.join(log_dir, f"{_safe(name)}__{b}__vs__{a}.txt")
            score_ba = b2_pair(name, picks[b], picks[a][0], log2)
            matrix[a][b] = score_ab
            matrix[b][a] = score_ba
            print(f"  {name:25s} {a:18s} vs {b:18s}  A→B={score_ab}  B→A={score_ba}")
        # Aggregate stats
        off_diag = [v for a in avail for b in avail if a != b for v in [matrix[a][b]] if v is not None and v >= 0]
        out["analysts"][name] = {
            "matrix": matrix,
            "n_pairs": len(off_diag) // 2,
            "mean_similarity": sum(off_diag) / len(off_diag) if off_diag else None,
            "min_similarity": min(off_diag) if off_diag else None,
            "max_similarity": max(off_diag) if off_diag else None,
            "spread": (max(off_diag) - min(off_diag)) if off_diag else None,
        }
    out_path = os.path.join(TOP_PICKS, "within_twin_pairwise.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {out_path}")
    print(f"\nPer-twin summary (mean / min / max / spread):")
    for name in ALL_11:
        a = out["analysts"].get(name)
        if not a: continue
        print(f"  {name:25s}  mean={a['mean_similarity']:.2f}  min={a['min_similarity']}  max={a['max_similarity']}  spread={a['spread']}")


if __name__ == "__main__":
    main()
