"""Roll up parsed transcripts into per-analyst (context, question, response) tuples.

Stages:
1. Load all parsed/*.json files.
2. Drop UI-chrome 'speakers' (no affiliation + suspicious name) and merge
   common first-name variants (Steve/Steven, Ben/Benjamin).
3. For each analyst question, build the *preceding context* = everything said
   in the call up to (but not including) that question. This mirrors the
   (context, question) tuple in the persona-paper setup.
4. Group by canonical analyst name and write one record per analyst with the
   chronological list of (call, context, question, response, affiliation) tuples.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict


# Speakers that are page chrome rather than real people.
NOISE_NAMES = {
    "install the app",
    "market newsletter",
    "dark",
    "compare",
    "royal caribbean cruises ltd. (rcl)",
    "earnings call",
    "speaker 16",
    "speaker 15",
    "speaker 14",
    "speaker 13",
    "speaker 12",
    "speaker 11",
    "speaker 10",
}

# Map first-name variants → canonical full name. Built from inspection of
# the appearance counts (Steve↔Steven, Ben↔Benjamin).
NAME_CANONICAL = {
    "steve wieczynski": "steven wieczynski",
    "ben chaiken": "benjamin chaiken",
    "vince ciepel": "vince ciepiel",
    "connor cunningham": "conor cunningham",
}


def canon_name(raw: str) -> str:
    n = re.sub(r"\s+", " ", raw).strip().lower()
    return NAME_CANONICAL.get(n, n)


def is_noise(name_lc: str, affiliation: str | None) -> bool:
    if name_lc in NOISE_NAMES:
        return True
    # Heuristic: real analysts always have an affiliation; chrome doesn't.
    if not affiliation:
        # But some early calls have analysts without affiliation lines — only
        # treat as noise if the name is suspicious (1 word or known chrome-like).
        words = name_lc.split()
        if len(words) == 1:
            return True
        # 2-word names with no affiliation: keep them (rare but real).
    return False


def display_name(canonical_lc: str) -> str:
    """Title-case the canonical lower-case name back to a display string."""
    return " ".join(w.capitalize() for w in canonical_lc.split())


def build_context_for_question(rec: dict, q_index_in_qa: int) -> str:
    """Concatenate all speaker turns up to (but not including) the analyst's
    question turn at q_index_in_qa within the QA list.

    Context format:
        [PRESENTATION]
        Speaker (Title): <text>
        ...
        [Q&A SO FAR]
        Speaker (Title): <text>
        ...
    """
    parts: list[str] = ["[PRESENTATION]"]
    for t in rec["presentation_turns"]:
        aff = f" ({t['affiliation']})" if t.get("affiliation") else ""
        parts.append(f"{t['speaker']}{aff}: {t['text']}")
    parts.append("\n[Q&A SO FAR]")
    for t in rec["qa_turns"][:q_index_in_qa]:
        aff = f" ({t['affiliation']})" if t.get("affiliation") else ""
        parts.append(f"{t['speaker']}{aff}: {t['text']}")
    return "\n".join(parts)


def find_question_turn_index(rec: dict, analyst_question_idx: int) -> int:
    """The QA list has all speaker turns; the analyst_questions list is a
    subset (only analyst turns). Map analyst_questions[i] back to its index in
    qa_turns by matching on speaker + question text.
    """
    target = rec["analyst_questions"][analyst_question_idx]
    for j, t in enumerate(rec["qa_turns"]):
        if t["speaker"] == target["analyst"] and t["text"] == target["question"]:
            return j
    raise ValueError(f"Couldn't relocate question {analyst_question_idx} in qa_turns")


def main(
    parsed_dir: str,
    out_path: str,
    train_only: bool = True,
    held_out_call: str | None = None,
) -> None:
    """Build the (training, held-out) split.

    ``held_out_call`` is a stem like "2025-q4" or "2026-q1". Everything up to
    (but not including) that call is training; that single call is held out as
    the evaluation cell. If None, defaults to the last call alphabetically.
    """
    files = sorted(
        f for f in os.listdir(parsed_dir)
        if f.endswith(".json") and not f.startswith("_")
    )
    if held_out_call is None:
        train_files = files[:-1]
        test_files = files[-1:]
    else:
        held_idx = next(
            (i for i, f in enumerate(files) if f.startswith(held_out_call)),
            None,
        )
        if held_idx is None:
            raise ValueError(f"held_out_call={held_out_call!r} not found in parsed dir")
        train_files = files[:held_idx]
        test_files = [files[held_idx]]

    by_analyst: dict[str, list[dict]] = defaultdict(list)
    skipped_noise = 0
    kept = 0

    for f in train_files:
        rec = json.load(open(os.path.join(parsed_dir, f)))
        for i, q in enumerate(rec["analyst_questions"]):
            name_lc = canon_name(q["analyst"])
            aff = q.get("affiliation")
            if is_noise(name_lc, aff):
                skipped_noise += 1
                continue
            kept += 1
            j = find_question_turn_index(rec, i)
            ctx = build_context_for_question(rec, j)
            by_analyst[name_lc].append({
                "call": f"{rec['year']}-Q{rec['quarter']}",
                "year": rec["year"],
                "quarter": rec["quarter"],
                "affiliation": aff,
                "operator_intro": q.get("operator_intro"),
                "context": ctx,
                "question": q["question"],
                "response": q.get("response", ""),
            })

    print(f"Kept {kept} questions across {len(by_analyst)} analysts; dropped {skipped_noise} noise turns.")

    # Sort each analyst's records chronologically.
    out: dict[str, dict] = {}
    for name_lc, recs in by_analyst.items():
        recs.sort(key=lambda r: (r["year"], r["quarter"]))
        affiliations = sorted({r["affiliation"] for r in recs if r["affiliation"]})
        out[name_lc] = {
            "display_name": display_name(name_lc),
            "n_questions": len(recs),
            "n_calls": len({r["call"] for r in recs}),
            "affiliations_seen": affiliations,
            "records": recs,
        }

    # Sort analysts by question count descending.
    ordered = dict(sorted(out.items(), key=lambda kv: -kv[1]["n_questions"]))
    with open(out_path, "w") as fp:
        json.dump(ordered, fp, indent=2)
    print(f"Wrote {out_path}")

    # Also build the test cell: parse 2026-Q1, gather (context, question)
    # tuples per analyst, but DO NOT include them in training.
    test_out_path = out_path.replace(".json", "_test.json")
    test_records: dict[str, list[dict]] = defaultdict(list)
    for f in test_files:
        rec = json.load(open(os.path.join(parsed_dir, f)))
        for i, q in enumerate(rec["analyst_questions"]):
            name_lc = canon_name(q["analyst"])
            aff = q.get("affiliation")
            if is_noise(name_lc, aff):
                continue
            j = find_question_turn_index(rec, i)
            ctx = build_context_for_question(rec, j)
            test_records[name_lc].append({
                "call": f"{rec['year']}-Q{rec['quarter']}",
                "year": rec["year"],
                "quarter": rec["quarter"],
                "affiliation": aff,
                "operator_intro": q.get("operator_intro"),
                "context": ctx,
                "question": q["question"],
                "response": q.get("response", ""),
            })
    # Also pull the full management-presentation context (everything up to the
    # FIRST analyst question of the test call); we'll feed this to the
    # simulator as the "what management said" context, separate from any
    # later analyst Q&A.
    test_rec = json.load(open(os.path.join(parsed_dir, test_files[0])))
    if test_rec["analyst_questions"]:
        first_q_j = find_question_turn_index(test_rec, 0)
        management_only_ctx = build_context_for_question(test_rec, first_q_j)
    else:
        management_only_ctx = ""
    with open(test_out_path, "w") as fp:
        json.dump({
            "call": f"{test_rec['year']}-Q{test_rec['quarter']}",
            "management_context": management_only_ctx,
            "per_analyst_actual_questions": dict(test_records),
        }, fp, indent=2)
    print(f"Wrote {test_out_path}")
    from denoise_dataset import denoise_test_file
    denoise_test_file(test_out_path)   # keep rebuilt eval data denoised


if __name__ == "__main__":
    import argparse

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--held-out", default=None,
        help="Call to hold out (e.g. '2026-q1' or '2025-q4'). Defaults to last call.",
    )
    ap.add_argument(
        "--out-dir", default=os.path.join(root, "data"),
        help="Output directory for analysts.json and analysts_test.json.",
    )
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    main(
        os.path.join(root, "parsed"),
        os.path.join(args.out_dir, "analysts.json"),
        held_out_call=args.held_out,
    )
