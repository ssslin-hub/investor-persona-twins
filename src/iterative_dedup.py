"""Recursive top-down halving anchor dedup.

Round r:
  - Operates within ranks [0, m_r) per analyst, where m_0 = source_K and m_{r+1} = m_r // 2
  - Anchors = ranks [0, m_r // 2) per analyst
  - Candidates = ranks [m_r // 2, m_r) per analyst
  - Single B4 anchor-match call → drop candidates marked useful=True
  - Stop if drop_rate < threshold or m_r // 2 < 1

Final filtered pool = source pool minus globally-dropped candidates.

Usage:
  python3 src/iterative_dedup.py --source-K 18 --threshold 0.10 --model gpt-5
"""
from __future__ import annotations
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict
from run_pipeline import load_text

DATA_AUTO = os.path.join(ROOT, "data_auto")
B4_TPL = load_text(os.path.join(ROOT, "prompts", "b4_eval.md"))


def safe(s): return re.sub(r"[^a-z0-9]+", "_", s.lower())


def build_prompt(anchors_flat, candidates_flat):
    return (B4_TPL
            .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(candidates_flat, indent=2))
            .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(anchors_flat, indent=2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-K", type=int, required=True)
    ap.add_argument("--threshold", type=float, default=0.10)
    ap.add_argument("--model", default="gpt-5")
    args = ap.parse_args()

    src_dir = os.path.join(DATA_AUTO, f"final_eval_{args.source_K}q_v5")
    summary = json.load(open(os.path.join(src_dir, "summary.json")))

    out_dir = os.path.join(src_dir, "iterative_dedup")
    os.makedirs(out_dir, exist_ok=True)

    # Per-analyst: list of (rank, question_dict)
    per_analyst_ranks = {}
    for name, cell in summary["per_analyst"].items():
        preds = (cell.get("predictions") or {}).get("predicted_questions", [])
        per_analyst_ranks[name] = list(enumerate(preds))

    # cid format: <analyst_safe>-r<rank>
    def cid(name, rank): return f"{safe(name)}-r{rank}"

    dropped_globally = set()
    trace_rounds = []

    m = args.source_K
    round_num = 0

    while True:
        round_num += 1
        L_anchors = m // 2
        L_candidates = m - L_anchors
        if L_anchors < 1 or L_candidates < 1:
            print(f"Stop: L_anchors={L_anchors} L_candidates={L_candidates} too small")
            break

        # Build anchors (ranks [0, L_anchors)) and candidates (ranks [L_anchors, m))
        # Exclude any already-dropped candidates
        anchors_flat = []
        candidates_flat = []
        for name, ranks in per_analyst_ranks.items():
            for rank, q in ranks:
                if rank >= m: continue  # outside current window
                c = cid(name, rank)
                if c in dropped_globally: continue  # already dropped, skip
                qtext = q.get("question_text", "")
                if rank < L_anchors:
                    anchors_flat.append({"actual_id": c, "question": qtext})
                else:  # rank in [L_anchors, m)
                    candidates_flat.append({"candidate_id": c, "question": qtext})

        if not anchors_flat or not candidates_flat:
            print(f"  Round {round_num}: no anchors or candidates after exclusions; stop")
            break

        round_dir = os.path.join(out_dir, f"round_{round_num}")
        os.makedirs(round_dir, exist_ok=True)
        prompt = build_prompt(anchors_flat, candidates_flat)
        with open(os.path.join(round_dir, "prompt.txt"), "w") as f: f.write(prompt)

        print(f"  Round {round_num}: m={m}, L_anchors={L_anchors}, L_cands={L_candidates}, "
              f"|anchors|={len(anchors_flat)}, |candidates|={len(candidates_flat)}; calling {args.model}...")
        out = call_llm(prompt, expect_json=True, model=args.model,
                       log_to=os.path.join(round_dir, "response.txt"))
        b4 = parse_json_strict(out)

        drops_this_round = set()
        drop_details = []
        for pp in b4.get("predicted_precision", []):
            c = pp.get("candidate_id")
            if c and pp.get("useful"):
                drops_this_round.add(c)
                drop_details.append({
                    "candidate_id": c,
                    "covered_by_anchor": pp.get("best_actual_id"),
                    "score": pp.get("match_score_0_to_4"),
                    "reasoning": (pp.get("reasoning") or "")[:200],
                })

        drop_rate = len(drops_this_round) / len(candidates_flat)
        with open(os.path.join(round_dir, "drops.json"), "w") as f:
            json.dump({"drops": drop_details, "drop_rate": drop_rate,
                      "anchors_count": len(anchors_flat),
                      "candidates_count": len(candidates_flat)}, f, indent=2)

        trace_rounds.append({
            "round": round_num,
            "m": m,
            "L_anchors": L_anchors,
            "L_candidates": L_candidates,
            "anchors_count": len(anchors_flat),
            "candidates_count": len(candidates_flat),
            "drop_count": len(drops_this_round),
            "drop_rate": drop_rate,
        })
        dropped_globally |= drops_this_round
        print(f"    → drops={len(drops_this_round)}/{len(candidates_flat)} ({100*drop_rate:.1f}%)")

        if drop_rate < args.threshold:
            print(f"  Drop rate {drop_rate:.3f} < threshold {args.threshold}; stop")
            trace_rounds[-1]["stopped_at_threshold"] = True
            break
        m = L_anchors

    # Build final filtered pool
    filtered_per_analyst = {}
    total_kept = 0; per_analyst_counts = []
    for name, ranks in per_analyst_ranks.items():
        kept = [q for rank, q in ranks if cid(name, rank) not in dropped_globally]
        filtered_per_analyst[name] = {
            "n_actual": summary["per_analyst"][name].get("n_actual"),
            "predictions": {"analyst": name, "predicted_questions": kept},
            "persona_source": summary["per_analyst"][name].get("persona_source", "v5"),
        }
        total_kept += len(kept); per_analyst_counts.append(len(kept))

    filtered = {
        "source_K": args.source_K,
        "method": f"iterative_recursive_halving (threshold={args.threshold}, model={args.model})",
        "source": "v5",
        "n_analysts_scored": len(filtered_per_analyst),
        "total_predicted_questions": total_kept,
        "per_analyst": filtered_per_analyst,
    }
    with open(os.path.join(out_dir, "filtered_pool.json"), "w") as f:
        json.dump(filtered, f, indent=2)

    trace = {
        "source_K": args.source_K,
        "threshold": args.threshold,
        "model": args.model,
        "rounds_run": len(trace_rounds),
        "rounds": trace_rounds,
        "total_dropped_globally": len(dropped_globally),
        "total_kept": total_kept,
        "per_analyst_kept_count": {n: c for n, c in zip(per_analyst_ranks, per_analyst_counts)},
    }
    with open(os.path.join(out_dir, "trace.json"), "w") as f:
        json.dump(trace, f, indent=2)

    counts = sorted(per_analyst_counts)
    n = len(counts)
    print(f"\n=== Done ===")
    print(f"Rounds run: {len(trace_rounds)}")
    print(f"Total dropped: {len(dropped_globally)} / {args.source_K * 11}")
    print(f"Total kept: {total_kept}")
    print(f"Per-analyst kept: min={counts[0]}, median={counts[n//2]}, max={counts[-1]}")


if __name__ == "__main__":
    main()
