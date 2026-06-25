"""Phase 23 Step 1: scan 18 RCL transcripts to produce per-asset / per-theme /
company-wide mentions slice files for downstream Sonnet sub-agent persona builders.

Output: data_auto/persona_slices/{asset_*,theme_*,company_*}_mentions.json
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARSED = os.path.join(ROOT, "parsed")
OUT = os.path.join(ROOT, "data_auto", "persona_slices")
os.makedirs(OUT, exist_ok=True)

# === Asset keyword library ===
ASSETS = {
    "perfect_day_mexico": {
        "display": "Perfect Day Mexico / Costa Maya",
        "category": "private_destination",
        "keywords": [r"perfect day mexico", r"perfect day costa maya", r"costa maya"],
    },
    "royal_beach_club_santorini": {
        "display": "Royal Beach Club Santorini",
        "category": "private_destination",
        "keywords": [r"royal beach club santorini", r"\bsantorini\b"],
    },
    "royal_beach_club_paradise_island": {
        "display": "Royal Beach Club Paradise Island",
        "category": "private_destination",
        "keywords": [r"royal beach club paradise island", r"\bparadise island\b"],
    },
    "royal_beach_club_cozumel": {
        "display": "Royal Beach Club Cozumel",
        "category": "private_destination",
        "keywords": [r"royal beach club cozumel", r"\bcozumel\b"],
    },
    "icon_class_fleet": {
        "display": "Icon-class fleet",
        "category": "ship_class",
        "keywords": [r"\bicon class\b", r"\bicon\b", r"icon 6", r"icon 7"],
    },
    "legend_of_the_seas": {
        "display": "Legend of the Seas",
        "category": "ship",
        "keywords": [r"legend of the seas", r"\blegend\b"],
    },
    "royal_one_credit_card": {
        "display": "Royal ONE co-branded credit card",
        "category": "loyalty",
        "keywords": [r"royal one", r"co[\s\-]?branded credit card", r"cardholder"],
    },
    "ig_bond_2_5b_2025": {
        "display": "$2.5B Investment-Grade bond (2025-Q1)",
        "category": "financing",
        "keywords": [r"\$2\.5\s*billion bond", r"\$2\.5\s*b(?:n|illion)?\b", r"investment[\-\s]grade bond"],
    },
    "tui_cruises_jv": {
        "display": "TUI Cruises (joint venture)",
        "category": "joint_venture",
        "keywords": [r"\btui\b", r"tui cruises"],
    },
    "perfecta_program": {
        "display": "Perfecta strategic program (2024-2027)",
        "category": "strategic_program",
        "keywords": [r"\bperfecta\b"],
    },
    "trifecta_program": {
        "display": "Trifecta strategic program (2022-2025)",
        "category": "strategic_program",
        "keywords": [r"\btrifecta\b"],
    },
    "cococay": {
        "display": "Perfect Day at CocoCay",
        "category": "private_destination",
        "keywords": [r"\bcococay\b", r"perfect day at cococay"],
    },
}

# === Theme keyword library ===
THEMES = {
    "yield_decomposition": {
        "display": "Yield decomposition / bps walk",
        "keywords": [
            r"net yield", r"\byield\b", r"bps?\s+(?:headwind|tailwind|drag|cut)",
            r"basis points?", r"200bp", r"400bp", r"like[\s\-]for[\s\-]like",
            r"ticket vs onboard", r"onboard vs ticket", r"yield (?:cadence|composition|bridge|decomposition|trajectory|walk)",
        ],
    },
    "cost_cadence_dry_dock": {
        "display": "Cost cadence / dry-dock / structural vs timing",
        "keywords": [
            r"dry[\s\-]dock", r"ncc ex[\s\-]fuel", r"net cruise cost",
            r"structural vs (?:timing|transitional)", r"cost cadence",
            r"crew travel", r"q2 (?:cost|ncc)",
        ],
    },
    "fuel_hedging_dynamics": {
        "display": "Fuel hedging dynamics + sensitivity",
        "keywords": [
            r"fuel hedg", r"fuel headwind", r"fuel sensitivity", r"60%\s*hedged",
            r"59%\s*hedged", r"\$0\.62", r"\$0\.74", r"fuel expense",
            r"per\s*share fuel", r"hedge profile",
        ],
    },
    "booking_dynamics": {
        "display": "Booking dynamics / forward visibility / recovery",
        "keywords": [
            r"book(?:ed|ing) curve", r"booking visibility", r"close[\s\-]in book",
            r"forward book", r"booked position", r"booked load factor",
            r"booked apd", r"wave season", r"recovery trajectory", r"turning the corner",
            r"booking pace", r"booking moderation",
        ],
    },
    "capital_allocation_pattern": {
        "display": "Capital allocation: buyback / leverage / financing choice",
        "keywords": [
            r"buyback", r"share repurchas", r"capital return",
            r"net leverage", r"leverage below 3x", r"investment[\s\-]grade",
            r"eca (?:financing|funding|backed)", r"unsecured bond", r"capital allocation",
            r"deleveraging", r"dividend",
        ],
    },
}

# === Company KPI vocab (track frequency) ===
COMPANY_KPI = [
    "Net Yield", "constant currency", "APD", "Load Factor", "NCC ex-fuel",
    "Adjusted EPS", "Adjusted EBITDA", "ROIC", "Net Leverage", "Free Cash Flow",
    "Operating Income", "APCD", "Capacity Growth", "Booking Curve", "Trifecta",
    "Perfecta", "Hedged", "Wave Season",
]


def parse_quarter_from_filename(fn: str) -> str:
    """e.g. '2026-q1-548547.json' -> '2026-Q1'"""
    m = re.match(r"(\d{4})-q(\d)", fn.lower())
    return f"{m.group(1)}-Q{m.group(2)}" if m else fn


def extract_sentences(text: str) -> list[str]:
    """Very simple sentence splitter."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def find_mentions(text: str, patterns: list[str]) -> list[str]:
    """Return sentences in `text` that match any of the regex `patterns`."""
    hits = []
    sents = extract_sentences(text)
    for s in sents:
        for p in patterns:
            if re.search(p, s, re.IGNORECASE):
                hits.append(s)
                break
    return hits


