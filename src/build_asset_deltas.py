"""Phase C — Asset status deltas (RCL).

For each data/asset_persona/*.json, diff ``lifecycle_by_quarter`` across
consecutive (chronological) quarters and annotate each quarter with:
  - status_changed_this_quarter: bool
  - status_delta: {prior_status, current_status, change_type, detail}

change_type ∈ {newly_tracked, status_transition, date_slip, restatement, none}.
Purely deterministic; fed the same way as the company metric deltas so the
generator can hook "what moved on the asset side."

Usage:
  python3 src/build_asset_deltas.py            # write back into asset files
  python3 src/build_asset_deltas.py --dry      # build + print summary, no write
"""

from __future__ import annotations

import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSET_DIR = os.path.join(ROOT, "data", "asset_persona")

# Year/date cues used to detect a "date slip" (opening pushed to a new year).
_YEAR = re.compile(r"\b(20\d{2})\b")


def _chrono_key(q: str) -> tuple[int, int]:
    m = re.match(r"(\d{4})-Q(\d)", q)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def _years_in(text: str) -> set[str]:
    return set(_YEAR.findall(text or ""))


def diff_lifecycle(lifecycle: dict) -> dict:
    """Return {quarter: status_delta_dict} for each quarter present."""
    quarters = sorted(lifecycle.keys(), key=_chrono_key)
    deltas: dict[str, dict] = {}
    prev_q = None
    for q in quarters:
        cur = lifecycle[q] or {}
        cur_status = cur.get("status")
        cur_summary = cur.get("mgmt_statement_summary", "")
        if prev_q is None:
            deltas[q] = {
                "status_changed_this_quarter": True,
                "status_delta": {
                    "prior_status": None,
                    "current_status": cur_status,
                    "change_type": "newly_tracked",
                    "detail": "first quarter this asset appears in the lifecycle record",
                },
            }
            prev_q = q
            continue

        prev = lifecycle[prev_q] or {}
        prev_status = prev.get("status")
        prev_summary = prev.get("mgmt_statement_summary", "")

        change_type = "none"
        detail = ""
        if cur_status != prev_status:
            change_type = "status_transition"
            detail = f"{prev_status} -> {cur_status}"
        else:
            # Same status: look for a date slip (new opening year mentioned).
            new_years = _years_in(cur_summary) - _years_in(prev_summary)
            future_years = {y for y in new_years if int(y) >= _chrono_key(q)[0]}
            if future_years:
                change_type = "date_slip"
                detail = f"new target year(s) mentioned: {sorted(future_years)}"

        deltas[q] = {
            "status_changed_this_quarter": change_type != "none",
            "status_delta": {
                "prior_status": prev_status,
                "current_status": cur_status,
                "change_type": change_type,
                "detail": detail,
            },
        }
        prev_q = q
    return deltas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    files = sorted(f for f in os.listdir(ASSET_DIR) if f.endswith(".json"))
    for fn in files:
        path = os.path.join(ASSET_DIR, fn)
        asset = json.load(open(path))
        lifecycle = asset.get("lifecycle_by_quarter", {})
        if not lifecycle:
            print(f"  {fn}: no lifecycle_by_quarter, skipping")
            continue
        deltas = diff_lifecycle(lifecycle)
        # Annotate each lifecycle quarter in place.
        for q, d in deltas.items():
            asset["lifecycle_by_quarter"][q]["status_changed_this_quarter"] = \
                d["status_changed_this_quarter"]
            asset["lifecycle_by_quarter"][q]["status_delta"] = d["status_delta"]
        n_changed = sum(1 for d in deltas.values() if d["status_changed_this_quarter"])
        print(f"  {fn}: {len(deltas)} quarters, {n_changed} with status change")
        if not args.dry:
            with open(path, "w") as fp:
                json.dump(asset, fp, indent=2)

    if args.dry:
        print("\n[--dry] not writing asset files")


if __name__ == "__main__":
    main()
