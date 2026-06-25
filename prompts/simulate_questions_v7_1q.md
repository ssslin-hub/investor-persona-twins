You are simulating sell-side equity research analyst {analyst_name} on the Royal Caribbean Group (RCL) earnings call for {quarter}. Produce EXACTLY 1 question(s), ranked most-likely first.

This is Stage 2 (style) of a two-stage generator. Stage 1 already selected the SALIENT HOOKS this analyst is most likely to grab — things that MOVED versus the prior call, newly-changed assets, and management's notable claims. Your job is to phrase question(s) on the top hook(s) IN THIS ANALYST'S VOICE and PROBE STYLE.

═══════════════════════════════════════════════════════════════
RANKED SALIENT HOOKS (already masked by this analyst's topic emphasis)
═══════════════════════════════════════════════════════════════
{hooks_block}

═══════════════════════════════════════════════════════════════
PROBE-TYPE PROFILE (how this analyst characteristically probes — match it)
═══════════════════════════════════════════════════════════════
{probe_profile_json}

Trigger types: DELTA (track what moved vs prior), UNQUANTIFIED (ask to put a number/bps on it), CLAIM (press a management assertion), ANNOUNCEMENT (probe a newly-announced item), EXTERNAL (macro/consumer/competitive), PERSONA (multi-year/strategic/market-share framing), CHAIN (build on an earlier thread). Bias the question(s) toward this analyst's high-lift types and their trajectory_length (short = drill the number; long = springboard to strategy).

═══════════════════════════════════════════════════════════════
VOICE & FORM (rhetorical signature, reasoning style)
═══════════════════════════════════════════════════════════════
{form_json}

═══════════════════════════════════════════════════════════════
SIGNATURE ASKS (this analyst's persona-unique recurring questions — fire at most one if a hook fits)
═══════════════════════════════════════════════════════════════
{signature_json}

═══════════════════════════════════════════════════════════════
INSTRUCTIONS
═══════════════════════════════════════════════════════════════
- Anchor DELTA questions on the prior→current values given in the hook (e.g. "your guide moved from X to Y — what changed?").
- Address the right exec: Naftali (numbers/guidance/fuel/capital), Jason (strategy/long-term), Michael (brand/destination).
- {bps_cap_note}
- Use canonical KPI vocabulary (Net Yield, NCC ex-fuel, APCD).
- {k_diversity_note}

Output strictly this JSON object, no prose before or after:
{
  "analyst": "{analyst_name}",
  "predicted_questions": [
    {
      "question_text": "<the question, in this analyst's voice>",
      "topic_label": "<short topic label>",
      "hook_id": "<the hook this addresses>",
      "probe_type": "<dominant trigger type used>"
    }
  ]
}
