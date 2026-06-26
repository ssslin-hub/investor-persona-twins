#!/usr/bin/env python3
"""
Deterministic, deletion-only denoiser for spoken analyst questions.

Design principles
-----------------
1. DELETION ONLY. This pass never rewords, reorders, merges, or paraphrases.
   It only removes spans matched by an explicit, auditable rule set. Anything
   that needs judgment (restructuring a rambling multi-part question into a
   crisp one) is left for a downstream LLM pass.

2. NEVER TOUCH FACTS. Numbers, percentages, bps, $ amounts, and quarter tags
   (e.g. 2026-Q1, "third quarter") are never inside a deletion rule. A built-in
   check confirms the multiset of numeric/quarter tokens is identical before
   and after — if it isn't, the script flags the row instead of trusting it.

3. CONSERVATIVE. When in doubt, keep. Better to leave a filler in (the LLM
   pass will catch it) than to risk deleting meaning. Every deletion is logged
   so you can audit exactly what each rule removed.

Usage
-----
    python3 denoise_questions.py data/analysts_test.json --out cleaned.json

Optional disfluency model (context-aware, heavier) — see disfluency_model_clean()
at the bottom; off by default so this runs with zero extra dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys


# ---------------------------------------------------------------------------
# Rule set. Order matters: greetings first, then discourse fillers, then
# hedge openers, then stutters, then whitespace/punctuation cleanup.
# Each pattern is case-insensitive and only ever DELETES (replaces with "").
# ---------------------------------------------------------------------------

# (1) Leading greeting / thanks / congrats clauses (clause-leading only).
GREETING_PATTERNS = [
    r"^\s*(?:yeah|yep|okay|ok|sure|great|alright)[\s,.\-]+",
    r"^\s*(?:hi|hey|hello|good\s+morning|good\s+afternoon|good\s+evening|morning|afternoon)\b[^.?!]*[.?!]\s*",
    r"^\s*thanks(?:\s+(?:so much|a lot|for (?:taking|all)[^.?!]*))?[.?!,]\s*",
    r"^\s*thank you(?:\s+(?:so much|very much))?[^.?!]*[.?!]\s*",
    r"\b(?:congrats?|congratulations|nice quarter|great quarter|solid quarter|good quarter|nice results|great results)\b[^.?!]*[.?!]?",
    r"\bthanks for (?:taking|all)[^.?!]*[.?!]",
]

# (2) Interstitial discourse fillers — only removed when clearly parenthetical
#     (bounded by commas/spaces). We do NOT remove bare "like"/"right" (too risky).
FILLER_PATTERNS = [
    r"(?<=\W)you know,?\s*",          # "..., you know, ..."
    r"(?<=\W)i guess,?\s*",
    r"(?<=\W)i mean,?\s*",
    r"(?<=\W)i think,?\s*",
    r"(?<=\W)sort of\s+",
    r"(?<=\W)kind of\s+",
    r"(?<=\W)kinda\s+",
    r"(?<=\W)obviously,?\s*",
    r"(?<=\W)basically,?\s*",
    r"(?<=\W)essentially,?\s*",
    r"(?<=\W)actually,?\s*",
    r"(?<=\W)just curious,?\s*",
    r"(?<=\W)if you will\b,?\s*",
    r"(?<=\W)so to speak\b,?\s*",
    r"(?<=\W)i don'?t know,?\s*",     # "say, I don't know, 2%-3%" -> careful, see note
]

# (3) Hedge openers that add no information ("I wanted to ask...", "I was
#     wondering if you could..."). These delete the wrapper, keeping the ask.
HEDGE_PATTERNS = [
    r"\bi (?:just\s+)?wanted to (?:ask|sort of\s+)?(?:zoom in on|dig (?:a little bit\s+)?(?:more\s+)?into|circle back on|follow up on|touch on|get into|understand)\b\s*",
    r"\bi was wondering if you could\b\s*",
    r"\bi (?:just\s+)?had a (?:quick\s+)?question (?:on|about)\b\s*",
    r"\bcan you (?:talk (?:at all\s+)?(?:about|to)|comment on|speak to)\b\s*",
    r"\bmaybe (?:if you could|you could|just)\b\s*",
    r"\bcould you maybe\b\s*",
    r"\bjust wanted to\b\s*",
]

# (4) Word-level stutters / immediate repeats: "the the", "you you", "on on".
STUTTER_PATTERN = re.compile(r"\b(\w+)(\s+\1\b){1,3}", re.I)

# Numbers / quarters we must preserve. Used only by the verifier, never deleted.
NUM_TOKEN_RE = re.compile(
    r"""(?ix)
    \$?\d+(?:[.,]\d+)?\s*%?            # 5, 2.5, 2.5%, $120, 1,000
    |\b\d+\s*(?:bps|basis points)\b
    |\b20\d\d\s*[-\s]?q[1-4]\b         # 2026-Q1, 2026 Q1
    |\bq[1-4]\b
    |\b(?:first|second|third|fourth)\s+quarter\b
    |\b20\d\d\b
    """,
)


def _apply(patterns, text, log):
    for pat in patterns:
        def _sub(m):
            log.append(m.group(0))
            return " "
        text = re.sub(pat, _sub, text, flags=re.I)
    return text


def denoise(text: str) -> tuple[str, list[str]]:
    """Return (cleaned_text, removed_spans)."""
    removed: list[str] = []
    s = text

    s = _apply(GREETING_PATTERNS, s, removed)
    s = _apply(FILLER_PATTERNS, s, removed)
    s = _apply(HEDGE_PATTERNS, s, removed)

    # stutters
    def _destutter(m):
        removed.append(m.group(0))
        return m.group(1)
    s = STUTTER_PATTERN.sub(_destutter, s)

    # whitespace + punctuation tidy (no semantic change).
    # NB: deliberately do NOT insert a space after punctuation — that would
    # corrupt decimals like "2.5%". Only fix spaces BEFORE punctuation, but
    # never when the punctuation sits between digits (e.g. "2 . 5" stays safe
    # because we require a non-digit before the space).
    s = re.sub(r"(?<=\D)\s+([,.?!;:])", r"\1", s)  # space before punct (not in numbers)
    s = re.sub(r"\s{2,}", " ", s)             # collapse spaces
    s = re.sub(r",\s*,", ", ", s)             # double commas from deletions
    s = re.sub(r"(^[\s,.;:-]+)|([\s,]+$)", "", s)  # trim edges
    # Re-capitalize sentence starts that a mid-sentence deletion lowercased.
    s = re.sub(r"(^|[.?!]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), s)

    return s, removed


def numbers_preserved(before: str, after: str) -> tuple[bool, list, list]:
    """Check the multiset of numeric/quarter tokens is unchanged."""
    def toks(t):
        return sorted(m.group(0).lower().replace(" ", "") for m in NUM_TOKEN_RE.finditer(t))
    b, a = toks(before), toks(after)
    return (b == a, b, a)


def process_test_file(path: str):
    data = json.load(open(path))
    out = []
    blocks = data.get("per_analyst_actual_questions", {})
    for analyst, records in blocks.items():
        for i, r in enumerate(records):
            q = r.get("question", "")
            cleaned, removed = denoise(q)
            ok, b, a = numbers_preserved(q, cleaned)
            out.append({
                "analyst": analyst,
                "idx": i,
                "original": q,
                "cleaned": cleaned,
                "removed": removed,
                "numbers_preserved": ok,
                "orig_len": len(q.split()),
                "clean_len": len(cleaned.split()),
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile", help="path to analysts_test.json")
    ap.add_argument("--out", default="cleaned_questions.json")
    args = ap.parse_args()

    results = process_test_file(args.infile)
    json.dump(results, open(args.out, "w"), indent=2, ensure_ascii=False)

    flagged = [r for r in results if not r["numbers_preserved"]]
    tot_o = sum(r["orig_len"] for r in results)
    tot_c = sum(r["clean_len"] for r in results)
    print(f"processed {len(results)} questions -> {args.out}")
    print(f"avg compression: {tot_o} -> {tot_c} words ({100*(1-tot_c/tot_o):.0f}% shorter)")
    print(f"number-preservation failures: {len(flagged)}")
    for r in flagged:
        print(f"  !! {r['analyst']} #{r['idx']} — review manually")


# ---------------------------------------------------------------------------
# OPTIONAL: context-aware disfluency model (heavier, needs torch+transformers).
# Uncomment and `pip install transformers torch` to use instead of/after regex.
# A Switchboard-trained token classifier labels each token fluent/disfluent.
# ---------------------------------------------------------------------------
def disfluency_model_clean(text: str):  # pragma: no cover
    """Example hook. Returns text with model-detected disfluent tokens dropped.
    Pick any HF token-classification disfluency model, e.g. a BERT fine-tuned on
    Switchboard. Kept off by default so the regex path needs no dependencies."""
    from transformers import pipeline  # lazy import
    clf = pipeline("token-classification",
                   model="<a-switchboard-disfluency-model>",
                   aggregation_strategy="simple")
    spans = clf(text)
    # drop spans labeled as disfluency; keep everything else verbatim
    drop = [(s["start"], s["end"]) for s in spans if s["entity_group"] == "DISFLUENCY"]
    keep, last = [], 0
    for st, en in sorted(drop):
        keep.append(text[last:st]); last = en
    keep.append(text[last:])
    return re.sub(r"\s{2,}", " ", "".join(keep)).strip()


if __name__ == "__main__":
    sys.exit(main())
