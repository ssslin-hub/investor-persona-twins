#!/bin/bash
# Launch a wave of fresh sim+eval jobs in parallel.
# Usage: bash launch_wave.sh <wave_number>
#   wave 1: V1 K=5,10,16,18,20 × labels s2-s5 (20 jobs)
#   wave 2: v5 K=5,10,16,18,20 × labels s2-s5 (20 jobs)
#   wave 3: Auto K=5,10,14 × labels s2-s5 (12 jobs)
#   wave 4: Auto K=16,18,20 × labels s2-s5 (12 jobs)
set -e
cd "$(dirname "$0")"
export OPENAI_API_KEY="${OPENAI_API_KEY:?set OPENAI_API_KEY in your environment}"

case "$1" in
  1) SOURCE=v1; KS="5 10 16 18 20" ;;
  2) SOURCE=v5; KS="5 10 16 18 20" ;;
  3) SOURCE=auto; KS="5 10 14" ;;
  4) SOURCE=auto; KS="16 18 20" ;;
  *) echo "Usage: $0 <1|2|3|4>"; exit 1 ;;
esac

pids=()
for K in $KS; do
  for L in s2 s3 s4 s5; do
    logf="/tmp/se_${SOURCE}_K${K}_${L}.log"
    python3 src/sim_then_eval_generic.py --source $SOURCE --K $K --label $L --n-eval-runs 5 > "$logf" 2>&1 &
    pids+=($!)
    echo "launched: $SOURCE K=$K $L (pid=$!)"
  done
done
echo ""
echo "Waiting on ${#pids[@]} jobs..."
for p in "${pids[@]}"; do
  wait $p
done
echo "Wave $1 complete."
