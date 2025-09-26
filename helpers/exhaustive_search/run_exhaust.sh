#!/usr/bin/env bash
set -euo pipefail

JOBS=12 # Max number of jobs to create at a time.
m=1
n=98
k=6

usage() {
cat << EOF
Usage: $0 -k <k> [-m minN] [-n maxN] [-j jobs]
  -k   k value (required)
  -m   min N (default 1)
  -n   max N (default 98)
  -j   max concurrent jobs (default 12)
Runs all points on the diagonal y = n - x - 1 for each n in [m..n].
EOF
}

opts=$(getopt -o "hk:m:n:j:" -- "$@") || { usage; exit 2; }
eval set -- "$opts"

while getopts "k:m:n:j:" opt; do
  case "$opt" in
    k) k="$OPTARG" ;;
    m) m="$OPTARG" ;;
    n) n="$OPTARG" ;;
    j) JOBS="$OPTARG" ;;
  esac
done

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

wait_for_slot() {
  while :; do
    running=$(jobs -pr | wc -l | awk '{print $1}')
    if [ "$running" -lt "$JOBS" ]; then break; fi
    sleep 0.2
  done
}

# Run each point as an individual job
run_point() {
  n_cur="$1"; x="$2"; y="$3"
  s=1; c=0; v=1; a=0; l=0; r=0; b=2; t=0; z=1
  run_id="$(date +%F_%H-%M-%S)"
  res_name="ex/k${k}_n${n}_$m{m}/res_k${k}_n${n_cur}_x${x}_y${y}_s${s}_c${c}_v${v}_a${a}_l${l}_b${b}_r${r}_${run_id}"
  python3 -u encode.py -k "$k" -n "$n_cur" -l "$l" -a "$a" -v "$v" -c "$c" -s "$s" -x "$x" -y "$y" -b "$b" -t "$t" -r "$r" -p "$res_name"
  python3 -u solve.py  -k "$k" -n "$n_cur" -x "$x" -y "$y" -t "$t" -r "$r" -p "$res_name" -z "$z"
  rm -f "output/$res_name/dimacsFile.knf" "output/$res_name/dimacsFile.cnf"
}

echo "Solving k=${k} diagonally from n=${m} to n=${n} with ${JOBS} jobs."

# Solve k diagonally from minN=m to maxN=n
for (( ni=m; ni<=n; ni++ )); do
  for (( x=0; x<=ni-1; x++ )); do
    y=$(( ni - x - 1 ))
    wait_for_slot
    run_point "$ni" "$x" "$y" &
    sleep 0.05
  done
done

wait
echo "Done."
