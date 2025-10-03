#!/usr/bin/env bash
set -euo pipefail
# Solving UNSAT jobs: CNF, need 12GB RAM
# List of jobs: each line is k n x y s c v a l b f
# Hard points past 180, SAT:KNF, UNSAT:CNF, using "UB"; line-filter heuristic (k+10) also set

jobs=(
"7 234 77 156 1 0 1 0 0 2 0"
"7 236 78 157 1 0 1 0 0 2 0"
"7 236 79 156 1 0 1 0 0 2 0"
"7 239 80 158 1 0 1 0 0 2 0"
"7 241 81 159 1 0 1 0 0 2 0"
"7 245 82 162 1 0 1 0 0 2 0"
"7 247 83 163 1 0 1 0 0 2 0"
"7 250 84 165 1 0 1 0 0 2 0"
"7 252 85 166 1 0 1 0 0 2 0"
"7 254 86 167 1 0 1 0 0 2 0"
"7 256 87 168 1 0 1 0 0 2 0"
"7 259 88 170 1 0 1 0 0 2 0"
"7 261 89 171 1 0 1 0 0 2 0"
"7 232 154 77 1 0 1 0 0 2 0"
"7 234 155 78 1 0 1 0 0 2 0"
"7 236 156 79 1 0 1 0 0 2 0"
"7 244 160 83 1 0 1 0 0 2 0"
"7 247 162 84 1 0 1 0 0 2 0"
"7 252 165 86 1 0 1 0 0 2 0"
"7 254 166 87 1 0 1 0 0 2 0"
"7 259 169 89 1 0 1 0 0 2 0"
"7 264 172 91 1 0 1 0 0 2 0"
"7 267 174 92 1 0 1 0 0 2 0"
)

for line in "${jobs[@]}"; do
  read -r k n x y s c v a l b f <<< "$line"
  for r in $(seq 1 1); do
    jobname="k${k}_n${n}_x${x}_y${y}_f${f}_b${b}_r${r}"
    echo "Submitting job $jobname"
    sbatch --job-name="$jobname" --mem-per-cpu=12GB --time=72:00:00 run_jobs.sh \
      -k "$k" -n "$n" -x "$x" -y "$y" \
      -s "$s" -c "$c" -v "$v" -a "$a" -l "$l" -b "$b" -f "$f" \
      -t 0 -r "$r" -j "10" #using line filter heuristic
    sleep 1
  done
done
