"""Build reports/actual_vs_predicted_by_analyst.md — no judge, just the texts.

For each analyst on the 2026-Q1 holdout: their REAL question(s), followed by the
predicted candidate questions from each twin version (v1, v5, v6, auto), pulled
from the committed K=10 / gpt-5 / run_1 predicted pools. v7 (DRY_RUN stub) is
appended separately and labeled as not a live run.

Usage:
  python3 src/build_actual_vs_predicted_doc.py
"""

from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
DA = os.path.join(ROOT, "data_auto")
OUT = os.path.join(ROOT, "reports", "actual_vs_predicted_by_analyst.md")

# version -> committed run_1 raw_pool.json (K=10, judge gpt-5)
POOLS = {
    "v1": "final_eval_10q_v1/v5_compare/gpt-5/run_1/raw_pool.json",
    "v5": "final_eval_10q_v5/v5_compare/gpt-5/run_1/raw_pool.json",
    "v6": "final_eval_10q_v6/variance/run_1/raw_pool.json",
    "auto": "final_eval_10q_auto/v5_compare/gpt-5/run_1/raw_pool.json",
}
# v7 DRY_RUN stub (K=3, persona-conditioned)
V7_POOL = "final_eval_3q_v7/run_1/raw_pool.json"


def load_predicted(path: str) -> dict[str, list[dict]]:
    d = json.load(open(os.path.join(DA, path)))
    out: dict[str, list[dict]] = {}
    for p in d["predicted"]:
        out.setdefault(p["source_analyst"], []).append(p)
    return out


def main() -> None:
    test = json.load(open(os.path.join(DATA, "analysts_test.json")))
    actuals = test["per_analyst_actual_questions"]
    pools = {v: load_predicted(p) for v, p in POOLS.items()}
    v7 = load_predicted(V7_POOL)

    lines: list[str] = []
    lines.append("# Actual vs predicted questions — by analyst (2026-Q1)")
    lines.append("")
    lines.append("No judge applied — raw texts only. Predicted candidates are the **K=10** "
                 "pools (judge config gpt-5, seed run_1) for v1/v5/v6/auto. v7 is the "
                 "**DRY_RUN stub** (K=3, not a live model run) shown for shape only.")
    lines.append("")
    lines.append(f"Source pools: " + ", ".join(f"`{v}`=`data_auto/{p}`" for v, p in POOLS.items()))
    lines.append("")
    lines.append("---")
    lines.append("")

    for analyst in actuals:
        lines.append(f"## {analyst}")
        lines.append("")
        # actual question(s)
        lines.append("**Actual question(s):**")
        lines.append("")
        for i, a in enumerate(actuals[analyst]):
            lines.append(f"> **[A{i}]** {' '.join(a['question'].split())}")
            lines.append("")
        # predicted per version
        for v in POOLS:
            preds = pools[v].get(analyst, [])
            lines.append(f"**Predicted — {v}** ({len(preds)} candidates):")
            lines.append("")
            if not preds:
                lines.append("_(none)_")
                lines.append("")
                continue
            for j, p in enumerate(preds):
                topic = p.get("topic_label", "")
                tag = f" _({topic})_" if topic else ""
                lines.append(f"{j+1}. {' '.join(p['question'].split())}{tag}")
            lines.append("")
        # v7 stub
        v7p = v7.get(analyst, [])
        if v7p:
            lines.append(f"**Predicted — v7 (DRY_RUN stub)** ({len(v7p)} candidates):")
            lines.append("")
            for j, p in enumerate(v7p):
                hk = p.get("hook_id", "")
                tag = f" _(hook={hk})_" if hk else ""
                lines.append(f"{j+1}. {' '.join(p['question'].split())}{tag}")
            lines.append("")
        lines.append("---")
        lines.append("")

    with open(OUT, "w") as fp:
        fp.write("\n".join(lines))
    print(f"wrote {OUT}  ({len(actuals)} analysts)")


if __name__ == "__main__":
    main()
