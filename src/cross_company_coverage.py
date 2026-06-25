"""Cross-reference RCL analyst roster against cruise and lodging peers.

For each peer ticker, list quarterly transcripts via the stockanalysis.com
listing page, download the most recent N quarters, extract Q&A analyst
speakers (lines of the form "<Name>\nAnalyst, <Firm>\n"), and compare
against the RCL analyst roster in data/analysts.json.

Outputs:
  reports/cross_company_coverage.json   raw per-call analyst lists
  reports/cross_company_coverage.md     human-readable coverage matrix
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from parse_transcripts import html_to_lines  # noqa: E402

CACHE = os.path.join(ROOT, "peer_cache")
REPORTS = os.path.join(ROOT, "reports")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

# Cruise peers + lodging peers
TICKERS = {
    "ccl": "Carnival",
    "nclh": "Norwegian Cruise Line",
    "mar": "Marriott",
    "hlt": "Hilton",
    "h": "Hyatt",
}

# Window: 17 most recent quarters (matches RCL window 2022-Q1..2026-Q1)
MAX_QUARTERS = 17

UA = "Mozilla/5.0 (compatible; coverage-analysis/1.0)"


def fetch(url: str, cache_path: str, sleep: float = 0.7) -> str:
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        with open(cache_path) as f:
            return f.read()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", errors="replace")
    with open(cache_path, "w") as f:
        f.write(body)
    time.sleep(sleep)
    return body


def list_transcripts(ticker: str) -> list[tuple[str, str]]:
    """Return [(quarter_label, url)] newest-first."""
    listing_url = f"https://stockanalysis.com/stocks/{ticker}/transcripts/"
    body = fetch(listing_url, os.path.join(CACHE, f"{ticker}_list.html"))
    # Match hrefs like /stocks/ccl/transcripts/533570-q1-2026/
    pat = re.compile(rf'href="(/stocks/{ticker}/transcripts/(\d+)-(q\d-\d{{4}})/)"')
    seen = set()
    out: list[tuple[str, str]] = []
    for m in pat.finditer(body):
        path, _tid, label = m.group(1), m.group(2), m.group(3)
        if label in seen:
            continue
        seen.add(label)
        out.append((label, "https://stockanalysis.com" + path))
    return out


# Lines we treat as the call-runner role; we skip Q&A turns coming from these.
OPERATOR_SET = {"operator", "moderator"}


def extract_analysts(lines: list[str]) -> list[tuple[str, str]]:
    """Return list of (analyst_name_lower, firm_lower) pairs appearing in Q&A.

    The HTML rendering puts speaker name on one line and "Analyst, <Firm>"
    (or "<Title>, <Firm>") on the next. We use the operator-intro
    "first question comes from" as the Q&A boundary.
    """
    qa_start = None
    for i, l in enumerate(lines):
        low = l.lower()
        if "first question" in low:
            qa_start = i
            break
        if "q&a" in low or "questions and answers" in low or "question-and-answer" in low:
            qa_start = i
            break
    if qa_start is None:
        return []

    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    n = len(lines)
    for i in range(qa_start, n - 1):
        name = lines[i].strip()
        title = lines[i + 1].strip()
        # Speaker-name lines are typically short and Title-Cased; title line
        # commonly contains a comma and the firm.
        if not (1 <= name.count(" ") <= 4):
            continue
        if name.lower() in OPERATOR_SET:
            continue
        # Reject pleasantries / filler lines ("Thank you.", "Got it.", etc.)
        if name.rstrip(".").lower() in {
            "thank you", "thanks", "got it", "great", "okay", "ok",
            "sure", "yes", "no", "right", "moving to guidance", "moving on",
            "that's helpful", "thanks for taking my question",
            "thanks for the question",
        }:
            continue
        # Person names: each word must start with an uppercase letter; allow
        # initials like "C." and hyphens. Must NOT end with a period.
        if not re.match(r"^([A-Z][a-zA-Z'\-]*\.?\s)+[A-Z][a-zA-Z'\-]+$", name):
            continue
        if "," not in title:
            continue
        if len(title) > 200:
            continue
        # Heuristic: title must look like a role-and-firm. Either it contains
        # the word Analyst/Director/Research/VP/Partner/Head, OR the firm is a
        # well-known sell-side house.
        low = title.lower()
        role_hit = any(k in low for k in (
            "analyst", "research", "director", "vp", "vice president",
            "partner", "head", "managing", "svp", "associate",
        ))
        if not role_hit:
            continue
        firm = title.split(",", 1)[1].strip()
        # drop trailing periods / quirky punctuation
        firm = re.sub(r"[\.;]+$", "", firm)
        key = (name.lower(), firm.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append((name, firm))
    return out


def normalize_firm(firm: str) -> str:
    f = firm.lower()
    f = re.sub(r"\b(financial|capital|investment bank|& company|& co\.?|securities|bank plc|research|llc|inc\.?|partners|nicolaus|chase & co\.?)\b", "", f)
    f = re.sub(r"\s+", " ", f).strip(" ,.;")
    return f


def main() -> None:
    rcl_analysts = json.load(open(os.path.join(ROOT, "data", "analysts.json")))
    rcl_roster = {name.lower() for name in rcl_analysts}

    print(f"RCL roster: {len(rcl_roster)} analysts")
    per_ticker: dict[str, dict] = {}

    for tk, name in TICKERS.items():
        print(f"\n=== {tk.upper()} ({name}) ===")
        try:
            transcripts = list_transcripts(tk)
        except Exception as e:
            print(f"  ! listing failed: {e}")
            per_ticker[tk] = {"error": str(e)}
            continue
        transcripts = transcripts[:MAX_QUARTERS]
        print(f"  listed {len(transcripts)} transcripts")
        calls: dict[str, list[dict]] = {}
        for label, url in transcripts:
            cache_path = os.path.join(CACHE, f"{tk}_{label}.html")
            try:
                fetch(url, cache_path)
                lines = html_to_lines(cache_path)
                analysts = extract_analysts(lines)
            except Exception as e:
                print(f"  ! {label}: {e}")
                continue
            calls[label] = [{"name": n, "firm": f} for n, f in analysts]
            print(f"  {label}: {len(analysts)} analysts")
        per_ticker[tk] = {"name": name, "calls": calls}

    # ---- Cross-reference ----
    # For each RCL analyst, list which peer tickers and quarters they appear in.
    coverage: dict[str, dict[str, list[str]]] = {a: {} for a in sorted(rcl_roster)}
    peer_only: dict[str, dict[str, list[str]]] = {}

    for tk, payload in per_ticker.items():
        if "calls" not in payload:
            continue
        for label, analysts in payload["calls"].items():
            for a in analysts:
                key = a["name"].lower()
                if key in rcl_roster:
                    coverage[key].setdefault(tk, []).append(label)
                else:
                    peer_only.setdefault(key, {}).setdefault(tk, []).append(label)

    out = {
        "tickers": TICKERS,
        "max_quarters": MAX_QUARTERS,
        "rcl_roster_size": len(rcl_roster),
        "per_ticker": per_ticker,
        "coverage_rcl_analysts": coverage,
        "peer_only_analysts": peer_only,
    }
    out_path = os.path.join(REPORTS, "cross_company_coverage.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote {out_path}")

    # ---- Markdown report ----
    md_lines: list[str] = []
    md_lines.append("# Cross-company analyst coverage\n")
    md_lines.append(
        f"Compared RCL roster ({len(rcl_roster)} analysts) against most recent "
        f"{MAX_QUARTERS} quarters of: " + ", ".join(
            f"{tk.upper()} ({TICKERS[tk]})" for tk in TICKERS
        ) + ".\n"
    )

    md_lines.append("## RCL analyst presence in peer calls\n")
    md_lines.append("| Analyst | " + " | ".join(t.upper() for t in TICKERS) + " | any peer |")
    md_lines.append("|" + "---|" * (len(TICKERS) + 2))
    any_count = 0
    for analyst in sorted(rcl_roster):
        row = [analyst]
        any_peer = False
        for tk in TICKERS:
            qs = coverage[analyst].get(tk, [])
            if qs:
                row.append(str(len(qs)))
                any_peer = True
            else:
                row.append("")
        row.append("yes" if any_peer else "")
        if any_peer:
            any_count += 1
        md_lines.append("| " + " | ".join(row) + " |")
    md_lines.append(f"\n**{any_count}/{len(rcl_roster)} RCL analysts appear in ≥1 peer call within the window.**\n")

    # Per-ticker analyst totals
    md_lines.append("## Per-peer analyst counts\n")
    md_lines.append("| Ticker | calls parsed | distinct analysts | RCL overlap |")
    md_lines.append("|---|---|---|---|")
    for tk in TICKERS:
        payload = per_ticker.get(tk, {})
        calls = payload.get("calls", {})
        all_names: set[str] = set()
        for analysts in calls.values():
            for a in analysts:
                all_names.add(a["name"].lower())
        overlap = len(all_names & rcl_roster)
        md_lines.append(f"| {tk.upper()} | {len(calls)} | {len(all_names)} | {overlap} |")

    md_path = os.path.join(REPORTS, "cross_company_coverage.md")
    with open(md_path, "w") as f:
        f.write("\n".join(md_lines))
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
