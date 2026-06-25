"""Per-RCL-analyst breakdown: how many extra (call) observations we already
gain from the 5 current peers, and which additional sectors / tickers
would most extend coverage for each one (based on their self-declared
title/firm).

Outputs reports/rcl_expansion_value.md.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPORTS = os.path.join(ROOT, "reports")

PEERS = ["ccl", "nclh", "mar", "hlt", "h"]


# Manual: each RCL analyst's self-declared coverage scope (from
# affiliations_seen / title strings). Used to suggest which untapped sectors
# would yield more data per analyst.
EXPANSION_HINT = {
    "robin farley": "Leisure (UBS): + theme parks (DIS, SIX, FUN, SEAS), Vail (MTN)",
    "steven wieczynski": "Gaming + Leisure (Stifel): + LVS, WYNN, MGM, CZR, BYD, BALY, PENN",
    "brandt montour": "Gaming, Lodging, Leisure (Barclays): + LVS, WYNN, MGM, CZR; possibly DIS",
    "vince ciepiel": "Lodging, OTAs, Cruise, Luxury (Cleveland): + BKNG, EXPE, ABNB, TRIP, TPR, RL",
    "benjamin chaiken": "Leisure (Mizuho/CS): + LVS, WYNN, MGM, BYD, gaming names",
    "matthew boss": "Consumer/Retail (JPM): + softlines/retail; less leisure overlap",
    "conor cunningham": "Travel & Transports (Melius): + DAL, UAL, AAL, LUV, ALK, JBLU",
    "daniel politzer": "Gaming, Lodging, Leisure (Wells Fargo): + LVS, WYNN, MGM, CZR, BYD",
    "fred wightman": "Travel (Wolfe): + DIS, theme parks, possibly OTAs",
    "paul golding": "Payments / Lifestyle (Macquarie): + V, MA, PYPL; limited leisure overlap",
    "james hardiman": "Leisure & Travel (Citi): + SIX, FUN, SEAS, BKNG, EXPE",
    "lizzie dove": "Equity research (Goldman): + lodging/gaming names",
    "ivan feinseth": "CIO/Director (Tigress): cross-sector — many names",
    "patrick scholes": "Senior analyst (Truist): + lodging/gaming",
    "jaime katz": "Senior analyst (Morningstar): + consumer cyclicals",
    "sharon zackfia": "Consumer sector head (William Blair): + consumer leisure/retail",
    "sean wagner": "Junior associate (Citigroup): tied to senior analyst's book",
    "ryan sundby": "Research analyst (William Blair): ride-along on lead's coverage",
    "stephen grambling": "Gaming/Lodging/Leisure (Goldman → Morgan Stanley): + LVS, WYNN, MGM, gaming",
    "chris stathoulopoulos": "Senior analyst (SIG → Susquehanna): + gaming",
    "jamie rollo": "European Leisure & Hotel (Morgan Stanley): only European tickers (CCL.L, IHG.L, etc.)",
    "andrew didora": "Senior research analyst (BofA): airlines + travel",
    "david katz": "MD (Jefferies): gaming/lodging/leisure broad",
}


def main() -> None:
    cov = json.load(open(os.path.join(REPORTS, "cross_company_coverage.json")))
    rcl = json.load(open(os.path.join(ROOT, "data", "analysts.json")))
    rcl_per = cov["coverage_rcl_analysts"]  # analyst → ticker → [quarters]

    rows = []
    for name in sorted(rcl):
        key = name.lower()
        n_rcl = rcl[name]["n_questions"]
        per_ticker = rcl_per.get(key, {})
        total_peer_calls = sum(len(v) for v in per_ticker.values())
        n_tickers_appeared = sum(1 for v in per_ticker.values() if v)
        hint = EXPANSION_HINT.get(key, "")
        rows.append((name, n_rcl, n_tickers_appeared, total_peer_calls, per_ticker, hint))

    lines: list[str] = []
    lines.append("# Per-RCL-analyst expansion value\n")
    lines.append(
        "For each RCL analyst, we show: questions in RCL history; how many of the 5 current "
        "peers they've appeared on; how many peer calls they've appeared in (rough proxy for "
        "additional question turns we can mine); and which sectors / tickers would extend "
        "their coverage further based on their self-declared title.\n"
    )

    lines.append("## Current 6 companies\n")
    lines.append("| ticker | name | sector |")
    lines.append("|---|---|---|")
    lines.append("| RCL | Royal Caribbean Group | Cruise |")
    lines.append("| CCL | Carnival | Cruise |")
    lines.append("| NCLH | Norwegian Cruise Line | Cruise |")
    lines.append("| MAR | Marriott | Lodging |")
    lines.append("| HLT | Hilton | Lodging |")
    lines.append("| H | Hyatt | Lodging |")
    lines.append("")

    lines.append("## Per-RCL-analyst peer-data gain so far\n")
    lines.append("| Analyst | RCL Qs | Peers ≥1 | Peer calls | CCL | NCLH | MAR | HLT | H | Coverage hint (extra tickers) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for name, n_rcl, n_pks, n_pcalls, pt, hint in sorted(rows, key=lambda r: -r[1]):
        ccl = len(pt.get("ccl", []))
        nclh = len(pt.get("nclh", []))
        mar = len(pt.get("mar", []))
        hlt = len(pt.get("hlt", []))
        h = len(pt.get("h", []))
        lines.append(
            f"| {name} | {n_rcl} | {n_pks}/5 | {n_pcalls} "
            f"| {ccl or ''} | {nclh or ''} | {mar or ''} | {hlt or ''} | {h or ''} "
            f"| {hint} |"
        )

    total_rcl_q = sum(r[1] for r in rows)
    total_peer_calls = sum(r[3] for r in rows)
    lines.append(
        f"\n**Totals:** {total_rcl_q} RCL question turns; "
        f"~{total_peer_calls} additional analyst-call appearances across the 5 current peers "
        f"(i.e. up to ~{total_peer_calls} more question turns can be mined for these same 23 people).\n"
    )

    lines.append("## Suggested next-tier ticker expansions, ranked by RCL-analyst gain\n")
    lines.append("Based on RCL analysts' declared coverage scope, the highest-yield additions:\n")
    proposals = [
        ("Gaming (LVS, WYNN, MGM, CZR, BYD, PENN)",
         "Steven Wieczynski, Brandt Montour, Daniel Politzer, Benjamin Chaiken, "
         "Stephen Grambling, David Katz, Chris Stathoulopoulos, Patrick Scholes — "
         "8+ RCL analysts heavily covered; gaming is the obvious adjacent sector."),
        ("Theme parks (DIS, FUN, SIX, SEAS, MTN)",
         "Robin Farley, James Hardiman, Fred Wightman, Brandt Montour — "
         "leisure-bucket analysts who'll appear here too."),
        ("OTAs (BKNG, EXPE, ABNB, TRIP)",
         "Vince Ciepiel, James Hardiman, Fred Wightman, Lizzie Dove — "
         "extends travel-supply analysts to travel-distribution side."),
        ("Airlines (DAL, UAL, AAL, LUV, ALK, JBLU)",
         "Conor Cunningham, Andrew Didora — "
         "specifically the Transports analysts in the roster."),
        ("European leisure (CCL.L, IHG.L, EZJ.L, RYAAY)",
         "Jamie Rollo (Morgan Stanley) is European-only and is the one RCL "
         "analyst currently uncovered by the US peers."),
    ]
    for tag, who in proposals:
        lines.append(f"\n### + {tag}\n{who}")

    out = os.path.join(REPORTS, "rcl_expansion_value.md")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {out}")
    print()
    print(f"23 RCL analysts; {total_rcl_q} RCL Qs total; ~{total_peer_calls} peer-call appearances already.")


if __name__ == "__main__":
    main()
