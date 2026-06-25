"""v6 simulator: load 5 persona layers + filter + call LLM to produce K questions per analyst.

Usage: python3 src/rerun_v6_kq.py --K 5

Output: data_auto/final_eval_<K>q_v6/summary.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from llm_client import call_llm, parse_json_strict  # noqa: E402
from run_pipeline import _fill, load_text  # noqa: E402

PROMPTS = os.path.join(ROOT, "prompts")
DATA_AUTO = os.path.join(ROOT, "data_auto")
COMPANY_PERSONA = os.path.join(ROOT, "data", "company_persona", "rcl.json")
ASSET_DIR = os.path.join(ROOT, "data", "asset_persona")
THEME_DIR = os.path.join(ROOT, "data", "theme_persona")
V6_DIR = os.path.join(ROOT, "data", "personas_v6")
AUTO_FALLBACK = os.path.join(DATA_AUTO, "final_personas", "_fallback.json")

TEST_RETURNING = [
    "matthew boss", "steven wieczynski", "brandt montour", "james hardiman",
    "lizzie dove", "robin farley", "vince ciepiel", "sharon zackfia",
    "andrew didora",
]
COLD_START = ["xian siew", "kevin kopelman"]
ALL_11 = TEST_RETURNING + COLD_START


def _safe(s: str) -> str:
    return s.replace(" ", "_")


def load_analyst_persona(name: str) -> dict:
    """Load v6 persona if exists; else fall back to auto _fallback.json (cold-start)."""
    p = os.path.join(V6_DIR, f"{_safe(name)}.json")
    if os.path.exists(p):
        return json.load(open(p))
    fb = json.load(open(AUTO_FALLBACK))
    return {
        "analyst_name": name,
        "coverage_profile": fb.get("coverage_profile", {}),
        "reasoning_style": fb.get("reasoning_style", {}),
        "blind_spots": "(cold-start; no history)",
        "stance_drift": "(cold-start; no history)",
        "queue_behavior": {},
        "cross_analyst_reactivity": {},
        "engages_assets": [],
        "engages_themes": [],
        "framing_overrides_by_theme": {},
        "_source": "auto_fallback (cold-start)",
    }


def load_all_assets() -> dict[str, dict]:
    out = {}
    for fn in sorted(os.listdir(ASSET_DIR)):
        if fn.endswith(".json"):
            d = json.load(open(os.path.join(ASSET_DIR, fn)))
            asset_id = d.get("asset_id", fn.replace(".json", ""))
            out[asset_id] = d
    return out


def load_all_themes() -> dict[str, dict]:
    out = {}
    for fn in sorted(os.listdir(THEME_DIR)):
        if fn.endswith(".json"):
            d = json.load(open(os.path.join(THEME_DIR, fn)))
            theme_id = d.get("theme_id", fn.replace(".json", ""))
            out[theme_id] = d
    return out


def quarter_le(q: str, target_q: str) -> bool:
    """Compare 'YYYY-Qn' strings — returns True if q <= target_q."""
    def parse(s):
        m = re.match(r"(\d{4})-Q(\d)", s)
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    return parse(q) <= parse(target_q)


def trim_asset_for_quarter(asset: dict, target_quarter: str) -> dict:
    """Return a slimmed asset dict: only include lifecycle ≤ target_quarter, and recent asked_by_history ≤ target_quarter."""
    out = {
        "asset_id": asset.get("asset_id"),
        "display_name": asset.get("display_name"),
        "category": asset.get("category"),
        "linked_pillars": asset.get("linked_pillars", []),
    }
    lc = asset.get("lifecycle_by_quarter", {})
    if isinstance(lc, dict):
        out["lifecycle_by_quarter"] = {q: v for q, v in lc.items() if quarter_le(q, target_quarter)}
    ar = asset.get("analyst_relevance", {})
    if isinstance(ar, dict):
        history = ar.get("asked_by_history", [])
        if isinstance(history, list):
            filtered = [h for h in history if isinstance(h, dict) and quarter_le(h.get("call", "0000-Q0"), target_quarter)]
            out["analyst_relevance"] = {
                "asked_by_history": filtered[:8],  # cap
                "primary_framings_observed": ar.get("primary_framings_observed", [])[:6],
            }
    open_q = asset.get("currently_open_questions_as_of_2026Q1", [])
    if isinstance(open_q, list):
        out["currently_open_questions"] = open_q[:6]
    return out


def select_relevant_assets(analyst_v6: dict, all_assets: dict, target_quarter: str, transcript_text: str) -> list[dict]:
    """Pick assets that are:
      (a) in analyst.engages_assets, OR
      (b) currently active (lifecycle has entry for target_quarter or prior 2 quarters) AND mentioned in transcript by name
    Cap to 6 assets to control prompt size.
    """
    engages = set(analyst_v6.get("engages_assets", []))
    transcript_lower = transcript_text.lower()
    selected = []

    # First add engaged assets (filter ≤ quarter)
    for aid in engages:
        a = all_assets.get(aid)
        if a:
            selected.append(trim_asset_for_quarter(a, target_quarter))

    # Then add assets mentioned by name in transcript (if not already in)
    have = {s["asset_id"] for s in selected}
    for aid, a in all_assets.items():
        if aid in have:
            continue
        name = (a.get("display_name") or "").lower()
        # check if any keyword from name appears in transcript
        words = [w for w in re.split(r"[\s/\-_]+", name) if len(w) > 3 and w not in ("with", "from", "the", "and", "for", "into", "this", "that")]
        if any(w in transcript_lower for w in words):
            selected.append(trim_asset_for_quarter(a, target_quarter))
            have.add(aid)
        if len(selected) >= 6:
            break

    return selected[:6]


def select_relevant_themes(analyst_v6: dict, all_themes: dict) -> list[dict]:
    """Pick themes analyst engages, plus 1-2 always-on themes (booking, yield)."""
    engaged_ids = analyst_v6.get("engages_themes", [])
    always_on = ["yield_decomposition", "booking_dynamics"]  # broad themes any analyst might touch
    chosen = list(dict.fromkeys(engaged_ids + always_on))[:5]
    out = []
    for tid in chosen:
        t = all_themes.get(tid)
        if t:
            slim = {
                "theme_id": t.get("theme_id"),
                "display_name": t.get("display_name"),
                "description": t.get("description"),
                "default_framing_options": t.get("default_framing_options", [])[:5],
                "analyst_affinity_for_this_analyst": (t.get("analyst_affinity") or {}).get(analyst_v6["analyst_name"].lower(), ""),
            }
            out.append(slim)
    return out


def build_prompt_for_analyst(name: str, K: int, quarter: str) -> str:
    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    mgmt = test["management_context"]

    company = json.load(open(COMPANY_PERSONA))
    all_assets = load_all_assets()
    all_themes = load_all_themes()

    analyst_v6 = load_analyst_persona(name)
    rel_assets = select_relevant_assets(analyst_v6, all_assets, quarter, mgmt)
    rel_themes = select_relevant_themes(analyst_v6, all_themes)

    tpl = load_text(os.path.join(PROMPTS, f"simulate_questions_v6_{K}q.md"))
    # Strip Q&A so far from transcript if present
    if "[Q&A SO FAR]" in mgmt:
        mgmt = mgmt.split("[Q&A SO FAR]", 1)[0].rstrip()

    return _fill(
        tpl,
        analyst_name=name,
        quarter=quarter,
        company_persona_json=json.dumps(company, indent=2),
        asset_personas_json=json.dumps(rel_assets, indent=2),
        theme_personas_json=json.dumps(rel_themes, indent=2),
        analyst_persona_json=json.dumps(analyst_v6, indent=2),
        management_presentation=mgmt,
    )


def stub_predictions(name: str, K: int) -> dict:
    return {
        "analyst": name,
        "predicted_questions": [
            {"question_text": f"[STUB {i}] for {name}", "topic_label": "stub",
             "linked_asset_id": None, "linked_theme_id": None,
             "dimension_tags": {"topic": "stub", "object": "stub", "framing": "stub", "granularity": "stub", "form": "single"},
             "rationale": "DRY_RUN stub"}
            for i in range(K)
        ],
    }


def run(K: int, quarter: str = "2026-Q1") -> None:
    out_dir = os.path.join(DATA_AUTO, f"final_eval_{K}q_v6")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    test = json.load(open(os.path.join(DATA_AUTO, "test.json")))
    actuals_by = test["per_analyst_actual_questions"]

    per_analyst: dict[str, dict] = {}
    total = 0
    for name in ALL_11:
        actuals = actuals_by.get(name, [])
        if not actuals:
            continue
        prompt = build_prompt_for_analyst(name, K, quarter)
        log_path = os.path.join(log_dir, f"sim_{_safe(name)}.txt")
        out = call_llm(prompt, expect_json=True,
                       dry_run_stub=stub_predictions(name, K),
                       log_to=log_path)
        try:
            pred = parse_json_strict(out)
        except Exception as e:
            print(f"  ! {name}: parse failed ({e}); stub")
            pred = stub_predictions(name, K)
        pq = pred.get("predicted_questions", [])
        if len(pq) > K:
            pred["predicted_questions"] = pq[:K]
        elif len(pq) < K:
            print(f"  ! {name}: simulator returned {len(pq)} (expected {K})")
        per_analyst[name] = {
            "n_actual": len(actuals),
            "predictions": pred,
            "persona_source": "v6" if name in TEST_RETURNING else "auto-fallback",
        }
        total += len(pred.get("predicted_questions", []))
        print(f"  {name:25s} K={len(pred.get('predicted_questions', []))}")

    summary = {
        "n_analysts_scored": len(per_analyst),
        "K": K,
        "source": "v6",
        "quarter": quarter,
        "total_predicted_questions": total,
        "per_analyst": per_analyst,
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {out_dir}/summary.json ({total} questions, {len(per_analyst)} analysts)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, required=True)
    ap.add_argument("--quarter", default="2026-Q1")
    args = ap.parse_args()
    run(args.K, args.quarter)


if __name__ == "__main__":
    main()
