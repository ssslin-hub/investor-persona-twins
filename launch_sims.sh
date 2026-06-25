#!/bin/bash
# Launch all 59 missing sims in parallel (cheap mini calls).
set -e
cd "$(dirname "$0")"
export OPENAI_API_KEY="${OPENAI_API_KEY:?set OPENAI_API_KEY in your environment}"

pids=()
for K in 5 10 14 16 18 20; do
  for SRC in v1 v5 auto; do
    if [ "$K" = "14" ] && [ "$SRC" != "auto" ]; then continue; fi
    for L in s2 s3 s4 s5; do
      out="data_auto/final_eval_${K}q_${SRC}_${L}/summary.json"
      if [ -f "$out" ]; then continue; fi
      logf="/tmp/sim_${SRC}_K${K}_${L}.log"
      python3 src/sim_only.py --source $SRC --K $K --label $L > "$logf" 2>&1 &
      pids+=($!)
    done
  done
done
echo "Launched ${#pids[@]} sim jobs."
for p in "${pids[@]}"; do wait $p; done
echo "All sims complete."
ls data_auto/final_eval_*q_{v1,v5,auto}_s{2,3,4,5}/summary.json 2>/dev/null | wc -l
