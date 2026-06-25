# Analyst dedup and cross-company breadth

Source: RCL data/analysts.json + cross-company scrape (reports/cross_company_coverage.json, 5 peer tickers × 17 quarters each).

## Totals

- **Companies (tickers):** 6 (RCL + CCL, NCLH, MAR, HLT, H)
- **Calls parsed:** 102 (RCL: 17; peers: CCL=17, NCLH=17, MAR=17, HLT=17, H=17)
- **Distinct (name, firm) persons:** 121
- **Distinct names (any firm):** 84
- **Distinct firms (canonical):** 66

## Same-name across firms (potential namesake / job switch)

| name | firms seen |
|---|---|
| adam rohman | fp a and treasurer hyatt, hyatt, hyatt hotels, hyatt hotels corporation |
| ari klein | bmo, bmo markets |
| benjamin chaiken | credit suisse, evercore, mizuho |
| beth roberts | carnival, carnival corporation, carnival corporation plc, investor relations carnival |
| christopher stathoulopoulos | sig, susquehanna |
| conor cunningham | director and senior equity research analyst, melius research |
| daniel politzer | jpmorgan, wells fargo |
| ivan feinseth | chief investment officer and director of research tigress, cio and director of research tigress |
| jackie mcconagha | investor relations marriott international, marriott, marriott international |
| jaime katz | morning star, morningstar |
| jessica john | corporate communications and esg norwegian cruise line holdings, esg and corporate communications norwegian cruise line, esg and corporate communications norwegian cruise line holdings, investor relations and esg corporate communications norwegian cruise line, norwegian cruise line holdings |
| jill chapman | hilton, hilton worldwide holdings |
| jill slattery | hilton worldwide, investor relations and corporate development hilton worldwide |
| joseph greff | equity research j p morgan, j p morgan, jpmorgan |
| kevin jacobs | hilton, hilton worldwide, hilton worldwide holdings, president and head of global development hilton |
| leeny oberg | business operations marriott international, development marriott international, marriott, marriott international |
| mark kempa | norwegian cruise line, norwegian cruise line holdings |
| matthew boss | j p morgan, jpmorgan |
| noah hoppe | hyatt, hyatt hotels, hyatt hotels corporation, white lodging |
| sarah inmon | norwegian cruise line, norwegian cruise line holdings |
| stephen grambling | goldman sachs, morgan stanley |

21 names have ≥2 distinct firm-strings. Most are the same analyst changing firms (e.g., Benjamin Chaiken: Credit Suisse → Mizuho); a few may be true namesakes and need manual check.

## Company-breadth distribution (dedup by name+firm)

| # of companies appeared in | # persons |
|---|---|
| 1 | 80 |
| 2 | 9 |
| 3 | 20 |
| 4 | 1 |
| 5 | 4 |
| 6 | 7 |

**41 of 121 dedup'd persons appear in ≥2 companies.**

## Company-breadth distribution (dedup by NAME ONLY — counts same person across firm changes)

| # of companies appeared in | # persons |
|---|---|
| 1 | 47 |
| 2 | 9 |
| 3 | 17 |
| 4 | 1 |
| 5 | 2 |
| 6 | 8 |

**37 of 84 distinct names appear in ≥2 companies.**

## Top cross-company analysts (by # tickers, name-only dedup)

| analyst | # tickers | tickers |
|---|---|---|
| brandt montour | 6 | CCL, H, HLT, MAR, NCLH, RCL |
| conor cunningham | 6 | CCL, H, HLT, MAR, NCLH, RCL |
| daniel politzer | 6 | CCL, H, HLT, MAR, NCLH, RCL |
| david katz | 6 | CCL, H, HLT, MAR, NCLH, RCL |
| lizzie dove | 6 | CCL, H, HLT, MAR, NCLH, RCL |
| patrick scholes | 6 | CCL, H, HLT, MAR, NCLH, RCL |
| stephen grambling | 6 | CCL, H, HLT, MAR, NCLH, RCL |
| vince ciepiel | 6 | CCL, H, HLT, MAR, NCLH, RCL |
| benjamin chaiken | 5 | CCL, H, HLT, NCLH, RCL |
| robin farley | 5 | CCL, HLT, MAR, NCLH, RCL |
| trey bowers | 4 | CCL, HLT, MAR, NCLH |
| chad beynon | 3 | H, HLT, MAR |
| duane pfennigwerth | 3 | H, HLT, MAR |
| fred wightman | 3 | CCL, NCLH, RCL |
| jaime katz | 3 | CCL, NCLH, RCL |
| james hardiman | 3 | CCL, NCLH, RCL |
| joseph greff | 3 | H, HLT, MAR |
| kevin kopelman | 3 | H, HLT, MAR |
| matthew boss | 3 | CCL, NCLH, RCL |
| meredith jensen | 3 | H, HLT, MAR |
| michael bellisario | 3 | H, HLT, MAR |
| paul golding | 3 | CCL, NCLH, RCL |
| richard clarke | 3 | H, HLT, MAR |
| shaun kelley | 3 | H, HLT, MAR |
| smedes rose | 3 | H, HLT, MAR |