"""Anchor-based cross-twin dedup of v5 K=10/K=18 candidate pools.

Algorithm:
  1. Pick source pool (v5 K=10 or K=18 single sim summary.json).
  2. For each analyst: keep top-L candidates as ANCHORS, rest as REMAINING.
  3. Single B4 call with anchors-as-actuals, remaining-as-predictions.
     B4 returns predicted_precision[] flagging which remaining candidates
     are "useful" (covered by an anchor with score≥3). Drop those.
  4. Write filtered pool in summary.json shape (consumable by eval scripts).

Usage:
  python3 src/anchor_dedup.py --source-K 10 --L 3
  python3 src/anchor_dedup.py --source-K 18 --L 4
"""
from __future__ import annotations
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import load_text  # noqa: E402

DATA_AUTO = os.path.join(ROOT, "data_auto")
B4_TPL = load_text(os.path.join(ROOT, "prompts", "b4_eval.md"))


def safe(s): return re.sub(r"[^a-z0-9]+", "_", s.lower())


def build_b4_anchor_match_prompt(anchors_flat, remaining_flat):
    """anchors_flat = list of {actual_id, question}; remaining_flat = list of {candidate_id, question}.
    The B4 prompt treats anchors as the 'actuals' and remaining as the 'predictions'.
    We then read predicted_precision[] to decide which remaining to drop.
    """
    return (B4_TPL
            .replace("{{PREDICTED_QUESTIONS_JSON}}", json.dumps(remaining_flat, indent=2))
            .replace("{{ACTUAL_QUESTIONS_JSON}}", json.dumps(anchors_flat, indent=2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-K", type=int, required=True, choices=[10, 18])
    ap.add_argument("--L", type=int, required=True)
    ap.add_argument("--model", default="gpt-5")
    args = ap.parse_args()

    source_dir = os.path.join(DATA_AUTO, f"final_eval_{args.source_K}q_v5")
    summary = json.load(open(os.path.join(source_dir, "summary.json")))

    out_dir = os.path.join(source_dir, "anchor_dedup", f"L{args.L}")
    os.makedirs(out_dir, exist_ok=True)
    log_dir = os.path.join(out_dir, "logs"); os.makedirs(log_dir, exist_ok=True)

    # Build anchors + remaining, per analyst
    anchors_flat = []
    remaining_flat = []
    per_analyst_split = {}  # name → {"anchors": [...], "remaining": [...]}
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

    print(f"Source: v5 K={args.source_K}, L={args.L}")
    print(f"  anchors: {len(anchors_flat)}; remaining: {len(remaining_flat)}")

    # Call B4 once
    prompt = build_b4_anchor_match_prompt(anchors_flat, remaining_flat)
    with open(os.path.join(log_dir, "b4_anchor_match_prompt.txt"), "w") as f:
        f.write(prompt)
    print(f"  Calling {args.model} (B4 anchor-match)...")
    out = call_llm(prompt, expect_json=True, log_to=os.path.join(log_dir, "b4_anchor_match_resp.txt"))
    b4 = parse_json_strict(out)

    # Build drop set
    drop_cids = set()
    cid_to_anchor = {}
    cid_to_score = {}
    cid_to_reason = {}
    for pp in b4.get("predicted_precision", []):
        cid = pp.get("candidate_id")
        if cid and pp.get("useful"):
            drop_cids.add(cid)
            cid_to_anchor[cid] = pp.get("best_actual_id")
            cid_to_score[cid] = pp.get("match_score_0_to_4")
            cid_to_reason[cid] = pp.get("reasoning", "")

    # Build filtered per_analyst (anchors + retained remaining)
    filtered_per_analyst = {}
    total_kept = 0
    per_analyst_counts = []
    for name, sp in per_analyst_split.items():
        sname = safe(name)
        kept = list(sp["anchors"])  # all L anchors kept
        for i, q in enumerate(sp["remaining"]):
            cid = f"{sname}-rem-{i}"
            if cid not in drop_cids:
                kept.append(q)
        filtered_per_analyst[name] = {
            "n_actual": summary["per_analyst"][name].get("n_actual"),
            "predictions": {"analyst": name, "predicted_questions": kept},
            "persona_source": summary["per_analyst"][name].get("persona_source", "v5"),
        }
        total_kept += len(kept)
        per_analyst_counts.append(len(kept))

    filtered = {
        "K_source": args.source_K,
        "L_anchors_per_analyst": args.L,
        "source": "v5",
        "n_analysts_scored": len(filtered_per_analyst),
        "total_predicted_questions": total_kept,
        "per_analyst": filtered_per_analyst,
    }
    with open(os.path.join(out_dir, "filtered_pool.json"), "w") as f:
        json.dump(filtered, f, indent=2)

    # Dedup trace
    trace = {
        "K_source": args.source_K,
        "L": args.L,
        "n_anchors": len(anchors_flat),
        "n_remaining": len(remaining_flat),
        "n_dropped": len(drop_cids),
        "n_kept_remaining": len(remaining_flat) - len(drop_cids),
        "total_kept": total_kept,
        "per_analyst_kept_count": dict(zip(per_analyst_split.keys(), per_analyst_counts)),
        "drops": [
            {"candidate_id": cid,
             "covered_by_anchor_id": cid_to_anchor[cid],
             "match_score_0_to_4": cid_to_score[cid],
             "reasoning": cid_to_reason[cid][:300]}
            for cid in sorted(drop_cids)
        ],
    }
    with open(os.path.join(out_dir, "dedup_trace.json"), "w") as f:
        json.dump(trace, f, indent=2)

    print(f"  Dropped {len(drop_cids)}/{len(remaining_flat)} remaining ({100*len(drop_cids)/max(1,len(remaining_flat)):.0f}%)")
    print(f"  Total kept = {total_kept} (was {args.source_K * 11})")
    print(f"  Per-analyst: min={min(per_analyst_counts)}, median={sorted(per_analyst_counts)[len(per_analyst_counts)//2]}, max={max(per_analyst_counts)}")
    print(f"Wrote {out_dir}/filtered_pool.json + dedup_trace.json")


if __name__ == "__main__":
    main()
