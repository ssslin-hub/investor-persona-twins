"""Aggregate the analyst roster across RCL + 5 peers, deduplicate by
(name, firm-root), and report:

  - total distinct analysts (by name+firm-root)
  - same-name-different-firm collisions (potential namesakes)
  - total companies, total calls
  - per-analyst company breadth: how many distinct tickers each appeared in
  - how many analysts appear in >= 2 companies

Outputs reports/analyst_dedup.md and reports/analyst_dedup.json.
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

REPORTS = os.path.join(ROOT, "reports")

TICKERS_PEERS = ["ccl", "nclh", "mar", "hlt", "h"]

# RCL data is in data/analysts.json, indexed by analyst name; each record has
# 'affiliations_seen' giving every (title, firm) string they ever appeared
# under.
RCL_PATH = os.path.join(ROOT, "data", "analysts.json")
PEERS_PATH = os.path.join(REPORTS, "cross_company_coverage.json")


# Map firm-name variants to a canonical token. Keep this conservative and
# data-driven: we only need to collapse the variants we actually observe.
FIRM_ALIASES = {
    "ubs": ["ubs", "ubs investment bank", "ubs financial"],
    "stifel": ["stifel", "stifel nicolaus", "stifel financial", "stifel nicolaus & company", "stifel nicolaus and company"],
    "barclays": ["barclays", "barclays capital", "barclays bank plc"],
    "cleveland research": ["cleveland research", "cleveland research company", "cleveland research and company"],
    "credit suisse": ["credit suisse"],
    "mizuho": ["mizuho", "mizuho securities"],
    "jpmorgan": ["jpmorgan", "j.p. morgan", "jp morgan", "jpmorgan chase & co", "jpmorgan chase & co.", "jpmorgan chase"],
    "melius research": ["melius research", "melius research llc"],
    "wells fargo": ["wells fargo", "wells fargo securities"],
    "wolfe research": ["wolfe research"],
    "macquarie": ["macquarie", "macquarie capital"],
    "citi": ["citi", "citigroup", "citi research"],
    "goldman sachs": ["goldman sachs"],
    "tigress financial partners": ["tigress financial partners", "tigress financial"],
    "truist securities": ["truist securities", "truist"],
    "morningstar": ["morningstar"],
    "william blair": ["william blair", "william blair & company"],
    "susquehanna": ["susquehanna", "susquehanna financial group", "susquehanna international group"],
    "morgan stanley": ["morgan stanley"],
    "bank of america": ["bank of america", "bofa", "bofa securities", "bofa global research", "merrill lynch"],
    "jefferies": ["jefferies", "jefferies llc"],
    "bnp paribas": ["bnp paribas", "bnp paribas exane", "exane bnp paribas"],
    "raymond james": ["raymond james", "raymond james financial"],
    "deutsche bank": ["deutsche bank", "deutsche bank securities"],
    "bernstein": ["bernstein", "alliancebernstein", "sanford bernstein", "ab bernstein"],
    "robert w. baird": ["robert w. baird", "baird", "robert w baird"],
    "tigress": ["tigress financial"],
    "redburn": ["redburn", "redburn atlantic"],
    "berenberg": ["berenberg", "berenberg capital markets"],
    "rbc": ["rbc", "rbc capital markets"],
    "evercore": ["evercore", "evercore isi"],
    "td cowen": ["td cowen", "cowen", "cowen and company"],
    "jmp securities": ["jmp securities", "jmp"],
}


def canon_firm(firm: str) -> str:
    f = firm.lower()
    f = re.sub(r"\b(financial|capital|investment bank|securities|nicolaus|llc|inc\.?|the|company|chase|group|& co\.?|& company|and company|bank plc|partners)\b", "", f)
    f = re.sub(r"[^\w ]+", " ", f)
    f = re.sub(r"\s+", " ", f).strip()
    # Try alias mapping
    for canon, variants in FIRM_ALIASES.items():
        if f == canon or f in variants:
            return canon
        for v in variants:
            if v in f:
                return canon
    return f


# Collapse short / common nicknames to their canonical first name. Conservative:
# only entries we actually observe in this dataset.
NICKNAMES = {
    "dan": "daniel",
    "ben": "benjamin",
    "joe": "joseph",
    "matt": "matthew",
    "matty": "matthew",
    "steve": "steven",
    "rob": "robert",
    "robbie": "robert",
    "chris": "christopher",
    "mike": "michael",
    "jim": "james",
    "jamie": "james",   # ambiguous; will be flagged in namesake table
    "tony": "anthony",
    "rick": "richard",
    "rich": "richard",
    "alex": "alexander",
    "andy": "andrew",
    "dave": "david",
    "nick": "nicholas",
    "bill": "william",
    "will": "william",
    "tom": "thomas",
}


def canon_name(name: str) -> str:
    n = name.lower().strip()
    n = re.sub(r"\s+", " ", n)
    # Drop trailing punctuation
    n = n.rstrip(".,")
    # Drop initials and middle initials/words: keep first-token + last-token only.
    toks = [t for t in n.split() if not re.match(r"^[a-z]\.?$", t)]  # drop "c." etc.
    if len(toks) >= 2:
        first, last = toks[0], toks[-1]
        first = NICKNAMES.get(first, first)
        n = f"{first} {last}"
    return n


def parse_rcl(rcl: dict) -> list[tuple[str, str, str]]:
    """Return list of (name, firm_canon, ticker='rcl')."""
    out: list[tuple[str, str, str]] = []
    for name, rec in rcl.items():
        affs = rec.get("affiliations_seen") or []
        for aff in affs:
            # aff string like "Analyst, UBS" or "Managing Director, Stifel"
            parts = aff.split(",", 1)
            firm = parts[1].strip() if len(parts) > 1 else parts[0].strip()
            out.append((canon_name(name), canon_firm(firm), "rcl"))
    return out


def parse_peers(peers: dict) -> tuple[list[tuple[str, str, str]], dict]:
    """Return list of (name, firm_canon, ticker) and per-ticker call counts."""
    out: list[tuple[str, str, str]] = []
    call_counts: dict[str, int] = {}
    for tk, payload in peers["per_ticker"].items():
        calls = payload.get("calls", {})
        call_counts[tk] = len(calls)
        for _label, analysts in calls.items():
            for a in analysts:
                out.append((canon_name(a["name"]), canon_firm(a["firm"]), tk))
    return out, call_counts


def main() -> None:
    rcl = json.load(open(RCL_PATH))
    peers = json.load(open(PEERS_PATH))

    rcl_rows = parse_rcl(rcl)
    peer_rows, peer_call_counts = parse_peers(peers)
    rcl_call_count = 17  # 2022-Q1..2026-Q1 inclusive
    all_call_count = rcl_call_count + sum(peer_call_counts.values())

    rows = rcl_rows + peer_rows

    # ---- Build (name, firm) → set of tickers index ----
    person_to_tickers: dict[tuple[str, str], set[str]] = defaultdict(set)
    name_to_firms: dict[str, set[str]] = defaultdict(set)
    name_only_to_tickers: dict[str, set[str]] = defaultdict(set)
    for name, firm, tk in rows:
        person_to_tickers[(name, firm)].add(tk)
        name_to_firms[name].add(firm)
        name_only_to_tickers[name].add(tk)

    # ---- Same-name-different-firm collisions ----
    namesakes = {n: sorted(firms) for n, firms in name_to_firms.items() if len(firms) >= 2}

    # ---- How many distinct persons by (name, firm) ----
    n_persons_dedup = len(person_to_tickers)
    n_distinct_names = len(name_to_firms)

    # ---- How many distinct firms / companies / calls ----
    all_firms: set[str] = set()
    for firms in name_to_firms.values():
        all_firms |= firms
    n_firms = len(all_firms)
    n_companies = 1 + len(TICKERS_PEERS)  # RCL + 5 peers

    # ---- Breadth: how many distinct companies each person appears in ----
    breadth_counts: dict[int, int] = defaultdict(int)
    multi_company_persons: list[tuple[tuple[str, str], list[str]]] = []
    for k, tks in person_to_tickers.items():
        breadth_counts[len(tks)] += 1
        if len(tks) >= 2:
            multi_company_persons.append((k, sorted(tks)))
    multi_company_persons.sort(key=lambda x: (-len(x[1]), x[0][0]))

    # Same as above, but matching by name only (ignores firm changes)
    breadth_counts_name: dict[int, int] = defaultdict(int)
    multi_company_by_name: list[tuple[str, list[str]]] = []
    for name, tks in name_only_to_tickers.items():
        breadth_counts_name[len(tks)] += 1
        if len(tks) >= 2:
            multi_company_by_name.append((name, sorted(tks)))
    multi_company_by_name.sort(key=lambda x: (-len(x[1]), x[0]))

    # ---- Markdown report ----
    lines: list[str] = []
    lines.append("# Analyst dedup and cross-company breadth\n")
    lines.append("Source: RCL data/analysts.json + cross-company scrape "
                 "(reports/cross_company_coverage.json, 5 peer tickers × 17 quarters each).\n")

    lines.append("## Totals\n")
    lines.append(f"- **Companies (tickers):** {n_companies} (RCL + {', '.join(t.upper() for t in TICKERS_PEERS)})")
    lines.append(f"- **Calls parsed:** {all_call_count} (RCL: {rcl_call_count}; peers: " +
                 ", ".join(f"{tk.upper()}={peer_call_counts.get(tk,0)}" for tk in TICKERS_PEERS) + ")")
    lines.append(f"- **Distinct (name, firm) persons:** {n_persons_dedup}")
    lines.append(f"- **Distinct names (any firm):** {n_distinct_names}")
    lines.append(f"- **Distinct firms (canonical):** {n_firms}\n")

    lines.append("## Same-name across firms (potential namesake / job switch)\n")
    if namesakes:
        lines.append("| name | firms seen |")
        lines.append("|---|---|")
        for n, firms in sorted(namesakes.items()):
            lines.append(f"| {n} | {', '.join(firms)} |")
        lines.append(f"\n{len(namesakes)} names have ≥2 distinct firm-strings. "
                     "Most are the same analyst changing firms (e.g., Benjamin Chaiken: "
                     "Credit Suisse → Mizuho); a few may be true namesakes and need manual check.\n")
    else:
        lines.append("(none)\n")

    lines.append("## Company-breadth distribution (dedup by name+firm)\n")
    lines.append("| # of companies appeared in | # persons |")
    lines.append("|---|---|")
    for k in sorted(breadth_counts):
        lines.append(f"| {k} | {breadth_counts[k]} |")
    multi_n = sum(v for k, v in breadth_counts.items() if k >= 2)
    lines.append(f"\n**{multi_n} of {n_persons_dedup} dedup'd persons appear in ≥2 companies.**\n")

    lines.append("## Company-breadth distribution (dedup by NAME ONLY — counts same person across firm changes)\n")
    lines.append("| # of companies appeared in | # persons |")
    lines.append("|---|---|")
    for k in sorted(breadth_counts_name):
        lines.append(f"| {k} | {breadth_counts_name[k]} |")
    multi_n2 = sum(v for k, v in breadth_counts_name.items() if k >= 2)
    lines.append(f"\n**{multi_n2} of {n_distinct_names} distinct names appear in ≥2 companies.**\n")

    lines.append("## Top cross-company analysts (by # tickers, name-only dedup)\n")
    lines.append("| analyst | # tickers | tickers |")
    lines.append("|---|---|---|")
    for name, tks in multi_company_by_name[:25]:
        lines.append(f"| {name} | {len(tks)} | {', '.join(t.upper() for t in tks)} |")

    out_md = os.path.join(REPORTS, "analyst_dedup.md")
    with open(out_md, "w") as f:
        f.write("\n".join(lines))

    out_json = os.path.join(REPORTS, "analyst_dedup.json")
    with open(out_json, "w") as f:
        json.dump({
            "n_companies": n_companies,
            "n_calls": all_call_count,
            "per_ticker_calls": {"rcl": rcl_call_count, **peer_call_counts},
            "n_persons_dedup_name_firm": n_persons_dedup,
            "n_distinct_names": n_distinct_names,
            "n_firms_canonical": n_firms,
            "breadth_name_firm": dict(breadth_counts),
            "breadth_name_only": dict(breadth_counts_name),
            "multi_company_name_only": [
                {"name": n, "tickers": tks} for n, tks in multi_company_by_name
            ],
            "namesake_candidates": namesakes,
        }, f, indent=2)
    print(f"wrote {out_md}")
    print(f"wrote {out_json}")
    print()
    # Print headline to stdout
    print(f"companies={n_companies}, calls={all_call_count}, "
          f"persons(name+firm)={n_persons_dedup}, names={n_distinct_names}, firms={n_firms}")
    print(f"≥2 companies (name+firm dedup): {multi_n}")
    print(f"≥2 companies (name-only dedup): {multi_n2}")


if __name__ == "__main__":
    main()
