"""Deterministic trigger-type ("probe type") tagger for analyst questions.

Tags a single question string with a subset of the 7 trigger types the v7 spec
tracks:

  DELTA        — tracks change vs the prior call (guide moved, cadence, bridge)
  UNQUANTIFIED — the generic "put a number / bps on it" quantification reflex
  CLAIM        — tests a management qualitative assertion ("you said X — is that…")
  ANNOUNCEMENT — probes a newly announced item (new asset / program / deal)
  EXTERNAL     — macro / consumer / competitive / geopolitical
  PERSONA      — strategist / big-picture / multi-year / market-share framing
  CHAIN        — builds on a prior analyst or an earlier answer (follow-up)

Also exposes ``strip_greeting`` — greeting/congrats boilerplate badly
contaminates similarity and probe-type scoring (Boss's raw persona-match was
0.93 purely on "congrats"), so callers strip it before tagging.

This module is import-only (no side effects) so build_persona_v7 and the
generator/eval can share one tagger.
"""

from __future__ import annotations

import re

TRIGGER_TYPES = [
    "DELTA", "UNQUANTIFIED", "CLAIM", "ANNOUNCEMENT", "EXTERNAL", "PERSONA", "CHAIN",
]

CUES: dict[str, list[str]] = {
    "DELTA": [
        "versus last", "vs last", "vs. last", "compared to last", "from last quarter",
        "since the last call", "since last call", "relative to your prior", "prior guide",
        "previous guide", "moved", "changed", "change in", "raised", "lowered", "updated",
        "revised", "step up", "step-up", "deceleration", "acceleration", "sequential",
        "quarter-over-quarter", "quarter over quarter", "cadence", "bridge", "walk",
        "delta", "uptick", "came down", "came up", "trajectory", "ramp",
    ],
    "UNQUANTIFIED": [
        "how much", "how many", "quantify", "quantification", "bps", "basis points",
        "magnitude", "can you size", "size of", "order of magnitude", "ballpark",
        "roughly how", "what level", "what's the number", "how big", "how large",
        "what kind of number", "put a number", "how do we size",
    ],
    "CLAIM": [
        "you said", "you mentioned", "you talked about", "you noted", "you called out",
        "you described", "you indicated", "is that", "does that mean", "fair to say",
        "what gives you confidence", "how confident", "what's driving", "what is driving",
        "what underpins", "sustainable", "sustainability", "how durable", "is it right",
        "you characterized", "you framed",
    ],
    "ANNOUNCEMENT": [
        "you announced", "the announcement", "just announced", "newly announced",
        "the new ", "launching", "launch of", "the deal", "acquisition", "partnership",
        "you unveiled", "recently announced", "the recent announcement", "rolling out",
    ],
    "EXTERNAL": [
        "macro", "macroeconomic", "economy", "recession", "consumer", "geopolit",
        "tariff", "fx", "currency", "interest rate", "land-based", "land based",
        "competitor", "competitive", "supply", "inflation", "demand environment",
        "share of wallet", "wallet", "discretionary",
    ],
    "PERSONA": [
        "multi-year", "multiyear", "long-term", "long term", "longer term", "strateg",
        "market share", "tam", "total addressable", "structural", "over time",
        "framework", "philosophy", "moat", "inning", "runway", "vision", "big picture",
        "durable", "secular", "the next chapter", "where do you see", "five years",
        "white space", "portfolio",
    ],
    "CHAIN": [
        "following up", "follow up", "follow-up", "to follow", "as a follow",
        "back to", "circle back", "go back to", "building on", "you mentioned earlier",
        "earlier you", "your earlier", "to the prior question", "piggyback",
    ],
}

# Greeting / congrats boilerplate stripped before tagging.
_GREETING_PATTERNS = [
    r"^(hi|hey|hello|good morning|good afternoon|good evening|morning|afternoon|thanks|thank you|great|okay|ok|yeah|yes)\b[^.?!]*[.?!]",
    r"\b(congrat\w*|congratulations|nice quarter|great quarter|solid quarter|good quarter|nice results|great results)\b[^.?!]*[.?!]?",
    r"^(thanks (?:for|so much)[^.?!]*[.?!])",
]


def strip_greeting(text: str) -> str:
    """Remove leading greeting/congrats clauses. Idempotent-ish; conservative
    (only strips clause-leading boilerplate, not body content)."""
    s = (text or "").strip()
    changed = True
    while changed and s:
        changed = False
        for pat in _GREETING_PATTERNS:
            new = re.sub(pat, "", s, count=1, flags=re.I).strip()
            if new != s:
                s = new
                changed = True
    return s or (text or "").strip()


def tag_question(text: str, *, strip: bool = True) -> set[str]:
    """Return the set of trigger types whose cues appear in ``text``."""
    s = strip_greeting(text) if strip else (text or "")
    low = s.lower()
    matched = set()
    for ttype, cues in CUES.items():
        if any(c in low for c in cues):
            matched.add(ttype)
    return matched


def _segments(text: str) -> list[str]:
    return [seg for seg in re.split(r"[.?!]+", text) if seg.strip()]


def trajectory_length(text: str, *, strip: bool = True) -> int:
    """Proxy for hook->payload distance: number of sentence segments in the
    greeting-stripped question. Short (1-2) = drill the number; long (3+) =
    springboard to strategy."""
    s = strip_greeting(text) if strip else (text or "")
    return len(_segments(s))


def trajectory_label(n: float) -> str:
    if n <= 1.5:
        return "short"
    if n <= 2.7:
        return "medium"
    return "long"


def profile_questions(questions: list[str]) -> dict:
    """Tag a list of questions and return a probe_type_profile dict:
      distribution over the 7 types (normalized to sum 1 over tag hits),
      primary type, coverage, mean trajectory length + label.
    """
    counts = {t: 0 for t in TRIGGER_TYPES}
    n_tagged = 0
    traj_vals = []
    for q in questions:
        tags = tag_question(q)
        if tags:
            n_tagged += 1
        for t in tags:
            counts[t] += 1
        traj_vals.append(trajectory_length(q))
    total = sum(counts.values())
    dist = {t: round(counts[t] / total, 4) for t in TRIGGER_TYPES} if total else \
        {t: 0.0 for t in TRIGGER_TYPES}
    primary = max(dist, key=dist.get) if total else None
    mean_traj = round(sum(traj_vals) / len(traj_vals), 2) if traj_vals else 0.0
    return {
        "distribution": dist,
        "raw_counts": counts,
        "primary": primary,
        "n_questions": len(questions),
        "n_tagged": n_tagged,
        "trajectory_length": mean_traj,
        "trajectory_label": trajectory_label(mean_traj),
    }


if __name__ == "__main__":  # tiny smoke test
    samples = [
        "Great, congrats on the quarter. How should we think about the multi-year market share opportunity versus land-based?",
        "Thanks. Your net yield guide moved from 1.5-3.5 to 1.5-2.5 — what changed quarter over quarter?",
        "Can you quantify the bps of cost from dry dock?",
    ]
    for s in samples:
        print(tag_question(s), "| traj=", trajectory_length(s), "|", strip_greeting(s)[:60])
