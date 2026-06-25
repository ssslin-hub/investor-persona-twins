"""Parse peer-company earnings call transcripts in peer_cache/ into analyst
question turns, tag with ticker + sector, and merge with the existing RCL
training data to produce data_auto/train_combined.json.

Filters:
- Only peer quarters <= 2025-Q2 (excludes 2025-Q3, 2025-Q4, 2026-Q1 to avoid
  forward leakage into CAL/TEST).
- Only the 11 CAL-eligible analysts (the rest of the peer analyst pool is
  out of scope for this run).

Output record shape per turn (matches run_pipeline.build_question_history_block
plus ticker / sector tags):
  {
    "call": "2024-Q1",
    "ticker": "CCL",
    "sector": "cruise",
    "context": "[PRESENTATION]\n...\n[Q&A SO FAR]\n...",
    "operator_intro": "",
    "question": "<verbatim>",
    "response": "<verbatim, truncated>",
    "affiliation": "Analyst, Mizuho Securities"
  }
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from parse_transcripts import html_to_lines  # noqa: E402

PEER_CACHE = os.path.join(ROOT, "peer_cache")
OUT_DIR = os.path.join(ROOT, "data_auto")
os.makedirs(OUT_DIR, exist_ok=True)

TICKERS = {
    "ccl": ("CCL", "cruise"),
    "nclh": ("NCLH", "cruise"),
    "mar": ("MAR", "lodging"),
    "hlt": ("HLT", "lodging"),
    "h": ("H", "lodging"),
}

# Peer calls <= 2025-Q2 only (chronological cutoff to match RCL TRAIN).
# Allowed quarter labels (the peer_cache filenames are <tk>_q<n>-<year>.html).
def quarter_allowed(label: str) -> bool:
    # label like "q1-2026"
    m = re.match(r"q([1-4])-(\d{4})", label)
    if not m:
        return False
    q = int(m.group(1))
    y = int(m.group(2))
    # Allow up to and including 2025-Q2
    if y < 2025:
        return True
    if y == 2025 and q <= 2:
        return True
    return False


CAL_ELIGIBLE_ANALYSTS = {
    "matthew boss",
    "steven wieczynski",
    "brandt montour",
    "james hardiman",
    "lizzie dove",
    "robin farley",
    "conor cunningham",
    "david katz",
    "vince ciepiel",
    "sharon zackfia",
    "andrew didora",
}

NICKNAMES = {
    "dan": "daniel",
    "ben": "benjamin",
    "joe": "joseph",
    "matt": "matthew",
    "steve": "steven",
    "chris": "christopher",
    "mike": "michael",
    "jamie": "james",
    "tony": "anthony",
    "andy": "andrew",
    "dave": "david",
    "jim": "james",
    "tom": "thomas",
}


def canon_name(raw: str) -> str:
    n = re.sub(r"\s+", " ", raw or "").strip().lower().rstrip(".,")
    toks = [t for t in n.split() if not re.match(r"^[a-z]\.?$", t)]
    if len(toks) >= 2:
        first = NICKNAMES.get(toks[0], toks[0])
        last = toks[-1]
        n = f"{first} {last}"
    return n


OPERATOR_NAMES = {"operator", "moderator"}
PLEASANTRIES = {
    "thank you", "thanks", "got it", "great", "okay", "ok", "sure",
    "yes", "no", "right", "moving to guidance", "moving on",
    "that's helpful", "thanks for taking my question",
    "thanks for the question",
}


def looks_like_name(name: str) -> bool:
    if not (1 <= name.count(" ") <= 4):
        return False
    if name.lower() in OPERATOR_NAMES:
        return False
    if name.rstrip(".").lower() in PLEASANTRIES:
        return False
    return bool(re.match(r"^([A-Z][a-zA-Z'\-]*\.?\s)+[A-Z][a-zA-Z'\-]+$", name))


CORP_FIRM_TOKENS = (
    "royal caribbean", "carnival", "norwegian cruise", "marriott",
    "hilton", "hyatt", "investor relations", "corporate communications",
    "corporate development", "fp&a", "fp a", "white lodging", "ir ",
)


def looks_like_analyst_title(title: str) -> bool:
    if "," not in title or len(title) > 200:
        return False
    low = title.lower()
    firm = title.split(",", 1)[1].strip().lower()
    # Reject anything that looks like in-house IR / management
    if any(tok in firm for tok in CORP_FIRM_TOKENS):
        return False
    if any(tok in low for tok in ("ceo", "cfo", "chief financial",
                                   "chief executive", "treasurer")):
        return False
    # Accept any sell-side-y title
    return any(k in low for k in (
        "analyst", "research", "vp", "head", "partner", "director",
        "managing director", "associate", "equity", "investment officer",
    ))


def find_qa_start(lines: list[str]) -> int | None:
    for i, l in enumerate(lines):
        low = l.lower()
        if "first question" in low:
            return i
        if "q&a" in low or "questions and answers" in low or "question-and-answer" in low:
            return i
    return None


def walk_turns(lines: list[str], qa_start: int) -> list[dict]:
    """Walk the Q&A region and emit speaker turns.

    A 'turn' = a contiguous block of utterance lines whose preceding 2 lines
    are (name, title). Operator turns are dropped.
    """
    n = len(lines)
    i = qa_start
    turns: list[dict] = []
    while i < n - 1:
        name = lines[i].strip()
        title = lines[i + 1].strip() if i + 1 < n else ""
        # Speaker header: name looks like person name AND title contains comma
        # (or this is the operator).
        if name.lower() in OPERATOR_NAMES:
            # operator: gobble utterance until next non-op speaker header
            utt_start = i + 1
            j = utt_start
            while j < n - 1:
                nm = lines[j].strip()
                tt = lines[j + 1].strip() if j + 1 < n else ""
                if (looks_like_name(nm) and "," in tt) or (nm.lower() in OPERATOR_NAMES and j > utt_start):
                    break
                j += 1
            turns.append({
                "speaker": "Operator", "title": "", "text": " ".join(lines[utt_start:j]).strip(),
            })
            i = j
            continue
        if looks_like_name(name) and "," in title:
            utt_start = i + 2
            j = utt_start
            while j < n - 1:
                nm = lines[j].strip()
                tt = lines[j + 1].strip() if j + 1 < n else ""
                if (looks_like_name(nm) and "," in tt) or nm.lower() in OPERATOR_NAMES:
                    break
                j += 1
            text = " ".join(lines[utt_start:j]).strip()
            turns.append({"speaker": name, "title": title, "text": text})
            i = j
            continue
        i += 1
    return turns


def make_presentation_excerpt(lines: list[str], qa_start: int, max_chars: int = 1500) -> str:
    """Compact presentation excerpt = last max_chars of pre-Q&A text."""
    text = " ".join(lines[:qa_start])
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return "..." + text[-(max_chars - 3) :]


def parse_peer_call(html_path: str, ticker: str, sector: str, quarter_label: str) -> list[dict]:
    """Return a list of records for analyst turns in this call."""
    lines = html_to_lines(html_path)
    qa_start = find_qa_start(lines)
    if qa_start is None:
        return []

    pres = make_presentation_excerpt(lines, qa_start)
    turns = walk_turns(lines, qa_start)
    records: list[dict] = []

    # Walk turns; for each analyst turn, find the next non-operator/non-analyst
    # turn as the management response.
    for k, t in enumerate(turns):
        if not looks_like_analyst_title(t["title"]):
            continue
        analyst_name = canon_name(t["speaker"])
        if analyst_name not in CAL_ELIGIBLE_ANALYSTS:
            continue
        # Build Q&A-so-far context: speakers + first ~80 chars of each prior turn
        qa_prev: list[str] = []
        for prev in turns[:k]:
            if not prev["text"]:
                continue
            sp = prev["speaker"]
            tx = prev["text"][:120]
            qa_prev.append(f"{sp}: {tx}")
        qa_prev_text = " | ".join(qa_prev)[-1200:]

        # Operator intro = nearest preceding operator turn before this analyst
        op_intro = ""
        for prev in reversed(turns[:k]):
            if prev["speaker"] == "Operator":
                op_intro = prev["text"][:300]
                break

        # Management response = first non-operator turn after this analyst
        # whose title is NOT analyst.
        resp = ""
        for nxt in turns[k + 1 :]:
            if nxt["speaker"] == "Operator":
                continue
            if looks_like_analyst_title(nxt["title"]):
                # Another analyst turn (rare) — stop
                break
            resp = nxt["text"][:600]
            break

        context = f"[PRESENTATION]\n{pres}\n\n[Q&A SO FAR]\n{qa_prev_text}"
        records.append({
            "call": f"{quarter_label[1]}-Q{quarter_label[0]}" if False else _normalize_quarter(quarter_label),
            "ticker": ticker,
            "sector": sector,
            "context": context,
            "operator_intro": op_intro,
            "question": t["text"],
            "response": resp,
            "affiliation": t["title"],
            "_analyst_name_lc": analyst_name,
        })
    return records


def _normalize_quarter(label: str) -> str:
    # input: 'q1-2024' -> '2024-Q1'
    m = re.match(r"q([1-4])-(\d{4})", label)
    if not m:
        return label
    return f"{m.group(2)}-Q{m.group(1)}"


# RCL calls to EXCLUDE from TRAIN — these become CAL.
RCL_CAL_CALLS = {"2025-Q3", "2025-Q4"}


def load_rcl_train() -> dict:
    """Load the existing RCL training data, tag each turn with
    ticker=RCL/sector=cruise, and DROP turns from 2025-Q3 + 2025-Q4 so they
    are reserved for CAL."""
    p = os.path.join(ROOT, "data", "analysts.json")
    d = json.load(open(p))
    for name, rec in d.items():
        kept = []
        for r in rec["records"]:
            if r.get("call") in RCL_CAL_CALLS:
                continue
            r.setdefault("ticker", "RCL")
            r.setdefault("sector", "cruise")
            kept.append(r)
        rec["records"] = kept
        rec["n_questions"] = len(kept)
    return d


def main() -> None:
    print("=== Building peer dataset ===")

    # 1. Parse peer cache
    peer_by_analyst: dict[str, list[dict]] = defaultdict(list)
    peer_call_count = 0
    peer_turn_count = 0
    for fn in sorted(os.listdir(PEER_CACHE)):
        if not fn.endswith(".html") or fn.endswith("_list.html"):
            continue
        m = re.match(r"([a-z]+)_(q\d-\d{4})\.html", fn)
        if not m:
            continue
        tk, qlabel = m.group(1), m.group(2)
        if tk not in TICKERS:
            continue
        if not quarter_allowed(qlabel):
            continue
        ticker, sector = TICKERS[tk]
        path = os.path.join(PEER_CACHE, fn)
        recs = parse_peer_call(path, ticker, sector, qlabel)
        peer_call_count += 1
        peer_turn_count += len(recs)
        for r in recs:
            an = r.pop("_analyst_name_lc")
            peer_by_analyst[an].append(r)

    print(f"  parsed {peer_call_count} peer calls (<=2025-Q2)")
    print(f"  extracted {peer_turn_count} analyst turns into {len(peer_by_analyst)} analysts")
    for an in sorted(peer_by_analyst):
        print(f"    {an:30s} +{len(peer_by_analyst[an])} peer turns")

    # 2. Merge with RCL training data
    rcl = load_rcl_train()
    print(f"\n  RCL train has {len(rcl)} analysts")

    # For each of the 11 CAL-eligible analysts, append peer turns (sorted by call).
    merged_extra = 0
    for an in CAL_ELIGIBLE_ANALYSTS:
        if an not in rcl:
            # Andrew Didora has only 1 RCL Q on 2025-Q3 → will exist in RCL data
            # but after we remove 2025-Q3 turns (CAL split), he'll have 0 RCL turns
            # remaining. Initialize an empty record so peer data can populate him.
            rcl[an] = {
                "analyst": an,
                "n_questions": 0,
                "affiliations_seen": [],
                "records": [],
            }
        existing = rcl[an]["records"]
        new_turns = peer_by_analyst.get(an, [])
        if not new_turns:
            print(f"  ! {an}: 0 peer turns (low coverage)")
            continue
        existing.extend(new_turns)
        # Re-sort by (call) chronologically. Call format is "YYYY-QN".
        def call_key(r: dict) -> tuple[int, int]:
            c = r.get("call", "0000-Q0")
            try:
                y, q = c.split("-Q")
                return (int(y), int(q))
            except Exception:
                return (0, 0)
        existing.sort(key=call_key)
        rcl[an]["records"] = existing
        rcl[an]["n_questions"] = len(existing)
        # Append peer firms to affiliations_seen
        peer_firms = sorted({r["affiliation"] for r in new_turns if r.get("affiliation")})
        affs = list(rcl[an].get("affiliations_seen") or [])
        for f in peer_firms:
            if f not in affs:
                affs.append(f)
        rcl[an]["affiliations_seen"] = affs
        merged_extra += len(new_turns)

    # 3. Write combined
    out_path = os.path.join(OUT_DIR, "train_combined.json")
    with open(out_path, "w") as f:
        json.dump(rcl, f, indent=2)
    print(f"\n  wrote {out_path}")
    print(f"  merged in +{merged_extra} peer turns across the 11 CAL-eligible analysts")

    # Summary table
    print("\n=== Per-analyst turn counts (RCL + peer merged) ===")
    print(f"{'analyst':30s} {'n_total':>8s}  ticker_breakdown")
    for an in sorted(CAL_ELIGIBLE_ANALYSTS):
        recs = rcl.get(an, {}).get("records", [])
        n = len(recs)
        tk_counts: dict[str, int] = defaultdict(int)
        for r in recs:
            tk_counts[r.get("ticker", "?")] += 1
        bd = ", ".join(f"{k}={v}" for k, v in sorted(tk_counts.items()))
        print(f"{an:30s} {n:>8d}  {bd}")


if __name__ == "__main__":
    main()
