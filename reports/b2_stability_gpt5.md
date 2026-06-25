# B2 evaluator stability check (gpt-5, 3 runs)

**Data**: Auto K=10 predictions × 12 actuals (Robin split into 2 cells). Same `prompts/b2_eval.md`, same data, only LLM call repeated.

## Headline

- **Cells with identical score across all 3 runs**: 9/12 = 0.750
- **Cells that flipped binary (≥3) boundary**: 1/12
- **Cells with any score variance**: 3/12

## Per-run aggregates

| Run | binary≥3 | strong≥4 | avg score |
|---|---|---|---|
| Run 1 | 5/12 = 0.417 | 0/12 = 0.000 | 2.333 |
| Run 2 | 6/12 = 0.500 | 1/12 = 0.083 | 2.500 |
| Run 3 | 6/12 = 0.500 | 0/12 = 0.000 | 2.333 |

## Per-cell score variance

| Cell | Run 1 | Run 2 | Run 3 | range | stable? |
|---|---|---|---|---|---|
| andrew_didora_a0 | 2 | 2 | 2 | 0 | ✓ |
| brandt_montour_a0 | 3 | 4 | 3 | 1 | ✗ |
| james_hardiman_a0 | 2 | 3 | 3 | 1 | ✗ |
| kevin_kopelman_a0 | 1 | 1 | 1 | 0 | ✓ |
| lizzie_dove_a0 | 3 | 3 | 3 | 0 | ✓ |
| matthew_boss_a0 | 2 | 2 | 2 | 0 | ✓ |
| robin_farley_a0 | 2 | 2 | 2 | 0 | ✓ |
| robin_farley_a1 | 3 | 3 | 3 | 0 | ✓ |
| sharon_zackfia_a0 | 2 | 2 | 1 | 1 | ✗ |
| steven_wieczynski_a0 | 2 | 2 | 2 | 0 | ✓ |
| vince_ciepiel_a0 | 3 | 3 | 3 | 0 | ✓ |
| xian_siew_a0 | 3 | 3 | 3 | 0 | ✓ |

## Sub-dimension flip counts

| Sub-dim | # cells where this sub-dim changed across runs |
|---|---|
| topic_match | 3 / 12 |
| trigger_alignment | 7 / 12 |
| question_form_alignment | 4 / 12 |
| granularity_alignment | 3 / 12 |

## Decision rule

- ≥10/12 cells identical → evaluator stable, use gpt-5 going forward
- 7-9/12 stable → moderate, average across 3 runs
- <7/12 stable → revise `prompts/b2_eval.md`

### Verdict: **Moderate instability.** Recommend reporting 3-run averages in the paper.