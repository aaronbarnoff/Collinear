#!/usr/bin/env bash
set -euo pipefail

# These are difficult boundary points that the CNF/cadical solver couldn't solve in under an hour in past tests

usage() {
  cat << EOF
Usage: $0 [-f 0|1] [-w 0|1] [-j N] [-r SEEDS]

  -f    solver flag (0 = CNF, 1 = KNF)
  -w    KNF mode (0 = pure, 1 = hybrid)
  -j    line-length heuristic (k+j)
  -r    number of seeds per job (default 1)
EOF
}

# Parse options in your usual style
options=$(getopt "hf:w:j:r:" "$@")
eval set -- "$options"

f=1
w=0
j=10
r=1

while true; do
  case "$1" in
    -h) usage; exit 0 ;;
    -f) f="$2"; shift 2 ;;
    -w) w="$2"; shift 2 ;;
    -j) j="$2"; shift 2 ;;
    -r) r="$2"; shift 2 ;;
    --) shift; break ;;
    *) echo "Bad option"; usage; exit 2 ;;
  esac
done

# Memory selection logic
mem="4G"
if [[ "$f" -eq 0 ]]; then
  mem="12G"
elif [[ "$f" -eq 1 && "$w" -eq 1 ]]; then
  mem="12G"
fi

# Each line: k n x y s c v a l b

jobs_UNSAT=(
"7 234 77 156 1 0 1 0 0 2"
"7 236 78 157 1 0 1 0 0 2"
"7 236 79 156 1 0 1 0 0 2"
"7 239 80 158 1 0 1 0 0 2"
"7 241 81 159 1 0 1 0 0 2"
"7 245 82 162 1 0 1 0 0 2"
"7 247 83 163 1 0 1 0 0 2"
"7 250 84 165 1 0 1 0 0 2"
"7 252 85 166 1 0 1 0 0 2"
"7 254 86 167 1 0 1 0 0 2"
"7 256 87 168 1 0 1 0 0 2"
"7 259 88 170 1 0 1 0 0 2"
"7 261 89 171 1 0 1 0 0 2"
"7 232 154 77 1 0 1 0 0 2"
"7 234 155 78 1 0 1 0 0 2"
"7 236 156 79 1 0 1 0 0 2"
"7 244 160 83 1 0 1 0 0 2"
"7 247 162 84 1 0 1 0 0 2"
"7 252 165 86 1 0 1 0 0 2"
"7 254 166 87 1 0 1 0 0 2"
"7 259 169 89 1 0 1 0 0 2"
"7 264 172 91 1 0 1 0 0 2"
"7 267 174 92 1 0 1 0 0 2"
)

jobs_SAT=(
"7 235 78 156 1 0 1 0 0 2"
"7 238 80 157 1 0 1 0 0 2"
"7 241 82 158 1 0 1 0 0 2"
"7 242 82 159 1 0 1 0 0 2"
"7 243 82 160 1 0 1 0 0 2"
"7 244 82 161 1 0 1 0 0 2"
"7 245 83 161 1 0 1 0 0 2"
"7 246 83 162 1 0 1 0 0 2"
"7 248 84 163 1 0 1 0 0 2"
"7 250 85 164 1 0 1 0 0 2"
"7 251 85 165 1 0 1 0 0 2"
"7 252 86 165 1 0 1 0 0 2"
"7 253 86 166 1 0 1 0 0 2"
"7 254 87 166 1 0 1 0 0 2"
"7 255 87 167 1 0 1 0 0 2"
"7 256 88 167 1 0 1 0 0 2"
"7 257 88 168 1 0 1 0 0 2"
"7 258 88 169 1 0 1 0 0 2"
"7 259 89 169 1 0 1 0 0 2"
"7 260 89 170 1 0 1 0 0 2"
"7 261 90 170 1 0 1 0 0 2"
"7 262 90 171 1 0 1 0 0 2"
"7 232 153 78 1 0 1 0 0 2"
"7 235 155 79 1 0 1 0 0 2"
"7 236 155 80 1 0 1 0 0 2"
"7 237 155 81 1 0 1 0 0 2"
"7 238 156 81 1 0 1 0 0 2"
"7 239 157 81 1 0 1 0 0 2"
"7 241 158 82 1 0 1 0 0 2"
"7 242 158 83 1 0 1 0 0 2"
"7 243 159 83 1 0 1 0 0 2"
"7 245 160 84 1 0 1 0 0 2"
"7 246 161 84 1 0 1 0 0 2"
"7 247 161 85 1 0 1 0 0 2"
"7 249 163 85 1 0 1 0 0 2"
"7 251 164 86 1 0 1 0 0 2"
"7 252 164 87 1 0 1 0 0 2"
"7 254 165 88 1 0 1 0 0 2"
"7 255 166 88 1 0 1 0 0 2"
"7 256 167 88 1 0 1 0 0 2"
"7 257 167 89 1 0 1 0 0 2"
"7 258 168 89 1 0 1 0 0 2"
"7 259 168 90 1 0 1 0 0 2"
"7 260 169 90 1 0 1 0 0 2"
"7 261 170 90 1 0 1 0 0 2"
"7 262 170 91 1 0 1 0 0 2"
"7 263 171 91 1 0 1 0 0 2"
"7 264 171 92 1 0 1 0 0 2"
"7 265 172 92 1 0 1 0 0 2"
"7 266 173 92 1 0 1 0 0 2"
"7 267 173 93 1 0 1 0 0 2"
"7 268 174 93 1 0 1 0 0 2"
)

# SAT jobs
for line in "${jobs_SAT[@]}"; do
  read -r k n x y s c v a l b <<< "$line"
  for seed in $(seq 1 "$r"); do
    jobname="k${k}_n${n}_x${x}_y${y}_f${f}_b${b}_r${seed}"
    echo "Submitting SAT job $jobname (mem=$mem)"
    sbatch --job-name="$jobname" --mem-per-cpu="$mem" --time=72:00:00 run_bounds_individual.sh \
      -k "$k" -n "$n" -x "$x" -y "$y" \
      -s "$s" -c "$c" -v "$v" -a "$a" -l "$l" -b "$b" \
      -f "$f" -t 0 -r "$seed" -j "$j" -w "$w"
    sleep 1
  done
done

# UNSAT jobs
for line in "${jobs_UNSAT[@]}"; do
  read -r k n x y s c v a l b <<< "$line"
  for seed in $(seq 1 "$r"); do
    jobname="k${k}_n${n}_x${x}_y${y}_f${f}_b${b}_r${seed}"
    echo "Submitting UNSAT job $jobname (mem=$mem)"
    sbatch --job-name="$jobname" --mem-per-cpu="$mem" --time=72:00:00 run_bounds_individual.sh \
      -k "$k" -n "$n" -x "$x" -y "$y" \
      -s "$s" -c "$c" -v "$v" -a "$a" -l "$l" -b "$b" \
      -f "$f" -t 0 -r "$seed" -j "$j" -w "$w"
    sleep 1
  done
done