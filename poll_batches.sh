#!/bin/bash
# Cron-driven: poll both batches, parse when ready. Logs to /tmp/batch_poll.log
ROOT="/Users/dengtianze/Desktop/digital twins/invest-call-twins/investorPersona"
cd "$ROOT"
export OPENAI_API_KEY="${OPENAI_API_KEY:?set OPENAI_API_KEY in your environment}"
{
  echo "=== $(date -Iseconds) ==="
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_gpt5.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_mini.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_gpt5_retry.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_dedup_eval_gpt5.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_dedup_eval_mini.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_iter_dedup_eval_gpt5.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_iter_dedup_eval_mini.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_kcurve_extend_retry.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_iter_round_eval_mini.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_iter_consensus_eval_gpt5.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_iter_consensus_eval_mini.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_iter_round_eval_gpt5.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_k10_dedup_5sims_eval_gpt5.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_k10_dedup_5sims_eval_mini.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_k10_sim1_dedup_eval_gpt5.json
  python3 src/batch_poll_parse.py --tracker data_auto/batch/tracker_k10_sim1_dedup_eval_mini.json
  echo ""
} >> /tmp/batch_poll.log 2>&1
