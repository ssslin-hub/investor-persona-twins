"""Phase B — Company qualitative narrative layer (RCL).

For each call's prepared remarks, produce a structured
``qualitative_narrative_by_quarter[q]`` with:
  - demand_environment
  - consumer_health
  - competitive_positioning
  - notable_claims  (vague qualitative assertions — "record wave", "consumer
                     remains healthy" — the hooks for CLAIM / demand / consumer
                     questions)

Source = prepared remarks ONLY (leakage guardrail §6). Per §11 this stage is
Opus-quality; it routes through llm_client.call_llm so that DRY_RUN=1 returns a
deterministic, keyword-seeded stub (no API cost). Flip DRY_RUN to run the real
model later.

Usage:
  DRY_RUN=1 python3 src/build_qual_narrative.py        # deterministic stub
  python3 src/build_qual_narrative.py                  # live (needs OPENAI_API_KEY)
  python3 src/build_qual_narrative.py --dry            # build + print, no write
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
from llm_client import call_llm, parse_json_strict  # noqa: E402

RCL_JSON = os.path.join(ROOT, "data", "company_persona", "rcl.json")
TRANSCRIPTS = os.path.join(ROOT, "transcripts")

# Phrases that flag a vague, probe-able management claim.
CLAIM_CUES = [
    "record", "strong", "healthy", "robust", "momentum", "turned a corner",
    "best", "highest", "accelerat", "resilient", "outperform", "exceeded",
    "ahead of", "all-time", "wave", "demand remains", "consumer remains",
    "better than expected", "unprecedented", "continue to see",
]
DEMAND_CUES = ["demand", "booking", "book position", "wave season", "close-in", "load factor"]
CONSUMER_CUES = ["consumer", "onboard spend", "spending", "value gap", "discretionary"]
COMPETE_CUES = ["land-based", "market share", "share of wallet", "competitor", "vacation", "versus"]


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if len(s.strip()) > 25]


def _matching(sentences: list[str], cues: list[str], limit: int) -> list[str]:
    out = []
    seen = set()
    for s in sentences:
        low = s.lower()
        if any(c in low for c in cues):
            key = low[:80]
            if key in seen:
                continue
            seen.add(key)
            out.append(s if len(s) <= 240 else s[:237] + "...")
        if len(out) >= limit:
            break
    return out


def deterministic_stub(pres: str, quarter: str) -> dict:
    sents = _sentences(pres)
    return {
        "demand_environment": _matching(sents, DEMAND_CUES, 3),
        "consumer_health": _matching(sents, CONSUMER_CUES, 3),
        "competitive_positioning": _matching(sents, COMPETE_CUES, 2),
        "notable_claims": _matching(sents, CLAIM_CUES, 5),
        "_source": "deterministic_stub",
    }


PROMPT_TEMPLATE = """You are summarizing the PREPARED REMARKS of the Royal Caribbean Group (RCL) {quarter} earnings call into a structured qualitative narrative. Use ONLY the prepared remarks below — do not infer from anything else.

Extract four fields. Each should be a short list of concise strings (verbatim or lightly paraphrased), capturing the management narrative an analyst would probe:
  - demand_environment: statements about demand, bookings, wave season, load factors, booked position.
  - consumer_health: statements about the consumer, onboard spend, value gap, discretionary spending.
  - competitive_positioning: statements about land-based vacations, market share, share of wallet.
  - notable_claims: the vague, qualitative assertions ("record wave", "consumer remains healthy", "turned a corner") that an analyst is likely to press management to substantiate.

PREPARED REMARKS ({quarter}):
{pres}

Output strictly this JSON object, no prose:
{
  "demand_environment": ["..."],
  "consumer_health": ["..."],
  "competitive_positioning": ["..."],
  "notable_claims": ["..."]
}
"""


def _fill(template: str, **kw) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def get_presentation(path: str) -> str:
    rec = parse_transcript(path)
    pres = " ".join(t["text"] for t in rec.get("presentation_turns", []))
    if len(pres) < 500:
        lines = html_to_lines(path)
        turns = parse_turns(lines)
        p, _ = split_call(turns)
        pres = " ".join(t.text for t in p)
    return pres


def build_narrative(path: str, quarter: str, log_dir: str) -> dict:
    pres = get_presentation(path)
    stub = deterministic_stub(pres, quarter)
    prompt = _fill(PROMPT_TEMPLATE, quarter=quarter, pres=pres[:12000])
    out = call_llm(
        prompt,
        expect_json=True,
        dry_run_stub=stub,
        log_to=os.path.join(log_dir, f"qual_{quarter}.txt"),
    )
    try:
        narrative = parse_json_strict(out)
    except Exception as e:  # noqa: BLE001
        print(f"[{quarter}] parse error: {e}; using deterministic stub")
        narrative = stub
    narrative.setdefault("_source", "llm")
    return narrative


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="build + print, do not write")
    args = ap.parse_args()

    rcl = json.load(open(RCL_JSON))
    log_dir = os.path.join(ROOT, "data", "prompt_logs")
    os.makedirs(log_dir, exist_ok=True)

    files = sorted(f for f in os.listdir(TRANSCRIPTS) if f.endswith(".html"))
    narratives: dict[str, dict] = {}
    for fn in files:
        m = re.match(r"(\d{4})-q(\d)-", fn)
        quarter = f"{m.group(1)}-Q{m.group(2)}"
        narratives[quarter] = build_narrative(os.path.join(TRANSCRIPTS, fn), quarter, log_dir)
        n_claims = len(narratives[quarter].get("notable_claims", []))
        print(f"  {quarter}: {n_claims} notable_claims  (source={narratives[quarter]['_source']})")

    rcl["qualitative_narrative_by_quarter"] = narratives
    if args.dry:
        print("\n[--dry] not writing rcl.json")
        return
    with open(RCL_JSON, "w") as fp:
        json.dump(rcl, fp, indent=2)
    print(f"\nwrote {RCL_JSON}")


if __name__ == "__main__":
    main()
