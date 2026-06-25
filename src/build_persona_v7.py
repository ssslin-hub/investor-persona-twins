"""Phase D — Persona v7 builder (RCL).

v7 = v6's distinctive prose fields + 3 new structured predictive fields, with
the SHARED core-metric listing removed (it now lives in the company layer).

Per analyst with >= MIN_QUESTIONS TRAIN questions:
  1. probe_type_profile — trigger-type distribution + population lift + primary
     (raw and by-lift) + trajectory_length  (src/probe_tagger.py).
  2. topic_emphasis — TRAIN topic frequencies + population lift (the tilt, not a
     re-listing of every metric).
  3. signature_questions — <=3 topics recurring in >=40% of the analyst's calls
     AND distinctive (low cross-analyst share), with a representative snippet.
  4. Carry coverage_profile, reasoning_style, queue_behavior,
     cross_analyst_reactivity, engages_assets, engages_themes from personas_v6.
  5. distinctive_concerns — v5 recurring_concerns.core_topics minus the shared
     core metrics; + blind_spots + stance_drift.
  6. covers_companies: ["RCL"]  (person-keyed; multi-company ready).

Cold-start analysts (in the 2026-Q1 test set but < MIN_QUESTIONS TRAIN turns)
fall back to data/personas_v7/_fallback.json (population probe profile + uniform
topic emphasis).

The prose-condensation step routes through llm_client.call_llm with a DRY_RUN
stub that carries the v6 prose verbatim (no API cost under DRY_RUN=1).

Usage:
  DRY_RUN=1 python3 src/build_persona_v7.py        # deterministic, no API
  python3 src/build_persona_v7.py --dry            # build + print, no write
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from probe_tagger import profile_questions, tag_question, strip_greeting, TRIGGER_TYPES  # noqa: E402
from llm_client import call_llm, parse_json_strict  # noqa: E402

DATA = os.path.join(ROOT, "data")
V6_DIR = os.path.join(DATA, "personas_v6")
V5_DIR = os.path.join(DATA, "personas_v5")
V7_DIR = os.path.join(DATA, "personas_v7")
ANALYSTS = os.path.join(DATA, "analysts.json")
TEST = os.path.join(DATA, "analysts_test.json")

MIN_QUESTIONS = 5

# Topic taxonomy (shared themes/metrics). Multi-label per question is fine.
TOPIC_CUES: dict[str, list[str]] = {
    "yield": ["net yield", "yields", "yield", "pricing", "per diem", "ticket", "rate"],
    "cost_ncc": ["ncc", "net cruise cost", "cost", "dry dock", "dry-dock", "expense", "sg&a"],
    "capacity": ["capacity", "apcd", "load factor", "occupancy", "berth", "deployment"],
    "bookings": ["booking", "booked", "book position", "wave", "close-in", "forward book"],
    "fuel": ["fuel", "bunker", "hedge", "hedged"],
    "capital_return": ["buyback", "repurchase", "dividend", "leverage", "balance sheet",
                        "capital allocation", "investment grade", "debt", "roic"],
    "guidance_targets": ["guidance", "guide", "trifecta", "perfecta", "target", "eps",
                         "full year", "full-year", "outlook"],
    "destinations": ["cococay", "perfect day", "beach club", "paradise island", "cozumel",
                     "mexico", "private destination", "island", "hideaway"],
    "consumer_macro": ["consumer", "macro", "economy", "recession", "spending",
                       "discretionary", "value gap"],
    "loyalty": ["loyalty", "crown", "cardholder", "credit card", "royal one", "member"],
    "new_ships": ["icon", "star class", "utopia", "legend", "new hardware", "newbuild",
                  "new ship", "ship delivery"],
}

# Shared core metrics every analyst lists because they are the company model.
# These are MOVED OUT of the persona (kept only as a topic_emphasis weight).
SHARED_CORE_TOKENS = ["yield", "cost", "ncc", "capacity", "booking", "fuel",
                      "capital", "guidance", "eps", "margin", "occupancy"]


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def topic_tags(q: str) -> set[str]:
    low = strip_greeting(q).lower()
    return {t for t, cues in TOPIC_CUES.items() if any(c in low for c in cues)}


def topic_profile(questions: list[str]) -> dict[str, float]:
    counts = {t: 0 for t in TOPIC_CUES}
    for q in questions:
        for t in topic_tags(q):
            counts[t] += 1
    total = sum(counts.values())
    return {t: (counts[t] / total if total else 0.0) for t in TOPIC_CUES}


def lift(dist: dict[str, float], pop: dict[str, float]) -> dict[str, float]:
    return {t: (round(dist[t] / pop[t], 3) if pop.get(t) else 0.0) for t in dist}


# ---------------------------------------------------------------------------
def build_populations(analysts: dict) -> tuple[dict, dict]:
    """Average probe + topic distributions over analysts with >= MIN_QUESTIONS."""
    probe_dists, topic_dists = [], []
    for rec in analysts.values():
        if rec["n_questions"] < MIN_QUESTIONS:
            continue
        qs = [r["question"] for r in rec["records"]]
        probe_dists.append(profile_questions(qs)["distribution"])
        topic_dists.append(topic_profile(qs))
    n = len(probe_dists) or 1
    pop_probe = {t: sum(d[t] for d in probe_dists) / n for t in TRIGGER_TYPES}
    pop_topic = {t: sum(d[t] for d in topic_dists) / n for t in TOPIC_CUES}
    return pop_probe, pop_topic


def signature_questions(concerns: dict) -> list[dict]:
    """The <=3 persona-unique recurring asks. Sourced from the analyst's v5
    distinctive (non-shared) concerns — these are already "recurring AND not the
    shared company model" (e.g. Boss vacation-market share, Farley ECA
    financing). Ranked by share_of_calls; require recurrence (>= 0.3)."""
    topics = concerns.get("topics") or []
    ranked = sorted(
        (t for t in topics if (t.get("share_of_calls") or 0) >= 0.3),
        key=lambda t: -(t.get("share_of_calls") or 0),
    )
    out = []
    for t in ranked[:3]:
        out.append({
            "topic": t.get("topic"),
            "fires_in_share_of_calls": round(t.get("share_of_calls") or 0, 2),
            "what_they_press_on": t.get("what_they_press_on"),
        })
    return out


def distinctive_concerns(v5: dict | None) -> dict:
    """Keep v5 recurring_concerns.core_topics that are NOT shared core metrics;
    carry blind_spots + stance_drift."""
    out = {"topics": [], "blind_spots": None, "stance_drift": None}
    if not v5:
        return out
    rc = v5.get("recurring_concerns") or {}
    for ct in rc.get("core_topics", []) or []:
        label = (ct.get("topic") or "").lower()
        if any(tok in label for tok in SHARED_CORE_TOKENS):
            continue  # shared → lives in company layer / topic_emphasis
        out["topics"].append({
            "topic": ct.get("topic"),
            "what_they_press_on": ct.get("what_they_press_on"),
            "share_of_calls": ct.get("share_of_calls"),
        })
    out["blind_spots"] = rc.get("blind_spots")
    out["stance_drift"] = rc.get("stance_drift")
    return out


PROSE_STUB_FIELDS = ["coverage_profile", "reasoning_style", "queue_behavior",
                     "cross_analyst_reactivity", "engages_assets", "engages_themes",
                     "framing_overrides_by_theme", "blind_spots", "stance_drift"]


def carry_prose(name: str, v6: dict | None, log_dir: str) -> dict:
    """Condense v6 prose via the LLM; under DRY_RUN the stub returns v6 verbatim."""
    if not v6:
        return {}
    stub = {k: v6.get(k) for k in PROSE_STUB_FIELDS if k in v6}
    prompt = (
        f"Condense the following v6 persona prose for analyst {name} into the same "
        f"fields, preserving all distinctive, voice-bearing detail but trimming "
        f"redundancy. Keep field names identical. Output strict JSON.\n\n"
        f"{json.dumps(stub, indent=2)}"
    )
    out = call_llm(prompt, expect_json=True, dry_run_stub=stub,
                   log_to=os.path.join(log_dir, f"prose_{slugify(name)}.txt"))
    try:
        return parse_json_strict(out)
    except Exception:
        return stub


def build_persona(name: str, rec: dict, analysts: dict, pop_probe: dict,
                  pop_topic: dict, log_dir: str) -> dict:
    qs = [r["question"] for r in rec["records"]]
    probe = profile_questions(qs)
    probe["lift_vs_population"] = lift(probe["distribution"], pop_probe)
    # If nothing tagged, the profile is degenerate — don't invent a primary.
    if probe["primary"] is None or sum(probe["lift_vs_population"].values()) == 0:
        probe["primary_by_lift"] = None
        probe["low_signal"] = True
    else:
        probe["primary_by_lift"] = max(probe["lift_vs_population"],
                                       key=probe["lift_vs_population"].get)

    tprof = topic_profile(qs)
    topic_emphasis = {
        "distribution": {t: round(v, 4) for t, v in tprof.items()},
        "lift_vs_population": lift(tprof, pop_topic),
    }

    v6_path = os.path.join(V6_DIR, f"{slugify(name)}.json")
    v5_path = os.path.join(V5_DIR, f"{slugify(name)}.json")
    v6 = json.load(open(v6_path)) if os.path.exists(v6_path) else None
    v5 = json.load(open(v5_path)) if os.path.exists(v5_path) else None

    prose = carry_prose(name, v6, log_dir)
    concerns = distinctive_concerns(v5)

    persona = {
        "analyst_name": name,
        "covers_companies": ["RCL"],
        "probe_type_profile": probe,
        "topic_emphasis": topic_emphasis,
        "signature_questions": signature_questions(concerns),
        "distinctive_concerns": concerns,
        # carried/condensed prose
        "coverage_profile": prose.get("coverage_profile"),
        "reasoning_style": prose.get("reasoning_style"),
        "queue_behavior": prose.get("queue_behavior"),
        "cross_analyst_reactivity": prose.get("cross_analyst_reactivity"),
        "engages_assets": prose.get("engages_assets", []),
        "engages_themes": prose.get("engages_themes", []),
        "framing_overrides_by_theme": prose.get("framing_overrides_by_theme", {}),
        "_built_from": "v7: company-layer split + probe/topic structure + v6 prose",
        "_train_calls": sorted({r["call"] for r in rec["records"]}),
        "_n_train_questions": rec["n_questions"],
    }
    return persona


def build_fallback(pop_probe: dict, pop_topic: dict) -> dict:
    return {
        "analyst_name": "_fallback",
        "covers_companies": ["RCL"],
        "probe_type_profile": {
            "distribution": {t: round(pop_probe[t], 4) for t in TRIGGER_TYPES},
            "lift_vs_population": {t: 1.0 for t in TRIGGER_TYPES},
            "primary": max(pop_probe, key=pop_probe.get),
            "primary_by_lift": None,
            "trajectory_length": 2.0,
            "trajectory_label": "medium",
        },
        "topic_emphasis": {
            "distribution": {t: round(1.0 / len(TOPIC_CUES), 4) for t in TOPIC_CUES},
            "lift_vs_population": {t: 1.0 for t in TOPIC_CUES},
        },
        "signature_questions": [],
        "distinctive_concerns": {"topics": [], "blind_spots": None, "stance_drift": None},
        "coverage_profile": None,
        "reasoning_style": None,
        "_built_from": "v7 fallback: population-average probe + uniform topic emphasis",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    analysts = json.load(open(ANALYSTS))
    test = json.load(open(TEST))
    test_names = set(test["per_analyst_actual_questions"].keys())

    pop_probe, pop_topic = build_populations(analysts)

    os.makedirs(V7_DIR, exist_ok=True)
    log_dir = os.path.join(DATA, "prompt_logs")
    os.makedirs(log_dir, exist_ok=True)

    targets = sorted(n for n, r in analysts.items() if r["n_questions"] >= MIN_QUESTIONS)
    cold = sorted(test_names - set(targets))

    built = 0
    example_persona = None
    for name in targets:
        persona = build_persona(name, analysts[name], analysts, pop_probe, pop_topic, log_dir)
        path = os.path.join(V7_DIR, f"{slugify(name)}.json")
        if not args.dry:
            with open(path, "w") as fp:
                json.dump(persona, fp, indent=2)
        built += 1
        if name == "steven wieczynski":
            example_persona = persona
        pl = persona["probe_type_profile"]
        print(f"  {name:22s} probe_primary={str(pl['primary']):12s} "
              f"by_lift={str(pl['primary_by_lift']):12s} sig={len(persona['signature_questions'])}")

    fb = build_fallback(pop_probe, pop_topic)
    if not args.dry:
        with open(os.path.join(V7_DIR, "_fallback.json"), "w") as fp:
            json.dump(fb, fp, indent=2)

    # Schema-example file (Wieczynski) at repo root, per spec.
    if example_persona and not args.dry:
        with open(os.path.join(ROOT, "personas_v7_schema_example.json"), "w") as fp:
            json.dump(example_persona, fp, indent=2)

    print(f"\nbuilt {built} personas + _fallback.json -> {V7_DIR}")
    print(f"cold-start (use _fallback): {cold}")
    if args.dry:
        print("[--dry] not writing files")


if __name__ == "__main__":
    main()
