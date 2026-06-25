"""Phase E — Two-stage v7 question generator (RCL).

Stage 1 (salience, deterministic): assemble candidate HOOKS from the company
layer for the target quarter — metrics that MOVED (deltas_by_transition), assets
whose status CHANGED (asset status_delta), and management's notable_claims — then
re-rank/mask by the analyst's topic_emphasis lift.

Stage 2 (style, LLM): render the v7 prompt with the top-K hooks +
probe_type_profile + form + signature_questions + prior-call anchors, and ask the
model to phrase question(s) in the analyst's voice and probe style; cap the
generic "give me bps" move unless the analyst's UNQUANTIFIED weight is high.
Routes through llm_client.call_llm, so DRY_RUN=1 returns a deterministic stub
(no API). Output is the {predicted, actual} raw_pool.json shape the existing
b2/b4 scorers consume.

--company-only runs the §4a ablation: uniform topic mask + neutral probe profile,
no per-analyst persona.

Usage:
  DRY_RUN=1 python3 src/simulate_v7.py --k 1
  DRY_RUN=1 python3 src/simulate_v7.py --k 2 --company-only
  python3 src/simulate_v7.py --k 1 --out data_auto/final_eval_1q_v7/run_1
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
from build_persona_v7 import TOPIC_CUES, slugify  # noqa: E402

DATA = os.path.join(ROOT, "data")
PROMPTS = os.path.join(ROOT, "prompts")
RCL_JSON = os.path.join(DATA, "company_persona", "rcl.json")
ASSET_DIR = os.path.join(DATA, "asset_persona")
V7_DIR = os.path.join(DATA, "personas_v7")
TEST = os.path.join(DATA, "analysts_test.json")

TARGET_QUARTER = "2026-Q1"
MIN_QUESTIONS = 5

# Base salience by hook kind (before topic-emphasis masking).
KIND_BASE = {"metric": 1.0, "asset": 0.6, "claim": 0.5}

# Map a metric short-name / hook to a persona topic_emphasis key.
METRIC_TO_TOPIC = {
    "yield": "yield", "EPS": "guidance_targets", "fuel": "fuel", "NCC": "cost_ncc",
    "capacity": "capacity", "fuel_hedge": "fuel", "Caribbean": "destinations",
}


# ---------------------------------------------------------------------------
# Stage 1 — build candidate hooks from the company layer.
# ---------------------------------------------------------------------------
def _fmt_metric(v) -> str:
    if not isinstance(v, dict):
        return str(v)
    if "low" in v and "high" in v:
        return f"{v['low']}-{v['high']}{v.get('unit', '')}"
    if "value" in v:
        return f"{v['value']}{v.get('unit', '')}"
    return v.get("text", json.dumps(v))


def build_company_hooks(rcl: dict, assets: list[dict]) -> list[dict]:
    hooks: list[dict] = []

    # (a) moved metrics on the transition ending at TARGET_QUARTER
    transition = next(
        (t for k, t in rcl.get("deltas_by_transition", {}).items()
         if k.endswith(f"-> {TARGET_QUARTER}")), None)
    if transition:
        for short in transition["moved_most"]:
            pm = transition["per_metric"].get(short, {})
            prior = _fmt_metric(pm.get("prior"))
            current = _fmt_metric(pm.get("current"))
            direction = pm.get("direction", "moved")
            hooks.append({
                "hook_id": f"metric:{short}",
                "kind": "metric",
                "topic": METRIC_TO_TOPIC.get(short, short),
                "text": f"FY guide for {short} {direction}: {prior} -> {current}",
                "anchor": {"prior": prior, "current": current, "direction": direction},
                "rank_within_kind": pm.get("magnitude_rank"),
            })

    # (b) assets whose status changed in TARGET_QUARTER
    for a in assets:
        q = (a.get("lifecycle_by_quarter") or {}).get(TARGET_QUARTER)
        if q and q.get("status_changed_this_quarter"):
            sd = q.get("status_delta", {})
            hooks.append({
                "hook_id": f"asset:{a['asset_id']}",
                "kind": "asset",
                "topic": "destinations",
                "text": f"{a.get('display_name', a['asset_id'])} status changed "
                        f"({sd.get('change_type')}: {sd.get('detail')})",
                "anchor": sd,
            })

    # (c) notable claims from the qualitative narrative
    narrative = (rcl.get("qualitative_narrative_by_quarter") or {}).get(TARGET_QUARTER, {})
    for i, claim in enumerate(narrative.get("notable_claims", [])[:5]):
        hooks.append({
            "hook_id": f"claim:{i}",
            "kind": "claim",
            "topic": _claim_topic(claim),
            "text": claim,
            "anchor": None,
        })
    return hooks


def _claim_topic(claim: str) -> str:
    low = claim.lower()
    for t, cues in TOPIC_CUES.items():
        if any(c in low for c in cues):
            return t
    return "consumer_macro"


# ---------------------------------------------------------------------------
# Stage 1 — rank/mask hooks by the analyst's topic emphasis.
# ---------------------------------------------------------------------------
def rank_hooks(hooks: list[dict], persona: dict | None, company_only: bool) -> list[dict]:
    lift_map = {}
    if persona and not company_only:
        lift_map = (persona.get("topic_emphasis") or {}).get("lift_vs_population", {})
    scored = []
    for h in hooks:
        base = KIND_BASE.get(h["kind"], 0.5)
        # magnitude rank bonus for metrics (rank 1 = biggest move)
        if h.get("rank_within_kind"):
            base += max(0.0, 0.5 - 0.1 * (h["rank_within_kind"] - 1))
        topic_lift = 1.0 if company_only else float(lift_map.get(h["topic"], 1.0))
        score = base * topic_lift
        scored.append({**h, "score": round(score, 4)})
    scored.sort(key=lambda x: -x["score"])
    return scored


# ---------------------------------------------------------------------------
# Stage 2 — render prompt + generate (LLM, DRY_RUN stub).
# ---------------------------------------------------------------------------
def _fill(template: str, **kw) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def _hooks_block(top_hooks: list[dict]) -> str:
    lines = []
    for i, h in enumerate(top_hooks):
        lines.append(f"[{i}] ({h['kind']}, topic={h['topic']}, score={h['score']}) "
                     f"hook_id={h['hook_id']} :: {h['text']}")
    return "\n".join(lines) or "(no salient hooks)"


def _bps_cap_note(persona: dict | None, company_only: bool) -> str:
    if company_only or not persona:
        return "Do NOT default to asking for basis-point quantification unless the hook demands it."
    unq = ((persona.get("probe_type_profile") or {}).get("distribution") or {}).get("UNQUANTIFIED", 0)
    if unq >= 0.15:
        return "This analyst does quantify; a bps/number ask is in-character where it fits."
    return ("CAP the generic 'give me bps' reflex — this analyst rarely opens with a "
            "quantification ask; prefer their characteristic probe type instead.")


def stub_questions(analyst: str, top_hooks: list[dict], k: int, persona: dict | None,
                   company_only: bool) -> dict:
    """Deterministic Stage-2 stub: one templated question per top hook, phrased
    by the analyst's primary probe type. Valid raw_pool content without an API."""
    probe = (persona or {}).get("probe_type_profile") or {}
    primary = (None if company_only else probe.get("primary_by_lift")) or "DELTA"
    out = []
    for h in top_hooks[:k]:
        anchor = h.get("anchor") or {}
        if h["kind"] == "metric":
            q = (f"On {h['topic']}: your {anchor.get('prior')} guide moved to "
                 f"{anchor.get('current')} — what drove the change and how should we "
                 f"think about it going forward?")
        elif h["kind"] == "asset":
            q = f"Can you update us on {h['text']} and what it means for the model?"
        else:
            q = f"You said: \"{h['text']}\" — what underpins that and is it durable?"
        out.append({
            "question_text": q,
            "topic_label": h["topic"],
            "hook_id": h["hook_id"],
            "probe_type": primary if h["kind"] != "claim" else "CLAIM",
        })
    return {"analyst": analyst, "predicted_questions": out}


