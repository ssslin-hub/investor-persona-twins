"""End-to-end pipeline:

  1. For each recurring analyst (>= MIN_QUESTIONS in training), build the
     extraction prompt from data/analysts.json and call the LLM to produce a
     structured BDE persona (saved to data/personas/<name>.json).

  2. Load the held-out 2026-Q1 management presentation from
     data/analysts_test.json. For each analyst persona, build the simulator
     prompt and call the LLM to produce predicted questions (saved to
     data/predictions/<name>.json).

  3. For each analyst who ALSO appears in the 2026-Q1 test set, build the
     judge prompt comparing predicted vs actual and call the LLM to score
     them (saved to data/scores/<name>.json).

  4. Print an aggregated summary.

Usage:
  python3 src/run_pipeline.py            # live run (needs OPENAI_API_KEY)
  DRY_RUN=1 python3 src/run_pipeline.py  # offline, dumps prompts only
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap

from llm_client import call_llm, parse_json_strict


MIN_QUESTIONS = 5  # only build personas for analysts with >= this many training Qs
MAX_HISTORY_TURNS = 60  # cap question history fed to extractor
MGMT_EXCERPT_CHARS = 1200  # per-turn cap when summarising prior management text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(ROOT, "prompts")
DATA = os.path.join(ROOT, "data")


def load_text(path: str) -> str:
    with open(path) as f:
        return f.read()


def _truncate(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 3].rstrip() + "..."


# Match "Firstname Lastname (Title, Firm):" speaker tags.
_SPEAKER_TAG_RE = re.compile(
    r"^([A-Z][A-Za-z'\.\-]+(?:\s+[A-Z][A-Za-z'\.\-]+)+)\s*\([^)]*\):",
    re.M,
)
# Management voices to exclude from the analyst list (heuristic by first name).
_MGMT_FIRST_NAMES = {
    "jason", "naftali", "michael", "richard", "adam", "operator",
    "scott", "stuart", "yuli", "mary", "harry",
}


def parse_qa_so_far(context: str) -> tuple[list[str], str]:
    """Split context at the [Q&A SO FAR] marker. Returns
    (ordered_unique_analyst_names, truncated_qa_excerpt_last_2000_chars).
    If marker absent, returns ([], "").
    """
    if "[Q&A SO FAR]" not in context:
        return [], ""
    qa = context.split("[Q&A SO FAR]", 1)[1]
    seen: set[str] = set()
    names: list[str] = []
    for m in _SPEAKER_TAG_RE.finditer(qa):
        nm = m.group(1).strip()
        first = nm.split()[0].lower()
        if first in _MGMT_FIRST_NAMES:
            continue
        if nm in seen:
            continue
        seen.add(nm)
        names.append(nm)
    excerpt = qa.strip()
    if len(excerpt) > 2000:
        excerpt = "...(truncated)..." + excerpt[-2000:]
    return names, excerpt


def build_question_history_block(records: list[dict]) -> str:
    """For each (context, question, response) record in the analyst's history,
    produce a compact block that includes:
      - The call quarter
      - A short excerpt of the management presentation portion of the context
        (we strip out the "[Q&A SO FAR]" section to keep things compact)
      - The verbatim question
      - A truncated response
    """
    # If the analyst has very many records, keep the most-recent N to fit token
    # budget.
    if len(records) > MAX_HISTORY_TURNS:
        records = records[-MAX_HISTORY_TURNS:]

    blocks: list[str] = []
    for i, r in enumerate(records, 1):
        ctx = r.get("context", "")
        prior_analysts, qa_excerpt = parse_qa_so_far(ctx)
        position_in_call = len(prior_analysts) + 1
        # Take only the [PRESENTATION] portion of the context, drop Q&A so far.
        pres = ctx
        if "[Q&A SO FAR]" in ctx:
            pres = ctx.split("[Q&A SO FAR]", 1)[0]
        pres = _truncate(pres.replace("[PRESENTATION]\n", "").strip(), MGMT_EXCERPT_CHARS)
        question = r["question"].strip()
        response = _truncate(r.get("response", ""), 500)
        operator_intro = r.get("operator_intro") or ""
        ticker = r.get("ticker", "RCL")
        sector = r.get("sector", "cruise")
        prior_str = ", ".join(prior_analysts) if prior_analysts else "(none — they were first)"
        qa_block = qa_excerpt if qa_excerpt else "(this analyst spoke first)"
        blocks.append(textwrap.dedent(f"""
            --- TURN {i} | CALL: {r['call']} | TICKER: {ticker} | SECTOR: {sector} | FIRM: {r.get('affiliation') or '?'} ---
            [Queue position] This analyst was #{position_in_call} to speak on this call.
            [Analysts who spoke before them on this call]
            {prior_str}

            [Setup: management presentation excerpt]
            {pres}

            [Q&A SO FAR — what prior analysts asked, truncated]
            {qa_block}

            [Operator intro to analyst, if any]
            {_truncate(operator_intro, 250)}

            [Analyst question]
            {question}

            [Management response excerpt]
            {response}
        """).strip())
    return "\n\n".join(blocks)


def _fill(template: str, **kwargs: str) -> str:
    """Replace ``{key}`` placeholders without touching other braces.

    We use ``str.replace`` rather than ``str.format`` because the prompt
    templates contain literal JSON example blocks (with their own braces) that
    we don't want interpreted as placeholders.
    """
    out = template
    for k, v in kwargs.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def build_extraction_prompt(template: str, name: str, analyst: dict) -> str:
    records = analyst["records"]
    calls = sorted({r["call"] for r in records})
    affiliations = analyst.get("affiliations_seen") or []
    aff = affiliations[-1] if affiliations else "(unknown)"
    history_block = build_question_history_block(records)
    return _fill(
        template,
        analyst_name=name,
        affiliation=aff,
        n_questions=str(analyst["n_questions"]),
        calls_covered=", ".join(calls),
        question_history=history_block,
    )


def build_simulator_prompt(template: str, persona: dict, mgmt_pres: str) -> str:
    # Strip the trailing "[Q&A SO FAR]" section: it leaks who's queued up to
    # speak. We only want the model to see management's presentation.
    if "[Q&A SO FAR]" in mgmt_pres:
        mgmt_pres = mgmt_pres.split("[Q&A SO FAR]", 1)[0].rstrip()
    return _fill(
        template,
        persona_json=json.dumps(persona, indent=2),
        management_presentation=mgmt_pres,
    )


def build_judge_prompt(
    template: str,
    name: str,
    predicted: list[dict],
    actual: list[dict],
) -> str:
    predicted_lines = []
    for i, p in enumerate(predicted):
        predicted_lines.append(
            f"[{i}] topic={p.get('topic_label', '?')} :: {p.get('question_text', '').strip()}"
        )
    actual_lines = []
    for i, a in enumerate(actual):
        actual_lines.append(f"[{i}] {a['question'].strip()}")
    return _fill(
        template,
        analyst_name=name,
        predicted_block="\n".join(predicted_lines) or "(none)",
        actual_block="\n".join(actual_lines) or "(none)",
    )


# ---------------------------------------------------------------------------
# Dry-run stubs that produce structurally-valid JSON so downstream steps work.
# ---------------------------------------------------------------------------


def stub_persona(name: str, analyst: dict) -> dict:
    calls = sorted({r["call"] for r in analyst["records"]})
    return {
        "coverage_profile": {
            "firm": (analyst.get("affiliations_seen") or ["(unknown)"])[-1],
            "seniority_signal": f"Stub persona for {name}; n={analyst['n_questions']} prior turns.",
            "sector_lens": "Cruise/leisure analyst.",
            "rhetorical_signature": ["Stub: opens with greeting.", "Stub: asks two-parters."],
        },
        "reasoning_style": {
            "primary_mode": "mixed",
            "follow_up_pattern": "Stub follow-up pattern.",
            "evidence_demanded": "Stub evidence preferences.",
            "anchoring_habits": "Stub anchoring habits.",
        },
        "recurring_concerns": {
            "core_topics": [
                {"topic": "pricing/yield", "what_they_press_on": "stub", "supporting_calls": calls[:3]},
                {"topic": "demand/booking_curve", "what_they_press_on": "stub", "supporting_calls": calls[:3]},
            ],
            "blind_spots": "Stub: unclear.",
            "stance_drift": "Stub: shifted from recovery to growth.",
        },
    }


def stub_predictions(name: str) -> dict:
    return {
        "analyst": name,
        "predicted_questions": [
            {
                "question_text": f"[stub] How are you thinking about yield growth into 2026 given current bookings? — for {name}",
                "topic_label": "pricing/yield",
                "rationale": "Stub rationale.",
            },
            {
                "question_text": f"[stub] Capital return + leverage trajectory question — for {name}",
                "topic_label": "capital_return",
                "rationale": "Stub rationale.",
            },
        ],
    }


def stub_judgment(name: str, actual: list[dict], predicted: list[dict]) -> dict:
    scored = [
        {
            "actual_question": a["question"][:120],
            "actual_topic": "stub_topic",
            "best_predicted_index": 0 if predicted else None,
            "match_level": "miss",
            "reasoning": "Stub.",
        }
        for a in actual
    ]
    return {
        "analyst": name,
        "scored": scored,
        "summary": {
            "n_actual": len(actual),
            "n_exact": 0,
            "n_partial": 0,
            "n_miss": len(actual),
            "hit_rate_exact_or_partial": 0.0,
        },
    }


# ---------------------------------------------------------------------------


def run(
    data_dir: str = DATA,
    extraction_prompt: str = "extract_bde.md",
    simulator_prompt: str = "simulate_questions.md",
    judge_prompt: str = "judge_match.md",
    persona_out_subdir: str = "personas",
    log_out_subdir: str = "prompt_logs",
    skip_simulate_and_judge: bool = False,
) -> dict:
    """Run extract → simulate → judge end-to-end against the dataset at
    ``data_dir`` (which must contain analysts.json and analysts_test.json).
    Returns the aggregate summary dict.
    """
    analysts = json.load(open(os.path.join(data_dir, "analysts.json")))
    test_set = json.load(open(os.path.join(data_dir, "analysts_test.json")))
    mgmt_pres = test_set["management_context"]
    actuals = test_set["per_analyst_actual_questions"]
    from denoise_dataset import clean_actuals
    actuals, _ = clean_actuals(actuals)   # Step 3: denoise actuals before judging

    extraction_tpl = load_text(os.path.join(PROMPTS, extraction_prompt))
    simulator_tpl = load_text(os.path.join(PROMPTS, simulator_prompt)) if not skip_simulate_and_judge else ""
    judge_tpl = load_text(os.path.join(PROMPTS, judge_prompt)) if not skip_simulate_and_judge else ""

    persona_dir = os.path.join(data_dir, persona_out_subdir)
    pred_dir = os.path.join(data_dir, "predictions")
    score_dir = os.path.join(data_dir, "scores")
    log_dir = os.path.join(data_dir, log_out_subdir)
    dirs_to_make = [persona_dir, log_dir]
    if not skip_simulate_and_judge:
        dirs_to_make.extend([pred_dir, score_dir])
    for d in dirs_to_make:
        os.makedirs(d, exist_ok=True)

    # Choose which analysts to build personas for. Filter by min question count
    # (rich-enough history) OR force-include any analyst who shows up in the
    # 2026-Q1 test set (so we cover the comparison cells).
    test_names = set(actuals.keys())
    rich_names = {n for n, a in analysts.items() if a["n_questions"] >= MIN_QUESTIONS}
    targets = sorted(rich_names | (test_names & set(analysts.keys())))

    print(f"# personas to build: {len(targets)}")
    print(f"  rich (>= {MIN_QUESTIONS} qs): {len(rich_names)}")
    print(f"  test-set returning: {len(test_names & set(analysts.keys()))}")
    print(f"  test-set NEW (no training history): {sorted(test_names - set(analysts.keys()))}")

    # ---- Step 1: persona extraction ----
    personas: dict[str, dict] = {}
    for name in targets:
        analyst = analysts[name]
        prompt = build_extraction_prompt(extraction_tpl, name, analyst)
        out = call_llm(
            prompt,
            expect_json=True,
            dry_run_stub=stub_persona(name, analyst),
            log_to=os.path.join(log_dir, f"extract_{name.replace(' ', '_')}.txt"),
        )
        try:
            persona = parse_json_strict(out)
        except Exception as e:  # noqa: BLE001
            print(f"[extract:{name}] JSON parse error: {e}; using stub instead.")
            persona = stub_persona(name, analyst)
        path = os.path.join(persona_dir, f"{name.replace(' ', '_')}.json")
        with open(path, "w") as fp:
            json.dump(persona, fp, indent=2)
        personas[name] = persona
        print(f"  extracted persona: {name} -> {path}")

    if skip_simulate_and_judge:
        print(f"\n[--skip-simulate-and-judge] wrote {len(personas)} personas to {persona_dir}; stopping.")
        return {"personas_written": len(personas), "persona_dir": persona_dir}

    # ---- Step 2: simulator (predicted questions for 2026-Q1) ----
    predictions: dict[str, dict] = {}
    for name, persona in personas.items():
        prompt = build_simulator_prompt(simulator_tpl, persona, mgmt_pres)
        out = call_llm(
            prompt,
            expect_json=True,
            dry_run_stub=stub_predictions(name),
            log_to=os.path.join(log_dir, f"simulate_{name.replace(' ', '_')}.txt"),
        )
        try:
            pred = parse_json_strict(out)
        except Exception as e:  # noqa: BLE001
            print(f"[simulate:{name}] JSON parse error: {e}; using stub instead.")
            pred = stub_predictions(name)
        path = os.path.join(pred_dir, f"{name.replace(' ', '_')}.json")
        with open(path, "w") as fp:
            json.dump(pred, fp, indent=2)
        predictions[name] = pred
        print(f"  predicted questions: {name} -> {path}")

    # ---- Step 3: judge predicted vs actual for returning analysts ----
    judgments: dict[str, dict] = {}
    for name, actual_qs in actuals.items():
        if name not in predictions:
            continue
        pred = predictions[name]["predicted_questions"]
        prompt = build_judge_prompt(judge_tpl, name, pred, actual_qs)
        out = call_llm(
            prompt,
            expect_json=True,
            dry_run_stub=stub_judgment(name, actual_qs, pred),
            log_to=os.path.join(log_dir, f"judge_{name.replace(' ', '_')}.txt"),
        )
        try:
            jd = parse_json_strict(out)
        except Exception as e:  # noqa: BLE001
            print(f"[judge:{name}] JSON parse error: {e}; using stub instead.")
            jd = stub_judgment(name, actual_qs, pred)
        path = os.path.join(score_dir, f"{name.replace(' ', '_')}.json")
        with open(path, "w") as fp:
            json.dump(jd, fp, indent=2)
        judgments[name] = jd

    # ---- Step 4: aggregate summary ----
    print("\n=== AGGREGATE ===")
    total_actual = total_exact = total_partial = total_miss = 0
    print(f"{'analyst':30s} {'n_actual':>8s} {'exact':>6s} {'partial':>8s} {'miss':>5s} {'hit%':>6s}")
    for name in sorted(judgments):
        s = judgments[name]["summary"]
        total_actual += s["n_actual"]
        total_exact += s["n_exact"]
        total_partial += s["n_partial"]
        total_miss += s["n_miss"]
        hit = s["hit_rate_exact_or_partial"]
        print(f"{name:30s} {s['n_actual']:>8d} {s['n_exact']:>6d} {s['n_partial']:>8d} {s['n_miss']:>5d} {hit:>6.2f}")
    agg_hit = (total_exact + total_partial) / total_actual if total_actual else 0.0
    print(f"{'TOTAL':30s} {total_actual:>8d} {total_exact:>6d} {total_partial:>8d} {total_miss:>5d} {agg_hit:>6.2f}")

    summary = {
        "n_actual": total_actual,
        "n_exact": total_exact,
        "n_partial": total_partial,
        "n_miss": total_miss,
        "hit_rate_exact_or_partial": agg_hit,
        "per_analyst": {n: judgments[n]["summary"] for n in judgments},
    }
    with open(os.path.join(data_dir, "aggregate_summary.json"), "w") as fp:
        json.dump(summary, fp, indent=2)
    return summary


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=DATA)
    ap.add_argument("--extraction-prompt", default="extract_bde.md")
    ap.add_argument("--simulator-prompt", default="simulate_questions.md")
    ap.add_argument("--judge-prompt", default="judge_match.md")
    ap.add_argument("--persona-out-subdir", default="personas")
    ap.add_argument("--log-out-subdir", default="prompt_logs")
    ap.add_argument("--skip-simulate-and-judge", action="store_true")
    args = ap.parse_args()
    run(
        data_dir=args.data_dir,
        extraction_prompt=args.extraction_prompt,
        simulator_prompt=args.simulator_prompt,
        judge_prompt=args.judge_prompt,
        persona_out_subdir=args.persona_out_subdir,
        log_out_subdir=args.log_out_subdir,
        skip_simulate_and_judge=args.skip_simulate_and_judge,
    )


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
