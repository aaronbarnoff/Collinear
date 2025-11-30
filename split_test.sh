#!/usr/bin/env bash
set -uo pipefail

usage() {
cat << EOF
Usage: $0 [options]

Example: ./split_test.sh -n 100 -x 49 -y 50 -f 1
Options:
  -n   num points in path
  -x   final point x (default 0)
  -y   final point y (default 0)
  -f   0=CNF (cadical), 1=KNF (cardinality cadical) (default 0)
  -t   sbatch wall clock timeout in hours
  -h   help
EOF
}

if ! options=$(getopt -o hx:y:f:n:s:t: -- "$@"); then
  usage
  exit 2
fi
eval set -- "$options"

x=0
y=0
f=0
b=0
r=0
m=0
j=10
s=0
t=0

while true; do
  case "$1" in
    -h) usage; exit 0 ;;
    -n) n="$2"; shift 2 ;;
    -x) x="$2"; shift 2 ;;
    -y) y="$2"; shift 2 ;;
    -f) f="$2"; shift 2 ;;
    -t) t="$2"; shift 2 ;;
    --) shift; break ;;
    *)  echo "Bad option"; usage; exit 2 ;;
  esac
done

case "$n" in *[^0-9]*|"") echo "n must be a non-negative integer"; exit 2 ;; esac
case "$x" in *[^0-9]*|"") echo "x must be a non-negative integer"; exit 2 ;; esac
case "$y" in *[^0-9]*|"") echo "y must be a non-negative integer"; exit 2 ;; esac
case "$t" in *[^0-9]*|"") echo "t must be a non-negative integer"; exit 2 ;; esac
case "$f" in 0|1) ;; *) echo "f (CNF/KNF) must be 0 or 1"; exit 2 ;; esac

run_id="$(date +%F_%H-%M-%S)"
dir="$PWD/output/res_k7_n${n}_x${x}_y${y}_b2_f${f}_r0_j10_w0_z0_g0_q0_${run_id}"

echo "Generating dimacs file for n${n}_x${x}_y${y}_f${f}_${run_id}"
./run.sh -k 7 -n $n -x $x -y $y -f $f -j 10 -p 1 -m 0 
sleep 1

s=$((f+1))
echo "Generating cubes."
python3 generate_cubes_diag_2.py -s "$s" -n "$n" -fx "$x" -fy "$y" -o cubes.icnf -f "res_k7_n${n}_x${x}_y${y}_b2_f${f}_r0_j10_w0_z0_g0_q0_${run_id}"
sleep 1

cnt=$(grep -c '^a ' "$dir/cubes.icnf")

if (( cnt == 0 )); then
    echo "No cube lines found in $dir/cubes.icnf"
    exit 1
fi
last=$((cnt - 1))

mkdir "$dir/slurm_logs"

echo "Scheduling cubes with timeout: ${t} hours, 12G ram"
echo sbatch --array=0-$last --mem-per-cpu=12G --time="${t}:00:00" --output="$dir/slurm_logs/k7_n${n}_x${x}_y${y}_f${f}_%A_%a.out" \
    run_cubes_split.sh -k 7 -n "$n" -s "$s" \
    -f "res_k7_n${n}_x${x}_y${y}_b2_f${f}_r0_j10_w0_z0_g0_q0_${run_id}" 
sbatch --array=0-$last --mem-per-cpu=12G --time="${t}:00:00" --output="$dir/slurm_logs/k7_n${n}_x${x}_y${y}_f${f}_%A_%a.out" \
    run_cubes_split.sh -k 7 -n "$n" -s "$s" \
    -f "res_k7_n${n}_x${x}_y${y}_b2_f${f}_r0_j10_w0_z0_g0_q0_${run_id}"

echo "Done"