def generate_for_analyst(analyst: str, persona: dict | None, ranked: list[dict],
                         template: str, k: int, company_only: bool, log_dir: str) -> list[dict]:
    top = ranked[:max(k * 2, 4)]  # give the model a few extra to choose from
    stub = stub_questions(analyst, ranked, k, persona, company_only)

    probe_json = json.dumps((persona or {}).get("probe_type_profile", {}), indent=1)
    form = {
        "coverage_profile": (persona or {}).get("coverage_profile"),
        "reasoning_style": (persona or {}).get("reasoning_style"),
    } if (persona and not company_only) else {"note": "company-only: neutral voice"}
    sig = (persona or {}).get("signature_questions", []) if not company_only else []

    prompt = _fill(
        template,
        analyst_name=analyst,
        quarter=TARGET_QUARTER,
        hooks_block=_hooks_block(top),
        probe_profile_json=("(company-only: neutral)" if company_only else probe_json),
        form_json=json.dumps(form, indent=1),
        signature_json=json.dumps(sig, indent=1),
        bps_cap_note=_bps_cap_note(persona, company_only),
        k_diversity_note=("Span different hooks; no near-duplicates." if k > 1
                          else "Produce only the single best-guess question."),
    )
    out = call_llm(prompt, expect_json=True, dry_run_stub=stub,
                   log_to=os.path.join(log_dir, f"sim_{slugify(analyst)}.txt"))
    try:
        parsed = parse_json_strict(out)
        qs = parsed.get("predicted_questions", [])[:k]
    except Exception:
        qs = stub["predicted_questions"][:k]
    return qs


