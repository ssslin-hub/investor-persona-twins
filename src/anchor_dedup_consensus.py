"""Multi-run consensus anchor-dedup. Each (K, L) combo: run B4 anchor-match
N times with gpt-5-mini, take majority vote on each candidate's drop decision.

This addresses the single-run noise that caused the K=18 L=3 outlier (97% drop)
in the original single-shot dedup.

Usage:
  python3 src/anchor_dedup_consensus.py --source-K 18 --L 3 --n-runs 3
"""
from __future__ import annotations
import argparse, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict
from run_pipeline import load_text

DATA_AUTO = os.path.join(ROOT, "data_auto")
B4_TPL = load_text(os.path.join(ROOT, "prompts", "b4_eval.md"))


def safe(s): return re.sub(r"[^a-z0-9]+", "_", s.lower())


def build_prompt(anchors_flat, remaining_flat):
    return (B4_TPL
            .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(remaining_flat, indent=2))
            .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(anchors_flat, indent=2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-K", type=int, required=True, choices=[10, 18])
    ap.add_argument("--L", type=int, required=True)
    ap.add_argument("--n-runs", type=int, default=3)
    ap.add_argument("--model", default="gpt-5-mini")
    args = ap.parse_args()

    source_dir = os.path.join(DATA_AUTO, f"final_eval_{args.source_K}q_v5")
    summary = json.load(open(os.path.join(source_dir, "summary.json")))

    out_dir = os.path.join(source_dir, "anchor_dedup", f"L{args.L}")
    os.makedirs(out_dir, exist_ok=True)
    log_dir = os.path.join(out_dir, "consensus_logs"); os.makedirs(log_dir, exist_ok=True)

    # Build anchors + remaining
    anchors_flat = []
    remaining_flat = []
    per_analyst_split = {}
    for name, cell in summary["per_analyst"].items():
        preds = (cell.get("predictions") or {}).get("predicted_questions", [])
        anchors = preds[:args.L]
        remaining = preds[args.L:]
        per_analyst_split[name] = {"anchors": anchors, "remaining": remaining}
        sname = safe(name)
        for i, q in enumerate(anchors):
            anchors_flat.append({"actual_id": f"{sname}-anchor-{i}", "question": q.get("question_text", "")})
        for i, q in enumerate(remaining):
            remaining_flat.append({"candidate_id": f"{sname}-rem-{i}", "question": q.get("question_text", "")})

    print(f"K={args.source_K} L={args.L}: anchors={len(anchors_flat)} remaining={len(remaining_flat)}")
    prompt = build_prompt(anchors_flat, remaining_flat)

    # Run B4 N times
    per_run_drops = []
    for run_i in range(1, args.n_runs+1):
        log_path = os.path.join(log_dir, f"run_{run_i}.txt")
        print(f"  run {run_i}/{args.n_runs}: calling {args.model}...")
        try:
            out = call_llm(prompt, expect_json=True, model=args.model, log_to=log_path)
            b4 = parse_json_strict(out)
        except Exception as e:
            print(f"    ERR: {e}"); continue
        drops_this_run = set()
        cid_to_info = {}
        for pp in b4.get("predicted_precision", []):
            cid = pp.get("candidate_id")
            if cid and pp.get("useful"):
                drops_this_run.add(cid)
                cid_to_info[cid] = {
                    "best_actual_id": pp.get("best_actual_id"),
                    "score": pp.get("match_score_0_to_4"),
                    "reasoning": (pp.get("reasoning") or "")[:200],
                }
        per_run_drops.append((drops_this_run, cid_to_info))
        print(f"    → {len(drops_this_run)} useful (drop candidates)")

    if not per_run_drops:
        print("All runs failed; abort.")
        sys.exit(1)

    # Majority vote across runs: drop if ≥ ceil(n/2) runs mark useful
    threshold = (len(per_run_drops) + 1) // 2  # majority
    all_cids = set()
    for d, _ in per_run_drops: all_cids.update(d)
    cid_vote_count = Counter()
    for d, _ in per_run_drops:
        for cid in d:
            cid_vote_count[cid] += 1
    drops_majority = {cid for cid, c in cid_vote_count.items() if c >= threshold}
    print(f"  Consensus: drop if ≥{threshold}/{len(per_run_drops)} runs mark useful")
    print(f"  Total drops by majority: {len(drops_majority)} / {len(remaining_flat)}")

    # Build filtered pool (anchors + retained remaining)
    filtered_per_analyst = {}
    total_kept = 0; per_analyst_counts = []
    for name, sp in per_analyst_split.items():
        sname = safe(name)
        kept = list(sp["anchors"])
        for i, q in enumerate(sp["remaining"]):
            cid = f"{sname}-rem-{i}"
            if cid not in drops_majority:
                kept.append(q)
        filtered_per_analyst[name] = {
            "n_actual": summary["per_analyst"][name].get("n_actual"),
            "predictions": {"analyst": name, "predicted_questions": kept},
            "persona_source": summary["per_analyst"][name].get("persona_source", "v5"),
        }
        total_kept += len(kept); per_analyst_counts.append(len(kept))

    filtered = {
        "K_source": args.source_K, "L_anchors_per_analyst": args.L,
        "source": "v5", "n_analysts_scored": len(filtered_per_analyst),
        "total_predicted_questions": total_kept, "per_analyst": filtered_per_analyst,
        "dedup_method": f"{args.model} × {len(per_run_drops)}-run consensus (≥{threshold} votes)",
    }
    with open(os.path.join(out_dir, "filtered_pool.json"), "w") as f:
        json.dump(filtered, f, indent=2)

    # Trace with per-run + consensus info
    drops_with_info = []
    for cid in sorted(drops_majority):
        votes = cid_vote_count[cid]
        # Get reasoning from first run that marked it
        info = None
        for d, ci in per_run_drops:
            if cid in d: info = ci[cid]; break
        drops_with_info.append({
            "candidate_id": cid, "votes": votes,
            "covered_by_anchor_id": info["best_actual_id"] if info else None,
            "match_score_0_to_4": info["score"] if info else None,
            "reasoning": info["reasoning"] if info else "",
        })

    trace = {
        "K_source": args.source_K, "L": args.L, "n_runs": len(per_run_drops),
        "majority_threshold": threshold,
        "n_anchors": len(anchors_flat), "n_remaining": len(remaining_flat),
        "n_dropped": len(drops_majority), "total_kept": total_kept,
        "per_run_drop_counts": [len(d) for d, _ in per_run_drops],
        "per_analyst_kept_count": dict(zip(per_analyst_split.keys(), per_analyst_counts)),
        "drops": drops_with_info,
    }
    with open(os.path.join(out_dir, "dedup_trace.json"), "w") as f:
        json.dump(trace, f, indent=2)

    counts = sorted(per_analyst_counts)
    n = len(counts)
    print(f"  Final: kept={total_kept}, per-analyst min/med/max = {counts[0]}/{counts[n//2]}/{counts[-1]}")
    print(f"  Per-run drop counts: {[len(d) for d, _ in per_run_drops]}")


if __name__ == "__main__":
    main()
