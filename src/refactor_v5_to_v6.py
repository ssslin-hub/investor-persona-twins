"""Refactor v5 analyst personas → v6 by removing fields that overlap with the
new Company / Asset / Theme layers, and adding engages_assets / engages_themes
cross-references mined from the asset & theme persona libraries' asked_by_history.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V5_DIR = os.path.join(ROOT, "data", "personas_v5")
V6_DIR = os.path.join(ROOT, "data", "personas_v6")
ASSET_DIR = os.path.join(ROOT, "data", "asset_persona")
THEME_DIR = os.path.join(ROOT, "data", "theme_persona")
os.makedirs(V6_DIR, exist_ok=True)


def get_asset_analyst_affinity() -> dict[str, list[str]]:
    """Returns {analyst_lower: [asset_id, ...]} — which assets each analyst is recorded asking about."""
    out = defaultdict(list)
    for fn in sorted(os.listdir(ASSET_DIR)):
        if not fn.endswith(".json"):
            continue
        asset = json.load(open(os.path.join(ASSET_DIR, fn)))
        asset_id = asset.get("asset_id", fn.replace(".json", ""))
        # asked_by_history may be in different structures from different sub-agents
        ar = asset.get("analyst_relevance", {})
        history = ar.get("asked_by_history", [])
        seen_analysts = set()
        for entry in history:
            if isinstance(entry, dict):
                a = (entry.get("analyst") or "").lower().strip()
                if a:
                    seen_analysts.add(a)
        # Also try alternative shapes
        for alt_key in ["analyst_engagement_profile", "all_analysts_mentioning"]:
            v = asset.get(alt_key)
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        seen_analysts.add(item.lower().strip())
                    elif isinstance(item, dict) and "analyst" in item:
                        seen_analysts.add((item["analyst"] or "").lower().strip())
        for a in seen_analysts:
            if a and a not in ("operator", ""):
                out[a].append(asset_id)
    return dict(out)


def get_theme_analyst_affinity() -> dict[str, list[str]]:
    """Returns {analyst_lower: [(theme_id, framing_text), ...]}"""
    out = defaultdict(list)
    for fn in sorted(os.listdir(THEME_DIR)):
        if not fn.endswith(".json"):
            continue
        theme = json.load(open(os.path.join(THEME_DIR, fn)))
        theme_id = theme.get("theme_id", fn.replace(".json", ""))
        aff = theme.get("analyst_affinity", {})
        if isinstance(aff, dict):
            for a, framing in aff.items():
                out[a.lower().strip()].append({"theme_id": theme_id, "framing": framing})
    return dict(out)


def refactor_one(v5_path: str, asset_aff: dict, theme_aff: dict) -> dict:
    """Build v6 from v5 + asset/theme affinity lookups."""
    v5 = json.load(open(v5_path))
    name = os.path.basename(v5_path).replace(".json", "").replace("_", " ")
    name_lower = name.lower()

    # Keep V5 identity / behavioral fields
    v6 = {
        "analyst_name": name,
        "coverage_profile": v5.get("coverage_profile", {}),
        "reasoning_style": v5.get("reasoning_style", {}),
        # Drop recurring_concerns.core_topics; keep blind_spots + stance_drift
        "blind_spots": (v5.get("recurring_concerns") or {}).get("blind_spots", ""),
        "stance_drift": (v5.get("recurring_concerns") or {}).get("stance_drift", ""),
        # v5 additions
        "queue_behavior": v5.get("queue_behavior", {}),
        "cross_analyst_reactivity": v5.get("cross_analyst_reactivity", {}),
        # NEW v6 cross-references to Layer 2/3
        "engages_assets": sorted(asset_aff.get(name_lower, [])),
        "engages_themes": [t["theme_id"] for t in theme_aff.get(name_lower, [])],
        "framing_overrides_by_theme": {
            t["theme_id"]: t["framing"] for t in theme_aff.get(name_lower, []) if t.get("framing")
        },
        # Provenance
        "_built_from": "v5 + asset/theme cross-references",
        "_v5_source": v5_path.replace(ROOT + "/", ""),
    }
    return v6


def main():
    asset_aff = get_asset_analyst_affinity()
    theme_aff = get_theme_analyst_affinity()
    print(f"Asset affinity: {sum(len(v) for v in asset_aff.values())} (analyst, asset) edges across {len(asset_aff)} analysts")
    print(f"Theme affinity: {sum(len(v) for v in theme_aff.values())} (analyst, theme) edges across {len(theme_aff)} analysts")

    n_written = 0
    for fn in sorted(os.listdir(V5_DIR)):
        if not fn.endswith(".json"):
            continue
        v5_path = os.path.join(V5_DIR, fn)
        v6 = refactor_one(v5_path, asset_aff, theme_aff)
        out_path = os.path.join(V6_DIR, fn)
        with open(out_path, "w") as f:
            json.dump(v6, f, indent=2)
        size_v5 = os.path.getsize(v5_path)
        size_v6 = os.path.getsize(out_path)
        n_assets = len(v6["engages_assets"])
        n_themes = len(v6["engages_themes"])
        print(f"  {fn:30s} v5={size_v5//100/10}KB → v6={size_v6//100/10}KB  assets={n_assets} themes={n_themes}")
        n_written += 1
    print(f"\nWrote {n_written} v6 personas to {V6_DIR}")


if __name__ == "__main__":
    main()