def load_all_transcripts() -> dict[str, dict]:
    """Returns {quarter: parsed_transcript_dict}"""
    out = {}
    for fn in sorted(os.listdir(PARSED)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        q = parse_quarter_from_filename(fn)
        out[q] = json.load(open(os.path.join(PARSED, fn)))
    return out


def is_management_speaker(affiliation: str | None) -> bool:
    """Heuristic: management has Royal Caribbean / Cruise affiliation."""
    if not affiliation:
        return False
    a = affiliation.lower()
    return any(k in a for k in ["royal caribbean", "ceo", "cfo", "chairman", "president", "investor relations", "rci"])


def extract_asset_slice(asset_id: str, meta: dict, transcripts: dict) -> dict:
    """For one asset, collect per-quarter mgmt mentions + per-quarter analyst Q&A mentions."""
    out = {
        "asset_id": asset_id,
        "display_name": meta["display"],
        "category": meta["category"],
        "matched_keywords": meta["keywords"],
        "mgmt_mentions_by_quarter": {},
        "qa_mentions_by_quarter": defaultdict(list),
        "all_analysts_mentioning": set(),
    }
    for q, t in transcripts.items():
        # Mgmt: presentation_turns + qa_turns where speaker is mgmt
        mgmt_text_parts = []
        for pt in t.get("presentation_turns", []):
            if isinstance(pt, dict):
                mgmt_text_parts.append(pt.get("text", ""))
        for qa in t.get("qa_turns", []):
            if isinstance(qa, dict) and is_management_speaker(qa.get("affiliation")):
                mgmt_text_parts.append(qa.get("text", ""))
        mgmt_text = "\n".join(mgmt_text_parts)
        mgmt_hits = find_mentions(mgmt_text, meta["keywords"])
        if mgmt_hits:
            out["mgmt_mentions_by_quarter"][q] = mgmt_hits[:6]  # cap

        # Analyst Q&A mentions
        for qa in t.get("qa_turns", []):
            if not isinstance(qa, dict):
                continue
            if is_management_speaker(qa.get("affiliation")):
                continue
            speaker = (qa.get("speaker") or "").strip().lower()
            if not speaker or speaker == "operator":
                continue
            text = qa.get("text", "")
            hits = find_mentions(text, meta["keywords"])
            if hits:
                out["qa_mentions_by_quarter"][q].append({
                    "analyst": speaker,
                    "affiliation": qa.get("affiliation"),
                    "question_snippet": text[:600],
                    "matched_sentences": hits[:3],
                })
                out["all_analysts_mentioning"].add(speaker)
    out["qa_mentions_by_quarter"] = dict(out["qa_mentions_by_quarter"])
    out["all_analysts_mentioning"] = sorted(out["all_analysts_mentioning"])
    return out


def extract_theme_slice(theme_id: str, meta: dict, transcripts: dict) -> dict:
    """For one theme, collect per-quarter analyst Q&A framings (don't bother with mgmt — themes are about analyst questioning patterns)."""
    out = {
        "theme_id": theme_id,
        "display_name": meta["display"],
        "matched_keywords": meta["keywords"],
        "qa_framings_by_quarter": defaultdict(list),
        "analyst_framing_counts": defaultdict(int),
    }
    for q, t in transcripts.items():
        for qa in t.get("qa_turns", []):
            if not isinstance(qa, dict):
                continue
            if is_management_speaker(qa.get("affiliation")):
                continue
            speaker = (qa.get("speaker") or "").strip().lower()
            if not speaker or speaker == "operator":
                continue
            text = qa.get("text", "")
            hits = find_mentions(text, meta["keywords"])
            if hits:
                out["qa_framings_by_quarter"][q].append({
                    "analyst": speaker,
                    "affiliation": qa.get("affiliation"),
                    "question_snippet": text[:500],
                    "matched_sentences": hits[:2],
                })
                out["analyst_framing_counts"][speaker] += 1
    out["qa_framings_by_quarter"] = dict(out["qa_framings_by_quarter"])
    out["analyst_framing_counts"] = dict(out["analyst_framing_counts"])
    return out


def extract_company_slice(transcripts: dict) -> dict:
    """For Layer 1 Company persona: collect kpi vocab usage, speaker roles, recurring headwinds."""
    out = {
        "company_name": "Royal Caribbean Group",
        "tickers": ["RCL"],
        "quarters_covered": sorted(transcripts.keys()),
        "speaker_roles": defaultdict(set),
        "kpi_usage_count": defaultdict(int),
        "headwind_mentions": defaultdict(list),
        "period_anchors_by_quarter": {},
    }
    HEADWIND_PATTERNS = {
        "fuel": [r"fuel headwind", r"fuel price", r"\$0\.\d{2}.*fuel", r"hedged"],
        "fx": [r"\bfx\b", r"foreign exchange", r"currency"],
        "dry_dock": [r"dry[\s\-]dock"],
        "geopolitical": [r"geopolitic", r"middle east", r"israel", r"war"],
        "macro": [r"airfare", r"consumer", r"recession", r"interest rate"],
        "mediterranean": [r"mediterranean (?:moderation|disruption|softness)"],
    }
    # Period anchors: specific patterns to extract per quarter
    ANCHOR_PATTERNS = {
        "fy_eps_guide": r"\$(\d+\.\d{2})\s*[-–]\s*\$(\d+\.\d{2})\s*(?:per share)?\s*(?:adjusted )?eps",
        "fy_net_yield_guide": r"(\d\.?\d*)\s*%\s*[-–]\s*(\d\.?\d*)\s*%\s*(?:constant currency )?net yield",
        "fuel_hedged_pct": r"(?:approximately\s*)?(\d{2,3})\s*%\s*hedged",
        "buyback_remaining": r"\$(\d+(?:\.\d+)?)\s*(?:billion|b)\s*remaining",
    }

    for q, t in transcripts.items():
        # Speaker roles
        for pt in t.get("presentation_turns", []):
            if isinstance(pt, dict):
                sp = pt.get("speaker")
                aff = pt.get("affiliation")
                if sp and aff:
                    out["speaker_roles"][sp].add(aff)
        for qa in t.get("qa_turns", []):
            if isinstance(qa, dict) and is_management_speaker(qa.get("affiliation")):
                sp = qa.get("speaker")
                aff = qa.get("affiliation")
                if sp and aff:
                    out["speaker_roles"][sp].add(aff)

        # KPI usage frequency
        all_mgmt_text = ""
        for pt in t.get("presentation_turns", []):
            if isinstance(pt, dict):
                all_mgmt_text += pt.get("text", "") + "\n"
        for qa in t.get("qa_turns", []):
            if isinstance(qa, dict) and is_management_speaker(qa.get("affiliation")):
                all_mgmt_text += qa.get("text", "") + "\n"

        for kpi in COMPANY_KPI:
            out["kpi_usage_count"][kpi] += len(re.findall(re.escape(kpi), all_mgmt_text, re.IGNORECASE))

        # Headwinds
        for hw, pats in HEADWIND_PATTERNS.items():
            for s in extract_sentences(all_mgmt_text):
                for p in pats:
                    if re.search(p, s, re.IGNORECASE):
                        out["headwind_mentions"][hw].append({"quarter": q, "snippet": s[:250]})
                        break

        # Period anchors
        anchors = {}
        for name, pat in ANCHOR_PATTERNS.items():
            m = re.search(pat, all_mgmt_text, re.IGNORECASE)
            if m:
                anchors[name] = m.group(0)[:200]
        # Also capture raw prepared-remarks first 800 chars for context
        first_pt_text = ""
        if t.get("presentation_turns"):
            first_pt_text = t["presentation_turns"][0].get("text", "")[:800]
        anchors["prepared_remarks_intro"] = first_pt_text
        out["period_anchors_by_quarter"][q] = anchors

    # Normalize
    out["speaker_roles"] = {k: sorted(list(v)) for k, v in out["speaker_roles"].items()}
    out["kpi_usage_count"] = dict(sorted(out["kpi_usage_count"].items(), key=lambda x: -x[1]))
    out["headwind_mentions"] = {k: v[:20] for k, v in out["headwind_mentions"].items()}  # cap
    return out


def main():
    transcripts = load_all_transcripts()
    print(f"Loaded {len(transcripts)} RCL transcripts: {sorted(transcripts.keys())}")

    # Assets
    print(f"\n=== Building {len(ASSETS)} asset slices ===")
    for asset_id, meta in ASSETS.items():
        slc = extract_asset_slice(asset_id, meta, transcripts)
        p = os.path.join(OUT, f"asset_{asset_id}_mentions.json")
        with open(p, "w") as f:
            json.dump(slc, f, indent=2)
        n_mgmt_qrts = len(slc["mgmt_mentions_by_quarter"])
        n_qa_qrts = len(slc["qa_mentions_by_quarter"])
        n_analysts = len(slc["all_analysts_mentioning"])
        print(f"  {asset_id:35s} mgmt:{n_mgmt_qrts}qrt qa:{n_qa_qrts}qrt analysts:{n_analysts}")

    # Themes
    print(f"\n=== Building {len(THEMES)} theme slices ===")
    for theme_id, meta in THEMES.items():
        slc = extract_theme_slice(theme_id, meta, transcripts)
        p = os.path.join(OUT, f"theme_{theme_id}_mentions.json")
        with open(p, "w") as f:
            json.dump(slc, f, indent=2)
        n_q = len(slc["qa_framings_by_quarter"])
        n_a = len(slc["analyst_framing_counts"])
        print(f"  {theme_id:35s} qrts:{n_q} analysts:{n_a}")

    # Company
    print(f"\n=== Building Company slice ===")
    slc = extract_company_slice(transcripts)
    p = os.path.join(OUT, "company_mentions.json")
    with open(p, "w") as f:
        json.dump(slc, f, indent=2)
    print(f"  speakers tracked: {list(slc['speaker_roles'].keys())[:5]}")
    print(f"  top KPIs: {list(slc['kpi_usage_count'].items())[:5]}")
    print(f"  headwinds tracked: {list(slc['headwind_mentions'].keys())}")
    print(f"  quarters in period_anchors: {len(slc['period_anchors_by_quarter'])}")

    print(f"\nDone. Output to {OUT}")


if __name__ == "__main__":
    main()
