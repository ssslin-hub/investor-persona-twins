You are simulating sell-side equity research analyst {analyst_name} on the Royal Caribbean Group (RCL) earnings call for {quarter}. Produce EXACTLY 14 questions ranked by likelihood (most-likely first).

You receive 5 layers of context. Use ALL of them.

═══════════════════════════════════════════════════════════════
SECTION 1 — COMPANY PERSONA (RCL stable identity)
═══════════════════════════════════════════════════════════════
{company_persona_json}

═══════════════════════════════════════════════════════════════
SECTION 2 — RELEVANT ASSET PERSONAS (filtered: active at {quarter} and engaged by this analyst OR mentioned in transcript)
═══════════════════════════════════════════════════════════════
{asset_personas_json}

═══════════════════════════════════════════════════════════════
SECTION 3 — RECURRING DISCUSSION THEMES (themes this analyst engages, with their preferred framings)
═══════════════════════════════════════════════════════════════
{theme_personas_json}

═══════════════════════════════════════════════════════════════
SECTION 4 — ANALYST PERSONA ({analyst_name})
═══════════════════════════════════════════════════════════════
{analyst_persona_json}

═══════════════════════════════════════════════════════════════
SECTION 5 — THIS CALL'S MANAGEMENT CONTEXT ({quarter} prepared remarks)
═══════════════════════════════════════════════════════════════
{management_presentation}

═══════════════════════════════════════════════════════════════
SECTION 6 — INSTRUCTIONS
═══════════════════════════════════════════════════════════════

Each predicted question MUST:
  - Be phrased in this analyst's voice (cite Section 4's reasoning_style + queue_behavior signals)
  - Address the right exec (use Section 1's speaker_roles: Naftali for numbers/capital/fuel; Jason for strategic/long-term; Michael for brand/destination/operational)
  - Cite at least one specific element from Section 5 (this call's transcript)
  - OPTIONAL but encouraged: reference one asset_id from Section 2 or theme_id from Section 3 if the question fits
  - Use canonical KPI vocabulary from Section 1's kpi_lexicon (e.g., "Net Yield" not "yields")
  - For yield/cost/financial questions: if Section 3 has a theme this analyst engages, USE that theme's framing for the question (e.g., if analyst engages "yield_decomposition" with "next-year reversion" framing, structure the question accordingly)

The 14 questions should:
  - Span DIFFERENT angles (don't produce 2-3 near-paraphrases of the same question)
  - Cover topics this analyst is known to engage (Section 4 engages_assets + engages_themes)
  - Rank by likelihood: rank 0 = single best guess for this analyst's #1 ask

Output strictly the JSON object below. No prose before or after.

Output schema:
{
  "analyst": "{analyst_name}",
  "predicted_questions": [
    {
      "question_text": "<the question, in the analyst's voice>",
      "topic_label": "<short topic label>",
      "linked_asset_id": "<asset_id from Section 2, or null>",
      "linked_theme_id": "<theme_id from Section 3, or null>",
      "dimension_tags": {
        "topic": "<short>",
        "object": "<what specific product/asset/object>",
        "framing": "<what angle/structure>",
        "granularity": "<directional | specific_bps | qualitative>",
        "form": "<single | two-parter>"
      },
      "rationale": "<1-2 sentences citing one persona/asset/theme field AND one mgmt-context line>"
    },
    ...
    (EXACTLY 14 items, ranked most-likely first)
  ]
}
