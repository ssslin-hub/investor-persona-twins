"""Phase A — Company metric ledger + same-FY deltas (RCL).

Builds the shared "company context" salience signal:

  1. Parse prepared remarks of all 17 calls (reuse parse_transcripts.split_call).
  2. Deterministically extract a per-quarter metric ledger, tagging the fiscal
     year each forward guide refers to (``guidance_for_fy``).
  3. Overlay spec-verified anchors + the values already curated in rcl.json
     (these take precedence over regex; provenance is tagged per value).
  4. Compute ``deltas_by_transition`` ONLY between consecutive same-FY guides
     (skip the Q3->Q4 roll-forward). Emit ranked ``moved_most`` + ``unchanged``.
  5. Validation gate: 2025-Q4 -> 2026-Q1 must move [yield, EPS, fuel, NCC] and
     leave [capacity, Caribbean] unchanged.
  6. Write period_anchors_by_quarter (all 17) + deltas_by_transition back into
     data/company_persona/rcl.json.

No fabricated numbers: a value we cannot source is written as null with a
``_needs_review`` flag; provenance ("parsed" | "verified" | "rcl_existing") is
recorded under ``_provenance`` for each quarter.

Usage:
  python3 src/build_company_ledger.py            # build + write
  python3 src/build_company_ledger.py --dry      # build + print, do not write
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from parse_transcripts import parse_transcript, split_call, parse_turns, html_to_lines  # noqa: E402

RCL_JSON = os.path.join(ROOT, "data", "company_persona", "rcl.json")
TRANSCRIPTS = os.path.join(ROOT, "transcripts")

# The 7 ledger metrics we track per quarter (+ quarter_result actuals).
METRIC_KEYS = [
    "fy_net_yield_guide",
    "fy_eps_guide",
    "fy_capacity_growth",
    "fy_fuel_expense",
    "fuel_hedged_pct",
    "fy_ncc_exfuel_guide",
    "caribbean_share",
]

# Canonical short names used in moved_most / unchanged rankings.
METRIC_SHORT = {
    "fy_net_yield_guide": "yield",
    "fy_eps_guide": "EPS",
    "fy_capacity_growth": "capacity",
    "fy_fuel_expense": "fuel",
    "fuel_hedged_pct": "fuel_hedge",
    "fy_ncc_exfuel_guide": "NCC",
    "caribbean_share": "Caribbean",
}


# ---------------------------------------------------------------------------
# Spec-verified anchors (from persona_v7_build_plan.md §1 + existing rcl.json).
# These are KNOWN-CORRECT values; they take precedence over regex parsing.
# Each value is a numeric/structured form so deltas are computable.
# ---------------------------------------------------------------------------
# FY net-yield guides as (low, high) in % constant-currency.
# FY EPS guides as (low, high) in $. Fuel expense in $B. Capacity in %.
VERIFIED: dict[str, dict] = {
    "2026-Q1": {
        "guidance_for_fy": 2026,
        "fy_net_yield_guide": {"low": 1.5, "high": 2.5, "unit": "%cc"},
        "fy_eps_guide": {"low": 17.10, "high": 17.50, "unit": "$"},
        "fy_capacity_growth": {"value": 6.7, "unit": "%"},
        "fy_fuel_expense": {"value": 1.35, "unit": "$B"},
        "fuel_hedged_pct": {"value": 60, "unit": "%"},
        "fy_ncc_exfuel_guide": {"text": "improved vs prior guide", "midpoint": None,
                                 "changed_vs_prior": "improved"},
        "caribbean_share": {"value": 57, "unit": "%"},
        "quarter_result": {"net_yield_pct": 2.0, "eps": None},
    },
    "2025-Q4": {
        "guidance_for_fy": 2026,
        "fy_net_yield_guide": {"low": 1.5, "high": 3.5, "unit": "%cc"},
        "fy_eps_guide": {"low": 17.70, "high": 18.10, "unit": "$"},
        "fy_capacity_growth": {"value": 6.7, "unit": "%"},
        "fy_fuel_expense": {"value": 1.17, "unit": "$B"},
        "fuel_hedged_pct": {"value": 60, "unit": "%"},
        "fy_ncc_exfuel_guide": {"text": "initial FY2026 NCC ex-fuel guide", "midpoint": None},
        "caribbean_share": {"value": 57, "unit": "%"},
        "quarter_result": {"net_yield_pct": 2.5, "eps": 2.80},
    },
}


def _is_meaningful(v) -> bool:
    """True if v is a real value, not a null / all-null placeholder dict."""
    if v is None:
        return False
    if isinstance(v, dict):
        return any(vv is not None for vv in v.values())
    return True


def guidance_for_fy(year: int, quarter: int) -> int:
    """Q4 of year Y gives the initial guide for FY(Y+1); Q1-Q3 guide FY Y."""
    return year + 1 if quarter == 4 else year


# ---------------------------------------------------------------------------
# Deterministic regex extraction from prepared remarks (best-effort backfill).
# ---------------------------------------------------------------------------
_RANGE = r"(\d+(?:\.\d+)?)\s*%?\s*(?:to|-|–|—)\s*(\d+(?:\.\d+)?)\s*%"
_DOLLAR_RANGE = r"\$(\d+(?:\.\d+)?)\s*(?:to|-|–|—)\s*\$?(\d+(?:\.\d+)?)"


def _search(pat: str, text: str):
    m = re.search(pat, text, re.I)
    return m


def extract_regex(pres: str) -> dict:
    """Best-effort numeric extraction from one call's prepared remarks.

    Returns only fields it can find with reasonable confidence; everything else
    is left out (the caller fills with null + _needs_review).
    """
    out: dict = {}

    # Fuel hedge %: "approximately 60% hedged" / "60% of our ... hedged".
    m = _search(r"(\d{1,3})\s*%\s*(?:hedged|of (?:our )?(?:projected )?fuel[^.]{0,40}hedged)", pres)
    if not m:
        m = _search(r"approximately\s*(\d{1,3})\s*%\s*hedged", pres)
    if m:
        out["fuel_hedged_pct"] = {"value": int(m.group(1)), "unit": "%"}

    # Fuel expense: "$1.17 billion" near the word fuel.
    m = _search(r"fuel\D{0,60}?\$(\d+(?:\.\d+)?)\s*billion", pres)
    if not m:
        m = _search(r"\$(\d+(?:\.\d+)?)\s*billion\D{0,40}?fuel", pres)
    if m:
        out["fy_fuel_expense"] = {"value": float(m.group(1)), "unit": "$B"}

    # Caribbean share: "Caribbean represents 57% of our deployment".
    m = _search(r"Caribbean\D{0,40}?(\d{1,2})\s*%\s*of (?:our )?deployment", pres)
    if m:
        out["caribbean_share"] = {"value": int(m.group(1)), "unit": "%"}

    return out


def parse_call(path: str) -> dict:
    rec = parse_transcript(path)
    pres = " ".join(t["text"] for t in rec.get("presentation_turns", []))
    # Fallback: if presentation split failed, use the raw lines minus Q&A markers.
    if len(pres) < 500:
        lines = html_to_lines(path)
        turns = parse_turns(lines)
        p, _ = split_call(turns)
        pres = " ".join(t.text for t in p)
    return {
        "year": rec["year"],
        "quarter": rec["quarter"],
        "presentation_text": pres,
        "parsed": extract_regex(pres),
    }


# ---------------------------------------------------------------------------
# Build the ledger: merge VERIFIED > rcl_existing > parsed.
# ---------------------------------------------------------------------------
def build_ledger(rcl: dict) -> tuple[dict, dict]:
    existing = rcl.get("period_anchors_by_quarter", {}) or {}
    files = sorted(f for f in os.listdir(TRANSCRIPTS) if f.endswith(".html"))

    anchors: dict[str, dict] = {}
    for fn in files:
        c = parse_call(os.path.join(TRANSCRIPTS, fn))
        q = f"{c['year']}-Q{c['quarter']}"
        fy = guidance_for_fy(c["year"], c["quarter"])
        entry: dict = {"guidance_for_fy": fy}
        prov: dict = {}

        verified = VERIFIED.get(q, {})
        parsed = c["parsed"]
        existing_q = existing.get(q, {})

        for key in METRIC_KEYS:
            if key in verified:
                entry[key] = verified[key]
                prov[key] = "verified"
            elif key in parsed:
                entry[key] = parsed[key]
                prov[key] = "parsed"
            else:
                # Surface a prior rcl.json value as a text note — but only if it
                # is a MEANINGFUL value (not a null/needs_review placeholder from
                # a previous run, which would silently mask missing data).
                ev = existing_q.get(key)
                if _is_meaningful(ev):
                    entry[key] = ev if isinstance(ev, dict) else {"text": ev}
                    prov[key] = "rcl_existing"
                else:
                    entry[key] = None
                    prov[key] = "needs_review"

        if "quarter_result" in verified:
            entry["quarter_result"] = verified["quarter_result"]
            prov["quarter_result"] = "verified"

        # Preserve any human notes already in rcl.json.
        if isinstance(existing_q, dict):
            for k in ("notes", "quarter_highlights"):
                if k in existing_q and k not in entry:
                    entry[k] = existing_q[k]

        entry["_provenance"] = prov
        if "needs_review" in prov.values():
            entry["_needs_review"] = sorted(
                k for k, v in prov.items() if v == "needs_review")
        anchors[q] = entry

    deltas = compute_deltas(anchors)
    return anchors, deltas


# ---------------------------------------------------------------------------
# Deltas: only between consecutive same-FY guides.
# ---------------------------------------------------------------------------
def _midpoint(v) -> float | None:
    if not isinstance(v, dict):
        return None
    if "value" in v and isinstance(v["value"], (int, float)):
        return float(v["value"])
    if "low" in v and "high" in v and isinstance(v["low"], (int, float)):
        return (float(v["low"]) + float(v["high"])) / 2.0
    if v.get("midpoint") is not None:
        return float(v["midpoint"])
    return None


def _chrono_key(q: str) -> tuple[int, int]:
    y, qq = q.split("-Q")
    return int(y), int(qq)


def compute_deltas(anchors: dict) -> dict:
    quarters = sorted(anchors.keys(), key=_chrono_key)
    transitions: dict = {}
    for prev, cur in zip(quarters, quarters[1:]):
        fy_prev = anchors[prev].get("guidance_for_fy")
        fy_cur = anchors[cur].get("guidance_for_fy")
        if fy_prev != fy_cur:
            continue  # roll-forward; not comparable
        moved = []
        unchanged = []
        per_metric = {}
        for key in METRIC_KEYS:
            short = METRIC_SHORT[key]
            mp_prev = _midpoint(anchors[prev].get(key))
            mp_cur = _midpoint(anchors[cur].get(key))
            if mp_prev is None or mp_cur is None:
                # Fall back to text equality where numeric is unavailable.
                tp = anchors[prev].get(key)
                tc = anchors[cur].get(key)
                # Verified qualitative move (e.g. NCC "improved") with no number.
                qual = tc.get("changed_vs_prior") if isinstance(tc, dict) else None
                if qual and qual != "unchanged":
                    moved.append((short, 0.0))  # ranked after numeric moves
                    per_metric[short] = {
                        "prior": tp, "current": tc, "delta": None,
                        "direction": qual, "magnitude_rank": None,
                    }
                    continue
                if isinstance(tp, dict) and isinstance(tc, dict) and tp == tc:
                    unchanged.append(short)
                per_metric[short] = {
                    "prior": tp, "current": tc, "delta": None,
                    "direction": "unknown", "magnitude_rank": None,
                }
                continue
            delta = round(mp_cur - mp_prev, 4)
            direction = "flat" if abs(delta) < 1e-9 else ("up" if delta > 0 else "down")
            per_metric[short] = {
                "prior": anchors[prev].get(key),
                "current": anchors[cur].get(key),
                "delta": delta,
                "direction": direction,
            }
            if direction == "flat":
                unchanged.append(short)
            else:
                moved.append((short, abs(delta)))
        # Rank moved by magnitude; attach magnitude_rank.
        moved_sorted = [s for s, _ in sorted(moved, key=lambda x: -x[1])]
        for rank, s in enumerate(moved_sorted, 1):
            per_metric[s]["magnitude_rank"] = rank
        transitions[f"{prev} -> {cur}"] = {
            "guidance_for_fy": fy_cur,
            "moved_most": moved_sorted,
            "unchanged": sorted(unchanged),
            "per_metric": per_metric,
        }
    return transitions


# ---------------------------------------------------------------------------
def validate(deltas: dict) -> bool:
    key = "2025-Q4 -> 2026-Q1"
    t = deltas.get(key)
    if not t:
        print(f"[VALIDATE] FAIL — transition {key!r} absent")
        return False
    moved = set(t["moved_most"])
    unchanged = set(t["unchanged"])
    want_moved = {"yield", "EPS", "fuel", "NCC"}
    want_unchanged = {"capacity", "Caribbean"}
    ok_moved = want_moved.issubset(moved)
    ok_unchanged = want_unchanged.issubset(unchanged)
    print(f"[VALIDATE] {key}")
    print(f"  moved_most = {t['moved_most']}")
    print(f"  unchanged  = {t['unchanged']}")
    print(f"  moved ⊇ {sorted(want_moved)} ? {ok_moved}")
    print(f"  unchanged ⊇ {sorted(want_unchanged)} ? {ok_unchanged}")
    ok = ok_moved and ok_unchanged
    print(f"[VALIDATE] {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="build + print, do not write")
    args = ap.parse_args()

    rcl = json.load(open(RCL_JSON))
    anchors, deltas = build_ledger(rcl)

    n_q = len(anchors)
    n_needs = sum(1 for q in anchors.values() if q.get("_needs_review"))
    print(f"# quarters: {n_q}  (with needs_review fields: {n_needs})")
    print(f"# same-FY transitions: {len(deltas)}")

    ok = validate(deltas)

    rcl["period_anchors_by_quarter"] = anchors
    rcl["deltas_by_transition"] = deltas

    if args.dry:
        print("\n[--dry] not writing rcl.json")
        return
    with open(RCL_JSON, "w") as fp:
        json.dump(rcl, fp, indent=2)
    print(f"\nwrote {RCL_JSON}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
