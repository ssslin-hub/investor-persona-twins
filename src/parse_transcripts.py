"""Parse RCG earnings call HTML transcripts into structured speaker turns.

Each transcript follows the format:
  <Speaker Name>
  <Title/Firm>            (optional second line)
  <one or more utterance lines>
  <Next Speaker Name>
  ...

The Q&A section starts after a line containing "first question comes from"
(operator intro). We split the call into management presentation + Q&A,
then within Q&A we group speaker turns into (analyst, question, answer) triples.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from typing import Optional


# Speakers known to be on the company side; everything else in Q&A is treated
# as an external analyst/reporter.
COMPANY_SPEAKERS = {
    "Operator",
    "Moderator",
    "Michael McCarthy",
    "Jason Liberty",
    "Naftali Holtz",
    "Michael Bayley",
    "Laura Hodges",
    "Lisa Lutoff-Perlo",
}
# Anything we treat as the call-runner role (operator/moderator).
OPERATOR_ROLES = {"Operator", "Moderator"}

# Lines that show up as section markers; skip them when grouping turns.
SKIP_LINES = {
    "Earnings release",
    "Quarterly report",
    "Play Audio",
    "← View all transcripts",
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = False

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


def html_to_lines(path: str) -> list[str]:
    with open(path) as f:
        html = f.read()
    p = TextExtractor()
    p.feed(html)
    return p.parts


@dataclass
class Turn:
    speaker: str
    affiliation: Optional[str]
    text: str


def _looks_like_speaker_header(line: str) -> bool:
    """Heuristic: a speaker header is a short line (1-5 words, mostly Capitalized,
    no trailing punctuation typical of sentences).
    """
    if len(line) > 60:
        return False
    if line.endswith(('.', '?', '!', ',', ':', ';')):
        return False
    words = line.split()
    if not (1 <= len(words) <= 5):
        return False
    # Each word should start uppercase (allowing for "and", "of", initials, etc.)
    # but at least the first word must be Capitalized.
    if not words[0][0].isupper():
        return False
    cap_count = sum(1 for w in words if w[:1].isupper())
    return cap_count >= max(1, len(words) - 1)


def _looks_like_affiliation(line: str) -> bool:
    """Heuristic: contains a comma + a firm-ish word, or is a title line."""
    if len(line) < 5 or len(line) > 200:
        return False
    if line.endswith(('.', '?', '!')):
        return False
    keywords = (
        "CEO", "CFO", "COO", "President", "Officer", "Analyst", "Director",
        "VP", "Vice President", "Managing", "Equity", "Research", "Capital",
        "Securities", "Bank", "Partners", "Group", "Stifel", "Truist",
        "Citi", "Citigroup", "Wells Fargo", "Goldman", "Morgan", "JPMorgan",
        "Macquarie", "Mizuho", "Barclays", "Bernstein", "Deutsche",
        "Investor Relations", "Royal Caribbean", "Loop", "Tigress",
    )
    if "," in line and any(k.lower() in line.lower() for k in keywords):
        return True
    if any(line.startswith(k) for k in ("CEO", "CFO", "COO", "President", "VP",
                                       "Chairman", "Chief", "Managing")):
        return True
    return False


def parse_turns(lines: list[str]) -> list[Turn]:
    """Group consecutive utterance lines into speaker turns.

    A turn begins when we see a speaker-header line; the next line may be an
    affiliation (kept) or part of the utterance.
    """
    turns: list[Turn] = []
    i = 0
    current_speaker = None
    current_aff = None
    current_text: list[str] = []

    def flush():
        if current_speaker and current_text:
            turns.append(Turn(current_speaker, current_aff,
                              " ".join(current_text).strip()))

    while i < len(lines):
        line = lines[i]
        if line in SKIP_LINES:
            i += 1
            continue
        if _looks_like_speaker_header(line):
            # Commit previous turn
            flush()
            current_speaker = line
            current_aff = None
            current_text = []
            # Look at next line for affiliation
            if i + 1 < len(lines) and _looks_like_affiliation(lines[i + 1]):
                current_aff = lines[i + 1]
                i += 2
                continue
            i += 1
            continue
        # Otherwise, append to current turn
        if current_speaker is not None:
            current_text.append(line)
        i += 1

    flush()
    return turns


def is_company_speaker(t: Turn) -> bool:
    """True if a turn is from the company (operator, named exec, or any
    speaker whose affiliation mentions Royal Caribbean)."""
    if t.speaker in COMPANY_SPEAKERS:
        return True
    aff = (t.affiliation or "").lower()
    if "royal caribbean" in aff:
        return True
    # Common exec titles when the company name isn't in the affiliation.
    if any(k in aff for k in ("ceo,", "cfo,", "president,", "investor relations")):
        return True
    return False


def split_call(turns: list[Turn]) -> tuple[list[Turn], list[Turn]]:
    """Split turns into (presentation, qa).

    Q&A starts at the first operator turn that is immediately followed by an
    EXTERNAL (non-company) speaker. We identify company speakers by either the
    fixed name set or by affiliation matching "Royal Caribbean" / exec titles,
    which makes us robust to new IR/CEO appointments.
    """
    qa_open = None
    for i, t in enumerate(turns):
        if t.speaker not in OPERATOR_ROLES:
            continue
        if i + 1 < len(turns) and not is_company_speaker(turns[i + 1]):
            qa_open = i
            break
    if qa_open is None:
        return turns, []

    real_start = qa_open  # fallback
    for i in range(qa_open):
        t = turns[i]
        if t.speaker in OPERATOR_ROLES or is_company_speaker(t):
            real_start = i
            break
    return turns[real_start:qa_open], turns[qa_open:]


def extract_analyst_questions(qa_turns: list[Turn]) -> list[dict]:
    """Within the Q&A turns, find analyst turns and pair them with the
    immediately preceding operator intro (if any) and the company response
    (all consecutive company turns after it).
    """
    results: list[dict] = []
    n = len(qa_turns)
    for i, t in enumerate(qa_turns):
        if is_company_speaker(t):
            continue
        # External analyst speaking. Collect operator-intro firm name from
        # the prior operator turn if present.
        operator_intro = None
        for j in range(i - 1, max(-1, i - 4), -1):
            if qa_turns[j].speaker in OPERATOR_ROLES:
                operator_intro = qa_turns[j].text
                break
        # Collect company response: consecutive following company turns
        response_parts: list[str] = []
        for k in range(i + 1, n):
            nxt = qa_turns[k]
            if is_company_speaker(nxt) and nxt.speaker not in OPERATOR_ROLES:
                response_parts.append(f"{nxt.speaker}: {nxt.text}")
            elif nxt.speaker in OPERATOR_ROLES:
                break
            else:
                # Another analyst speaks (follow-up by same person handled below)
                if nxt.speaker == t.speaker:
                    # Same analyst follow-up: stop here; this is a new question turn.
                    break
                else:
                    break
        results.append({
            "analyst": t.speaker,
            "affiliation": t.affiliation,
            "operator_intro": operator_intro,
            "question": t.text,
            "response": "\n".join(response_parts),
        })
    return results


def parse_transcript(path: str) -> dict:
    lines = html_to_lines(path)
    turns = parse_turns(lines)
    pres, qa = split_call(turns)
    qs = extract_analyst_questions(qa)
    fname = os.path.basename(path)
    m = re.match(r"(\d{4})-q(\d)-", fname)
    year = int(m.group(1)) if m else None
    quarter = int(m.group(2)) if m else None
    return {
        "file": fname,
        "year": year,
        "quarter": quarter,
        "presentation_turns": [asdict(t) for t in pres],
        "qa_turns": [asdict(t) for t in qa],
        "analyst_questions": qs,
    }


def main(transcripts_dir: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(transcripts_dir) if f.endswith(".html"))
    summary = []
    for f in files:
        rec = parse_transcript(os.path.join(transcripts_dir, f))
        out_path = os.path.join(out_dir, f.replace(".html", ".json"))
        with open(out_path, "w") as fp:
            json.dump(rec, fp, indent=2)
        summary.append({
            "file": rec["file"],
            "year": rec["year"],
            "quarter": rec["quarter"],
            "n_presentation_turns": len(rec["presentation_turns"]),
            "n_qa_turns": len(rec["qa_turns"]),
            "n_analyst_questions": len(rec["analyst_questions"]),
        })
    with open(os.path.join(out_dir, "_summary.json"), "w") as fp:
        json.dump(summary, fp, indent=2)
    for s in summary:
        print(s)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    main(os.path.join(root, "transcripts"), os.path.join(root, "parsed"))
