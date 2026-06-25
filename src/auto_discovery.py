"""Auto-discovery loop driver.

Subcommands:
  round0                                 — extract+simulate+judge with round-0 prompt
  prepare-meta --t <int>                 — assemble meta_context.md for the sub-agent
  apply-edit --t <int>                   — consume meta_response.json, gate, apply, re-eval
  select-r-star                          — pick winning round, persist
  prepare-variant-b --analyst <name>     — assemble per-analyst meta_context for B
  apply-variant-b --analyst <name> --t   — apply B edit, re-eval analyst's persona
  final-test                             — final TEST eval with chosen personas

Convention: all artifacts under data_auto/round_<t>/ for Variant A and
data_auto/refine_<analyst>/round_<t>/ for Variant B.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import (  # noqa: E402
    build_extraction_prompt, build_simulator_prompt, build_judge_prompt,
    stub_persona, stub_predictions, stub_judgment, load_text,
)

# ---- Constants ----

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
TRAIN_PATH = os.path.join(DATA_AUTO, "train_combined.json")
CAL_PATH = os.path.join(DATA_AUTO, "cal.json")
TEST_PATH = os.path.join(DATA_AUTO, "test.json")
SIMULATOR_PROMPT = os.path.join(PROMPTS, "simulate_questions.md")
JUDGE_PROMPT = os.path.join(PROMPTS, "judge_match.md")
ROUND0_PROMPT = os.path.join(PROMPTS, "extract_bde_round0.md")

CAL_ELIGIBLE = {
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "conor cunningham", "david katz",
    "vince ciepiel", "sharon zackfia", "andrew didora",
}
TEST_RETURNING = {  # the 9 returning TEST analysts (cold-start excluded)
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
}

# Anti-niche denylist seeded from common CAL-quarter topic words.
EVENT_DENYLIST = {
    "mediterranean", "wave season", "perfecta", "trifecta", "icon class",
    "star of the seas", "cococay", "perfect day", "royal beach club",
}

EDIT_BUDGET_TEXT = (
    "May only: add/remove sub-profile fields at Layer 1 (BDE skeleton); "
    "reword Layer 2 evidence-allocation; revise peer-vs-RCL separation rule. "
    "May not: write question templates, opener phrases, analyst names, or "
    "specific CAL/TEST actual wording."
)


# ---- Helpers ----

def _safe_name(s: str) -> str:
    return s.replace(" ", "_")


def _all_4grams(text: str) -> set[tuple[str, ...]]:
    toks = re.findall(r"[A-Za-z0-9']+", text.lower())
    return {tuple(toks[i : i + 4]) for i in range(len(toks) - 3)}


def _ngram_overlap(haystack_text: str, needle_grams: set[tuple[str, ...]]) -> set[tuple[str, ...]]:
    h_grams = _all_4grams(haystack_text)
    return h_grams & needle_grams


def _cal_actual_ngrams() -> set[tuple[str, ...]]:
    cal = json.load(open(CAL_PATH))
    grams: set[tuple[str, ...]] = set()
    for blk in cal["calls"]:
        for _name, actuals in blk["per_analyst_actual_questions"].items():
            for a in actuals:
                grams |= _all_4grams(a["question"])
    return grams


def _test_actual_ngrams() -> set[tuple[str, ...]]:
    t = json.load(open(TEST_PATH))
    grams: set[tuple[str, ...]] = set()
    for _name, actuals in t["per_analyst_actual_questions"].items():
        for a in actuals:
            grams |= _all_4grams(a["question"])
    return grams


# ---- Step: extract personas ----

def extract_personas(prompt_path: str, out_dir: str, targets: set[str]) -> dict[str, dict]:
    os.makedirs(out_dir, exist_ok=True)
    tpl = load_text(prompt_path)
    train = json.load(open(TRAIN_PATH))
    personas: dict[str, dict] = {}
    for name in sorted(targets):
        if name not in train:
            print(f"  ! {name}: not in train, skipping")
            continue
        analyst = train[name]
        if not analyst.get("records"):
            print(f"  ! {name}: 0 train turns, skipping")
            continue
        prompt = build_extraction_prompt(tpl, name, analyst)
        log = os.path.join(out_dir, "logs", f"extract_{_safe_name(name)}.txt")
        out = call_llm(prompt, expect_json=True,
                       dry_run_stub=stub_persona(name, analyst), log_to=log)
        try:
            persona = parse_json_strict(out)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {name}: persona JSON parse failed ({e}); using stub")
            persona = stub_persona(name, analyst)
        path = os.path.join(out_dir, f"{_safe_name(name)}.json")
        with open(path, "w") as f:
            json.dump(persona, f, indent=2)
        personas[name] = persona
        print(f"  extracted persona: {name}")
    return personas


# ---- Step: simulate + judge on CAL ----

def simulate_judge_cal(personas_dir: str, out_dir: str) -> dict:
    """Run simulate + judge for every (analyst, cal-call) combination
    where the analyst has actuals on that call. Returns aggregated CAL score.
    """
    os.makedirs(out_dir, exist_ok=True)
    sim_tpl = load_text(SIMULATOR_PROMPT)
    judge_tpl = load_text(JUDGE_PROMPT)
    cal = json.load(open(CAL_PATH))

    # Load all personas
    personas: dict[str, dict] = {}
    for fn in os.listdir(personas_dir):
        if not fn.endswith(".json"):
            continue
        if fn in ("predictions.json", "scores.json"):
            continue
        name = fn[: -len(".json")].replace("_", " ")
        try:
            personas[name] = json.load(open(os.path.join(personas_dir, fn)))
        except Exception:
            continue

    all_predictions: dict[str, dict] = {}  # key = "<call>::<name>"
    all_scores: dict[str, dict] = {}

    per_analyst_agg: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_actual = total_exact = total_partial = total_miss = 0

    for blk in cal["calls"]:
        call_label = blk["call"]
        mgmt = blk["management_context"]
        for name, actuals in blk["per_analyst_actual_questions"].items():
            if name not in personas:
                # No persona built for this analyst (e.g. benjamin chaiken or
                # analysts outside CAL_ELIGIBLE) — skip silently.
                continue
            persona = personas[name]
            sim_prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
            log = os.path.join(out_dir, "logs",
                                f"sim_{call_label}_{_safe_name(name)}.txt")
            sim_out = call_llm(sim_prompt, expect_json=True,
                                dry_run_stub=stub_predictions(name), log_to=log)
            try:
                pred = parse_json_strict(sim_out)
            except Exception:
                pred = stub_predictions(name)
            all_predictions[f"{call_label}::{name}"] = pred

            judge_prompt = build_judge_prompt(
                judge_tpl, name, pred["predicted_questions"], actuals,
            )
            log = os.path.join(out_dir, "logs",
                                f"judge_{call_label}_{_safe_name(name)}.txt")
            judge_out = call_llm(judge_prompt, expect_json=True,
                                  dry_run_stub=stub_judgment(name, actuals,
                                                               pred["predicted_questions"]),
                                  log_to=log)
            try:
                judgment = parse_json_strict(judge_out)
            except Exception:
                judgment = stub_judgment(name, actuals, pred["predicted_questions"])
            all_scores[f"{call_label}::{name}"] = judgment
            s = judgment["summary"]
            per_analyst_agg[name]["n_actual"] += s["n_actual"]
            per_analyst_agg[name]["n_exact"] += s["n_exact"]
            per_analyst_agg[name]["n_partial"] += s["n_partial"]
            per_analyst_agg[name]["n_miss"] += s["n_miss"]
            total_actual += s["n_actual"]
            total_exact += s["n_exact"]
            total_partial += s["n_partial"]
            total_miss += s["n_miss"]

    with open(os.path.join(out_dir, "predictions.json"), "w") as f:
        json.dump(all_predictions, f, indent=2)
    with open(os.path.join(out_dir, "scores.json"), "w") as f:
        json.dump(all_scores, f, indent=2)

    hit = (total_exact + total_partial) / total_actual if total_actual else 0.0
    summary = {
        "n_actual": total_actual,
        "n_exact": total_exact,
        "n_partial": total_partial,
        "n_miss": total_miss,
        "hit_rate_exact_or_partial": hit,
        "per_analyst": {
            n: {
                **dict(v),
                "hit": (v["n_exact"] + v["n_partial"]) / v["n_actual"] if v["n_actual"] else 0.0,
            }
            for n, v in per_analyst_agg.items()
        },
    }
    with open(os.path.join(out_dir, "cal_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  CAL: n_actual={total_actual} exact={total_exact} partial={total_partial} miss={total_miss} hit={hit:.3f}")
    return summary


# ---- Step: round 0 ----

def cmd_round0() -> None:
    print("=== Variant A — Round 0 ===")
    round_dir = os.path.join(DATA_AUTO, "round_0")
    os.makedirs(round_dir, exist_ok=True)
    personas_dir = os.path.join(round_dir, "personas")
    eval_dir = os.path.join(round_dir, "eval")
    # Snapshot the round-0 prompt
    shutil.copy2(ROUND0_PROMPT, os.path.join(round_dir, "prompt.md"))
    print("Step 1: extract personas")
    extract_personas(ROUND0_PROMPT, personas_dir, CAL_ELIGIBLE | TEST_RETURNING)
    print("Step 2: simulate + judge on CAL")
    summary = simulate_judge_cal(personas_dir, eval_dir)
    # Persist round summary
    round_summary = {
        "t": 0,
        "edit_type": "baseline",
        "rule": "round-0 baseline (peer-aware extract_bde_round0.md)",
        "evidence_count": None,
        "cal_summary": summary,
    }
    with open(os.path.join(round_dir, "round_summary.json"), "w") as f:
        json.dump(round_summary, f, indent=2)
    # Prepare meta_context for round 1 (so the sub-agent can be called next)
    prepare_meta(t_next=1, current_round=0)


# ---- Step: prepare meta_context for sub-agent ----

def prepare_meta(t_next: int, current_round: int) -> None:
    """Assemble meta_context.md for round t_next, using the eval results of
    `current_round`. The sub-agent will be spawned by the orchestrator with
    this file as input.
    """
    print(f"=== Preparing meta_context for round {t_next} ===")
    round_dir = os.path.join(DATA_AUTO, f"round_{t_next}")
    os.makedirs(round_dir, exist_ok=True)

    # Current prompt (the one we'll be revising)
    cur_prompt = open(os.path.join(DATA_AUTO, f"round_{current_round}", "prompt.md")).read()

    # CAL feedback: per-analyst predictions vs actuals + judge reasoning
    cal = json.load(open(CAL_PATH))
    eval_dir = os.path.join(DATA_AUTO, f"round_{current_round}", "eval")
    predictions = json.load(open(os.path.join(eval_dir, "predictions.json")))
    scores = json.load(open(os.path.join(eval_dir, "scores.json")))

    cal_feedback_lines: list[str] = []
    for blk in cal["calls"]:
        cl = blk["call"]
        cal_feedback_lines.append(f"\n## CAL call: {cl}")
        for name, actuals in blk["per_analyst_actual_questions"].items():
            if name not in CAL_ELIGIBLE:
                continue
            key = f"{cl}::{name}"
            pred = predictions.get(key, {}).get("predicted_questions", [])
            jud = scores.get(key, {}).get("scored", [])
            cal_feedback_lines.append(f"\n### Analyst: {name}")
            cal_feedback_lines.append("Predicted (under current persona):")
            for i, p in enumerate(pred):
                cal_feedback_lines.append(
                    f"  [{i}] topic={p.get('topic_label','?')} :: "
                    f"{p.get('question_text','').strip()[:240]}"
                )
            cal_feedback_lines.append("Actual question(s) and judge verdict:")
            for k, a in enumerate(actuals):
                actual_q = a["question"].strip()[:240]
                verdict = jud[k] if k < len(jud) else {}
                ml = verdict.get("match_level", "?")
                rsn = verdict.get("reasoning", "(no reasoning)")[:300]
                cal_feedback_lines.append(
                    f"  ACTUAL[{k}] ({ml}): {actual_q}\n    judge: {rsn}"
                )

    cal_feedback_text = "\n".join(cal_feedback_lines)

    # Diff log: accumulated from prior accepted rounds
    diff_entries: list[str] = []
    for tt in range(1, t_next):
        rd = os.path.join(DATA_AUTO, f"round_{tt}", "round_summary.json")
        if os.path.exists(rd):
            s = json.load(open(rd))
            if s.get("edit_type") in (None, "baseline", "noop", "rejected"):
                continue
            diff_entries.append(
                f"  ROUND {tt}: rule=\"{s.get('rule','?')}\" "
                f"evidence_count={s.get('evidence_count','?')} "
                f"edit_type={s.get('edit_type','?')}\n    diff: {s.get('diff_summary','?')[:300]}"
            )
    diff_log_text = "\n".join(diff_entries) if diff_entries else "  (no accepted edits yet)"

    # Substitute into meta_reasoning_a.md
    meta_tpl = load_text(os.path.join(PROMPTS, "meta_reasoning_a.md"))
    meta_text = (meta_tpl
                 .replace("{current_prompt}", cur_prompt)
                 .replace("{cal_feedback}", cal_feedback_text)
                 .replace("{diff_log}", diff_log_text)
                 .replace("{edit_budget}", EDIT_BUDGET_TEXT))

    meta_path = os.path.join(round_dir, "meta_context.md")
    with open(meta_path, "w") as f:
        f.write(meta_text)
    print(f"  wrote {meta_path}")
    print(f"  Next: sub-agent reads this and writes JSON to {round_dir}/meta_response.json")


# ---- Step: apply edit ----

def apply_edit(t: int) -> None:
    """Consume data_auto/round_<t>/meta_response.json, gate, apply (or reject),
    re-run extract+simulate+judge on CAL, persist."""
    print(f"=== Variant A — Round {t}: applying edit ===")
    round_dir = os.path.join(DATA_AUTO, f"round_{t}")
    resp_path = os.path.join(round_dir, "meta_response.json")
    if not os.path.exists(resp_path):
        raise FileNotFoundError(f"missing {resp_path} — sub-agent must produce this first")
    resp = json.load(open(resp_path))

    # Gates
    rejected_reason = _gate_variant_a(resp, t)
    prev_round_dir = os.path.join(DATA_AUTO, f"round_{t-1}")
    if rejected_reason:
        print(f"  REJECTED: {rejected_reason}; reusing round {t-1} prompt")
        # Copy prior prompt forward, mark this round as a no-op
        shutil.copy2(os.path.join(prev_round_dir, "prompt.md"),
                     os.path.join(round_dir, "prompt.md"))
        # We still re-extract+simulate+judge to keep per-round artifacts in
        # sync? Or skip and just inherit prior summary? Skip re-eval to save
        # API calls. Just record the rejection.
        cal_summary = json.load(open(os.path.join(prev_round_dir, "eval", "cal_summary.json")))
        round_summary = {
            "t": t,
            "edit_type": "rejected",
            "rule": resp.get("rule"),
            "evidence_count": resp.get("evidence_count"),
            "diff_summary": resp.get("diff_summary"),
            "rejection_reason": rejected_reason,
            "cal_summary": cal_summary,
        }
        with open(os.path.join(round_dir, "round_summary.json"), "w") as f:
            json.dump(round_summary, f, indent=2)
        # Also snapshot personas from prior round
        prev_personas = os.path.join(prev_round_dir, "personas")
        new_personas = os.path.join(round_dir, "personas")
        if os.path.exists(prev_personas) and not os.path.exists(new_personas):
            shutil.copytree(prev_personas, new_personas)
        if t < 2:
            prepare_meta(t_next=t + 1, current_round=t)
        return

    # Accepted — write new prompt and re-run pipeline
    new_prompt = resp["new_prompt"]
    prompt_path = os.path.join(round_dir, "prompt.md")
    with open(prompt_path, "w") as f:
        f.write(new_prompt)
    print(f"  accepted edit; wrote new prompt to {prompt_path}")

    personas_dir = os.path.join(round_dir, "personas")
    eval_dir = os.path.join(round_dir, "eval")
    print("  re-extracting personas")
    extract_personas(prompt_path, personas_dir, CAL_ELIGIBLE | TEST_RETURNING)
    print("  re-evaluating on CAL")
    cal_summary = simulate_judge_cal(personas_dir, eval_dir)
    round_summary = {
        "t": t,
        "edit_type": resp.get("edit_type"),
        "rule": resp.get("rule"),
        "evidence_count": resp.get("evidence_count"),
        "diff_summary": resp.get("diff_summary"),
        "what_attended": resp.get("what_attended"),
        "how_reasoned": resp.get("how_reasoned"),
        "cal_summary": cal_summary,
    }
    with open(os.path.join(round_dir, "round_summary.json"), "w") as f:
        json.dump(round_summary, f, indent=2)
    # Prepare next meta_context if not last round
    if t < 4:
        prepare_meta(t_next=t + 1, current_round=t)


def _gate_variant_a(resp: dict, t: int) -> str | None:
    """Return rejection reason string, or None if accepted."""
    if resp.get("edit_type") == "noop":
        return "edit_type=noop"
    if resp.get("evidence_count", 0) < 2:
        return f"evidence_count={resp.get('evidence_count')} < 2 (anti-niche)"
    prev_prompt = open(os.path.join(DATA_AUTO, f"round_{t-1}", "prompt.md")).read()
    new_prompt = resp.get("new_prompt", "")
    if not new_prompt:
        return "new_prompt empty"
    if len(new_prompt) > 1.25 * len(prev_prompt):
        return f"new_prompt length {len(new_prompt)} > 1.25x previous {len(prev_prompt)} (anti-bloat)"
    # Leakage check: 4-gram from CAL or TEST actuals
    cal_grams = _cal_actual_ngrams()
    test_grams = _test_actual_ngrams()
    new_prompt_grams = _all_4grams(new_prompt)
    cal_hits = new_prompt_grams & cal_grams
    test_hits = new_prompt_grams & test_grams
    if cal_hits:
        return f"new_prompt leaks {len(cal_hits)} CAL 4-grams (e.g. {next(iter(cal_hits))})"
    if test_hits:
        return f"new_prompt leaks {len(test_hits)} TEST 4-grams (e.g. {next(iter(test_hits))})"
    # Anti-niche denylist
    low_text = (resp.get("diff_summary", "") + " " + new_prompt).lower()
    for term in EVENT_DENYLIST:
        if term in low_text:
            # Allow if it's also called out as generalized (heuristic — look for nearby "generaliz" or "category" or "lens")
            window_starts = [m.start() for m in re.finditer(re.escape(term), low_text)]
            generalized = False
            for s in window_starts:
                window = low_text[max(0, s - 200) : s + 200]
                if any(k in window for k in ("generaliz", "category", "broader", "abstract", "lens-level", "trait-level")):
                    generalized = True
                    break
            if not generalized:
                return f"contains over-niche term '{term}' without generalization"
    return None


# ---- Step: select r-star ----

def cmd_select_r_star() -> None:
    summaries = []
    for t in range(0, 5):
        path = os.path.join(DATA_AUTO, f"round_{t}", "round_summary.json")
        if os.path.exists(path):
            s = json.load(open(path))
            summaries.append((t, s["cal_summary"]["hit_rate_exact_or_partial"], s["cal_summary"]))
    if not summaries:
        raise RuntimeError("no rounds found")
    # Earliest-round tie-break
    best_hit = max(s[1] for s in summaries)
    r_star = min(t for t, hit, _ in summaries if hit >= best_hit)
    out = {
        "r_star": r_star,
        "per_round_hit": {str(t): hit for t, hit, _ in summaries},
    }
    with open(os.path.join(DATA_AUTO, "r_star.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"  r* = round {r_star} (cal_hit = {best_hit:.3f})")
    print(f"  per-round CAL hit: {out['per_round_hit']}")


# ---- Step: prepare Variant B meta_context ----

def cmd_prepare_variant_b(analyst: str, t: int = 1) -> None:
    """Build the per-analyst meta_context for Variant B round t.

    t=1: persona + predictions/judges come from Variant A r*.
    t>1: persona comes from refine_<analyst>/round_{t-1}/persona.json and
         predictions/judges come from refine_<analyst>/round_{t-1}/round_summary.json.
    """
    print(f"=== Variant B — preparing context for {analyst} (round {t}) ===")
    refine_dir = os.path.join(DATA_AUTO, "refine_" + _safe_name(analyst))

    if t == 1:
        r_star = json.load(open(os.path.join(DATA_AUTO, "r_star.json")))["r_star"]
        src_personas_dir = os.path.join(DATA_AUTO, f"round_{r_star}", "personas")
        src_eval_dir = os.path.join(DATA_AUTO, f"round_{r_star}", "eval")
        persona_path = os.path.join(src_personas_dir, f"{_safe_name(analyst)}.json")
        if not os.path.exists(persona_path):
            raise FileNotFoundError(f"no persona for {analyst} at {persona_path}")
        persona = json.load(open(persona_path))
        predictions = json.load(open(os.path.join(src_eval_dir, "predictions.json")))
        scores = json.load(open(os.path.join(src_eval_dir, "scores.json")))
    else:
        # Source = prior B round
        prev_dir = os.path.join(refine_dir, f"round_{t-1}")
        persona_path = os.path.join(prev_dir, "persona.json")
        if not os.path.exists(persona_path):
            raise FileNotFoundError(f"no prior B persona at {persona_path}")
        persona = json.load(open(persona_path))
        # Prior round's predictions/scores are nested per-call in the summary
        prev_summary = json.load(open(os.path.join(prev_dir, "round_summary.json")))
        predictions = {}
        scores = {}
        for cl, pred in (prev_summary.get("predictions") or {}).items():
            predictions[f"{cl}::{analyst}"] = pred
        for cl, jud in (prev_summary.get("scores") or {}).items():
            scores[f"{cl}::{analyst}"] = jud

    cal = json.load(open(CAL_PATH))
    actuals: list[dict] = []
    for blk in cal["calls"]:
        for name, qs in blk["per_analyst_actual_questions"].items():
            if name == analyst:
                actuals.extend(qs)
    if not actuals:
        raise RuntimeError(f"{analyst} has no CAL actuals; cannot run Variant B")

    cur_preds: list[dict] = []
    judge_per_actual: list[dict] = []
    for blk in cal["calls"]:
        cl = blk["call"]
        if analyst in blk["per_analyst_actual_questions"]:
            key = f"{cl}::{analyst}"
            p = predictions.get(key, {}).get("predicted_questions", [])
            j = scores.get(key, {}).get("scored", [])
            cur_preds.extend(p)
            judge_per_actual.extend(j)

    forbidden = set()
    for a in actuals:
        forbidden |= _all_4grams(a["question"])
    forbidden_text = "\n".join(" ".join(g) for g in list(forbidden)[:300])

    actuals_text = "\n".join(
        f"  CAL {a['call']}: {a['question'].strip()[:600]}" for a in actuals
    )
    preds_text = "\n".join(
        f"  [{i}] topic={p.get('topic_label','?')} :: {p.get('question_text','').strip()[:400]}"
        for i, p in enumerate(cur_preds)
    )
    judge_text = "\n".join(
        f"  ACTUAL[{k}] ({j.get('match_level','?')}): {j.get('reasoning','')[:400]}"
        for k, j in enumerate(judge_per_actual)
    )

    meta_tpl = load_text(os.path.join(PROMPTS, "meta_reasoning_b.md"))
    meta_text = (meta_tpl
                 .replace("{analyst_name}", analyst)
                 .replace("{current_persona}", json.dumps(persona, indent=2))
                 .replace("{cal_actuals}", actuals_text)
                 .replace("{current_predictions}", preds_text)
                 .replace("{judge_reasoning}", judge_text)
                 .replace("{forbidden_ngrams}", forbidden_text))

    out_dir = os.path.join(refine_dir, f"round_{t}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "meta_context.md")
    with open(out_path, "w") as f:
        f.write(meta_text)
    # Snapshot starting persona at round_0 for inspection (only first time)
    if t == 1:
        r0 = os.path.join(refine_dir, "round_0")
        os.makedirs(r0, exist_ok=True)
        shutil.copy2(persona_path, os.path.join(r0, "persona.json"))
    print(f"  wrote {out_path}")


def cmd_apply_variant_b(analyst: str, t: int) -> None:
    """Consume refine_<analyst>/round_<t>/meta_response.json, gate, apply,
    re-evaluate on CAL for that analyst, persist."""
    print(f"=== Variant B — applying for {analyst}, round {t} ===")
    refine_dir = os.path.join(DATA_AUTO, "refine_" + _safe_name(analyst))
    round_dir = os.path.join(refine_dir, f"round_{t}")
    resp_path = os.path.join(round_dir, "meta_response.json")
    if not os.path.exists(resp_path):
        raise FileNotFoundError(f"missing {resp_path}")
    resp = json.load(open(resp_path))

    prev_persona_path = os.path.join(refine_dir, f"round_{t-1}", "persona.json")
    prev_persona = json.load(open(prev_persona_path))

    # Gates
    reason = _gate_variant_b(resp, prev_persona, analyst)
    if reason:
        print(f"  REJECTED: {reason}; reusing round {t-1} persona")
        shutil.copy2(prev_persona_path, os.path.join(round_dir, "persona.json"))
        with open(os.path.join(round_dir, "round_summary.json"), "w") as f:
            json.dump({"t": t, "edit_type": "rejected", "rejection_reason": reason}, f, indent=2)
        return

    new_persona = resp["new_persona"]
    persona_path = os.path.join(round_dir, "persona.json")
    with open(persona_path, "w") as f:
        json.dump(new_persona, f, indent=2)
    # Re-simulate + judge for this analyst on CAL
    sim_tpl = load_text(SIMULATOR_PROMPT)
    judge_tpl = load_text(JUDGE_PROMPT)
    cal = json.load(open(CAL_PATH))
    per_analyst_summary: dict[str, Any] = {
        "n_actual": 0, "n_exact": 0, "n_partial": 0, "n_miss": 0,
    }
    pred_log: dict[str, Any] = {}
    score_log: dict[str, Any] = {}
    for blk in cal["calls"]:
        cl = blk["call"]
        if analyst not in blk["per_analyst_actual_questions"]:
            continue
        actuals = blk["per_analyst_actual_questions"][analyst]
        mgmt = blk["management_context"]
        sim_prompt = build_simulator_prompt(sim_tpl, new_persona, mgmt)
        sim_out = call_llm(sim_prompt, expect_json=True,
                           dry_run_stub=stub_predictions(analyst),
                           log_to=os.path.join(round_dir, "logs", f"sim_{cl}.txt"))
        try:
            pred = parse_json_strict(sim_out)
        except Exception:
            pred = stub_predictions(analyst)
        judge_prompt = build_judge_prompt(judge_tpl, analyst, pred["predicted_questions"], actuals)
        judge_out = call_llm(judge_prompt, expect_json=True,
                             dry_run_stub=stub_judgment(analyst, actuals, pred["predicted_questions"]),
                             log_to=os.path.join(round_dir, "logs", f"judge_{cl}.txt"))
        try:
            judgment = parse_json_strict(judge_out)
        except Exception:
            judgment = stub_judgment(analyst, actuals, pred["predicted_questions"])
        s = judgment["summary"]
        per_analyst_summary["n_actual"] += s["n_actual"]
        per_analyst_summary["n_exact"] += s["n_exact"]
        per_analyst_summary["n_partial"] += s["n_partial"]
        per_analyst_summary["n_miss"] += s["n_miss"]
        pred_log[cl] = pred
        score_log[cl] = judgment

    per_analyst_summary["hit"] = (
        (per_analyst_summary["n_exact"] + per_analyst_summary["n_partial"])
        / per_analyst_summary["n_actual"]
        if per_analyst_summary["n_actual"] else 0.0
    )
    with open(os.path.join(round_dir, "round_summary.json"), "w") as f:
        json.dump({
            "t": t,
            "edit_type": resp.get("trait_edit"),
            "rule": resp.get("rule"),
            "what_attended": resp.get("what_attended"),
            "how_reasoned": resp.get("how_reasoned"),
            "predictions": pred_log,
            "scores": score_log,
            "summary": per_analyst_summary,
        }, f, indent=2)
    print(f"  round {t} CAL: actual={per_analyst_summary['n_actual']} "
          f"exact={per_analyst_summary['n_exact']} partial={per_analyst_summary['n_partial']} "
          f"miss={per_analyst_summary['n_miss']} hit={per_analyst_summary['hit']:.3f}")


_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
    "with", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "can", "shall", "must", "i", "you", "he", "she", "it",
    "we", "they", "me", "him", "her", "us", "them", "my", "your", "his",
    "its", "our", "their", "this", "that", "these", "those", "at", "by",
    "from", "up", "about", "into", "over", "after", "again", "out", "if",
    "then", "so", "than", "as", "now", "just", "very", "too", "any", "some",
    "all", "no", "not", "only", "yes", "ok", "okay", "thanks", "thank",
    "great", "got", "hey", "hi", "follow", "question", "quick", "good",
    "much", "well", "right", "sure",
}


def _content_grams(grams: set[tuple[str, ...]]) -> set[tuple[str, ...]]:
    """Drop n-grams that are mostly stopwords (≤1 content token)."""
    out = set()
    for g in grams:
        content = sum(1 for t in g if t not in _STOPWORDS)
        if content >= 2:
            out.add(g)
    return out


def _gate_variant_b(resp: dict, prev_persona: dict, analyst: str) -> str | None:
    if resp.get("trait_edit") == "noop":
        return "trait_edit=noop"
    new_persona = resp.get("new_persona")
    if not new_persona:
        return "new_persona empty"
    prev_text = json.dumps(prev_persona)
    new_text = json.dumps(new_persona)
    if len(new_text) > 1.30 * len(prev_text):
        return f"new_persona length {len(new_text)} > 1.30x previous {len(prev_text)}"
    # Forbidden CONTENT 4-grams from this analyst's CAL actuals
    cal = json.load(open(CAL_PATH))
    forbidden: set[tuple[str, ...]] = set()
    for blk in cal["calls"]:
        for a in blk["per_analyst_actual_questions"].get(analyst, []):
            forbidden |= _all_4grams(a["question"])
    forbidden = _content_grams(forbidden)
    new_grams = _content_grams(_all_4grams(new_text))
    hits = new_grams & forbidden
    if hits:
        return f"new_persona leaks {len(hits)} CAL-actual content 4-grams (e.g. {next(iter(hits))})"
    test_grams = _content_grams(_test_actual_ngrams())
    test_hits = new_grams & test_grams
    if test_hits:
        return f"new_persona leaks {len(test_hits)} TEST content 4-grams (e.g. {next(iter(test_hits))})"
    # Anti-niche denylist — only flag if term is NEWLY introduced (not already
    # present in prev_persona). Variant B may legitimately keep existing
    # topic mentions like "Royal Beach Club" in recurring_concerns.core_topics.
    low_new = new_text.lower()
    low_prev = prev_text.lower()
    for term in EVENT_DENYLIST:
        if term in low_new and term not in low_prev:
            return f"newly introduces over-niche term '{term}'"
    return None


# ---- Step: final TEST ----

def cmd_final_test() -> None:
    """Apply selected personas to TEST (2026-Q1) and score on returning
    analysts only. For analysts who went through Variant B, use the
    best-selection-rule persona; for others, use Variant A r*'s persona.
    """
    print("=== Final TEST evaluation ===")
    r_star = json.load(open(os.path.join(DATA_AUTO, "r_star.json")))["r_star"]
    a_personas_dir = os.path.join(DATA_AUTO, f"round_{r_star}", "personas")

    # Choose final persona per analyst: keep A r* as the floor; swap to a B
    # round ONLY if its CAL hit is STRICTLY greater than A r*'s CAL hit on
    # the same analyst.
    final_personas: dict[str, dict] = {}
    persona_choice: dict[str, str] = {}
    a_cal_summary = json.load(open(os.path.join(
        DATA_AUTO, f"round_{r_star}", "eval", "cal_summary.json")))
    for name in sorted(TEST_RETURNING):
        path_a = os.path.join(a_personas_dir, f"{_safe_name(name)}.json")
        if not os.path.exists(path_a):
            print(f"  ! {name}: no Variant A persona, skipping")
            continue
        final_personas[name] = json.load(open(path_a))
        persona_choice[name] = f"A_r{r_star}"
        a_hit = a_cal_summary["per_analyst"].get(name, {}).get("hit", 0.0)
        refine_dir = os.path.join(DATA_AUTO, "refine_" + _safe_name(name))
        if not os.path.isdir(refine_dir):
            continue
        best_b_hit = a_hit
        best_b_path = None
        best_b_round = None
        for tt in range(1, 4):
            rd = os.path.join(refine_dir, f"round_{tt}")
            sp = os.path.join(rd, "persona.json")
            summary_path = os.path.join(rd, "round_summary.json")
            if not os.path.exists(sp) or not os.path.exists(summary_path):
                continue
            s = json.load(open(summary_path))
            if s.get("edit_type") == "rejected":
                continue
            h = s.get("summary", {}).get("hit", -1.0)
            if h > best_b_hit:
                best_b_hit = h
                best_b_path = sp
                best_b_round = tt
        if best_b_path is not None:
            final_personas[name] = json.load(open(best_b_path))
            persona_choice[name] = f"B_round_{best_b_round} ({a_hit:.2f}->{best_b_hit:.2f})"
    print("  persona choice per analyst:")
    for n, c in sorted(persona_choice.items()):
        print(f"    {n:25s} -> {c}")

    # Persist the final persona set
    out_dir = os.path.join(DATA_AUTO, "final_personas")
    os.makedirs(out_dir, exist_ok=True)
    for n, p in final_personas.items():
        with open(os.path.join(out_dir, f"{_safe_name(n)}.json"), "w") as f:
            json.dump(p, f, indent=2)

    # Simulate + judge on TEST
    sim_tpl = load_text(SIMULATOR_PROMPT)
    judge_tpl = load_text(JUDGE_PROMPT)
    test = json.load(open(TEST_PATH))
    mgmt = test["management_context"]
    actuals_by_name = test["per_analyst_actual_questions"]

    per_analyst: dict[str, dict] = {}
    total_actual = total_exact = total_partial = total_miss = 0
    eval_log_dir = os.path.join(DATA_AUTO, "final_eval", "logs")
    os.makedirs(eval_log_dir, exist_ok=True)
    for name in sorted(TEST_RETURNING):
        if name not in actuals_by_name or name not in final_personas:
            continue
        actuals = actuals_by_name[name]
        persona = final_personas[name]
        sim_prompt = build_simulator_prompt(sim_tpl, persona, mgmt)
        sim_out = call_llm(sim_prompt, expect_json=True,
                           dry_run_stub=stub_predictions(name),
                           log_to=os.path.join(eval_log_dir, f"sim_{_safe_name(name)}.txt"))
        try:
            pred = parse_json_strict(sim_out)
        except Exception:
            pred = stub_predictions(name)
        judge_prompt = build_judge_prompt(judge_tpl, name, pred["predicted_questions"], actuals)
        judge_out = call_llm(judge_prompt, expect_json=True,
                             dry_run_stub=stub_judgment(name, actuals, pred["predicted_questions"]),
                             log_to=os.path.join(eval_log_dir, f"judge_{_safe_name(name)}.txt"))
        try:
            judgment = parse_json_strict(judge_out)
        except Exception:
            judgment = stub_judgment(name, actuals, pred["predicted_questions"])
        s = judgment["summary"]
        per_analyst[name] = {
            "n_actual": s["n_actual"],
            "n_exact": s["n_exact"],
            "n_partial": s["n_partial"],
            "n_miss": s["n_miss"],
            "hit": (s["n_exact"] + s["n_partial"]) / s["n_actual"] if s["n_actual"] else 0.0,
            "predictions": pred,
            "judgment": judgment,
        }
        total_actual += s["n_actual"]
        total_exact += s["n_exact"]
        total_partial += s["n_partial"]
        total_miss += s["n_miss"]

    hit = (total_exact + total_partial) / total_actual if total_actual else 0.0
    summary = {
        "n_returning_analysts_scored": len(per_analyst),
        "n_actual": total_actual,
        "n_exact": total_exact,
        "n_partial": total_partial,
        "n_miss": total_miss,
        "hit_rate_exact_or_partial": hit,
        "per_analyst": per_analyst,
        "v1_baseline": 0.500,
    }
    with open(os.path.join(DATA_AUTO, "final_eval", "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n=== FINAL TEST RESULT ===")
    print(f"  N returning scored: {len(per_analyst)}")
    print(f"  n_actual={total_actual} exact={total_exact} partial={total_partial} miss={total_miss}")
    print(f"  test_hit = {hit:.3f}  (V1 baseline = 0.500)")


# ---- main ----

def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("round0")
    p = sub.add_parser("prepare-meta")
    p.add_argument("--t", type=int, required=True)
    p.add_argument("--from-round", type=int, default=None)
    p = sub.add_parser("apply-edit")
    p.add_argument("--t", type=int, required=True)
    sub.add_parser("select-r-star")
    p = sub.add_parser("prepare-variant-b")
    p.add_argument("--analyst", required=True)
    p.add_argument("--t", type=int, default=1)
    p = sub.add_parser("apply-variant-b")
    p.add_argument("--analyst", required=True)
    p.add_argument("--t", type=int, required=True)
    sub.add_parser("final-test")
    args = ap.parse_args()

    if args.cmd == "round0":
        cmd_round0()
    elif args.cmd == "prepare-meta":
        cur = args.from_round if args.from_round is not None else (args.t - 1)
        prepare_meta(t_next=args.t, current_round=cur)
    elif args.cmd == "apply-edit":
        apply_edit(args.t)
    elif args.cmd == "select-r-star":
        cmd_select_r_star()
    elif args.cmd == "prepare-variant-b":
        cmd_prepare_variant_b(args.analyst, t=args.t)
    elif args.cmd == "apply-variant-b":
        cmd_apply_variant_b(args.analyst, args.t)
    elif args.cmd == "final-test":
        cmd_final_test()


if __name__ == "__main__":
    main()