# ---------------------------------------------------------------------------
def load_personas() -> dict:
    out = {}
    for fn in os.listdir(V7_DIR):
        if fn.endswith(".json") and fn != "_fallback.json":
            p = json.load(open(os.path.join(V7_DIR, fn)))
            out[p["analyst_name"]] = p
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=1, choices=[1, 2, 3])
    ap.add_argument("--company-only", action="store_true")
    ap.add_argument("--out", default=None, help="dir to write raw_pool.json")
    args = ap.parse_args()

    rcl = json.load(open(RCL_JSON))
    assets = [json.load(open(os.path.join(ASSET_DIR, f)))
              for f in sorted(os.listdir(ASSET_DIR)) if f.endswith(".json")]
    test = json.load(open(TEST))
    actuals = test["per_analyst_actual_questions"]
    personas = load_personas()
    fallback = json.load(open(os.path.join(V7_DIR, "_fallback.json")))

    template_path = os.path.join(PROMPTS, f"simulate_questions_v7_{args.k}q.md")
    template = open(template_path).read()
    log_dir = os.path.join(DATA, "prompt_logs")
    os.makedirs(log_dir, exist_ok=True)

    hooks = build_company_hooks(rcl, assets)
    print(f"# company hooks for {TARGET_QUARTER}: {len(hooks)} "
          f"({sum(h['kind']=='metric' for h in hooks)} metric, "
          f"{sum(h['kind']=='asset' for h in hooks)} asset, "
          f"{sum(h['kind']=='claim' for h in hooks)} claim)")

    predicted, actual = [], []
    for analyst, real_qs in actuals.items():
        persona = personas.get(analyst, fallback)
        is_cold = analyst not in personas
        ranked = rank_hooks(hooks, persona, args.company_only)
        qs = generate_for_analyst(analyst, persona, ranked, template, args.k,
                                  args.company_only, log_dir)
        for i, q in enumerate(qs):
            predicted.append({
                "candidate_id": f"{slugify(analyst)}-pred-{i}",
                "source_analyst": analyst,
                "question": q.get("question_text", ""),
                "topic_label": q.get("topic_label", ""),
                "hook_id": q.get("hook_id"),
                "probe_type": q.get("probe_type"),
                "_cold_start": is_cold,
            })
        for i, a in enumerate(real_qs):
            actual.append({
                "actual_id": f"{slugify(analyst)}-actual-{i}",
                "source_analyst": analyst,
                "question": a["question"],
            })

    pool = {"predicted": predicted, "actual": actual,
            "_meta": {"version": "v7", "k": args.k,
                      "mode": "company_only" if args.company_only else "company+persona",
                      "target_quarter": TARGET_QUARTER}}

    print(f"# predicted: {len(predicted)}  # actual: {len(actual)}")
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, "raw_pool.json")
        with open(path, "w") as fp:
            json.dump(pool, fp, indent=2)
        print(f"wrote {path}")
    else:
        print("(no --out; sample predicted[0]):")
        print(json.dumps(predicted[0], indent=2) if predicted else "(none)")


if __name__ == "__main__":
    main()
