#!/usr/bin/env bash
#SBATCH --account=def-cbright
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=12G
set -euo pipefail

# CNF requires 8-12GB+ past k=7, n=220
# KNF can stay with 4GB for k=7 until very high n

usage() {
cat << EOF
Usage: $0 -k <k> -n <n> [options]

e.g. ./run.sh -k 7 -n 122 -x 33 -y 88 -s 1 -c 0 -v 1 -a 0 -l -0 -b 0 -f 0 -t 0 -r 0 -e seqcounter -z 0

Options:
  -k   k value
  -n   n value 
  -x   point x (default 0)
  -y   point y (default 0)
  -s   (0,1) symmetry break (0=off, 1=on) (default 1)
  -v   Vertical/horizontal binary clauses (0=off, 1=on) (default 1)
  -a   antidiagonal constraints (0=off, 1=on) (default 0)
  -l   line length for antidiagonal and v/h binary constraints (0= one point, 5= six points) (default 0)
  -c   Vertical/horizontal Cardinality constraints (0=off, 1=on) (default 0)
  -b   boundary constraints (0=off, 1=unit, 2=unit+binary) (default 2)
  -f   0=CNF (cadical), 1=KNF (cardinality cadical) (default 1)
  -t   wall-clock timeout for SAT solver (s) (default 0, no limit)
  -r   SAT solver seed (default 0)
  -e   (optional) CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer; (default: knf2cnf (seqcounter))
  -z   0=regular solve (cadical), 1=exhaustive search (cadical-exhaust) (default 0)
  -u   cardinality constraints heuristics. 0=no heuristic, 1=old heuristic, 4=line-filter (default 0)
  -j   line heuristic threshold value (default 0)
  -h   help
EOF
}

options=$(getopt "hk:n:l:s:v:a:c:x:y:b:f:t:r:e:z:u:j:" "$@")
eval set -- "$options"

k= n= l= s= v= a= c= x= y= b= f= t= r= e= z= u= j=

while true; do
  case "$1" in
    -h) usage; exit 0 ;;
    -k) k="$2"; shift 2 ;;
    -n) n="$2"; shift 2 ;;
    -l) l="$2"; shift 2 ;;
    -s) s="$2"; shift 2 ;;
    -v) v="$2"; shift 2 ;;
    -a) a="$2"; shift 2 ;;
    -c) c="$2"; shift 2 ;;
    -x) x="$2"; shift 2 ;;
    -y) y="$2"; shift 2 ;;
    -b) b="$2"; shift 2 ;;
    -f) f="$2"; shift 2 ;;
    -t) t="$2"; shift 2 ;;
    -r) r="$2"; shift 2 ;;
    -e) e="$2"; shift 2 ;;
    -z) z="$2"; shift 2 ;;
    -u) u="$2"; shift 2 ;;
    -j) j="$2"; shift 2 ;;
    --) shift; break ;;
    *)  echo "Bad option"; usage; exit 2 ;;
  esac
done

run_id="$(date +%F_%H-%M-%S)"
: "${x:=0}" "${y:=0}" "${s:=1}" "${c:=0}" "${v:=1}" "${a:=0}" "${l:=0}" "${b:=2}" "${f:=1}" "${t:=0}" "${r:=0}" "${z:=0}" "${u:=0}" "${j:=0}"

# required for pysat and encoding types
if [[ -n "${e:-}" ]]; then
  if [[ $(hostname) == *".fir.alliancecan.ca" || -n "${CC_CLUSTER:-}" ]]; then
    module load python/3.11
    virtualenv --no-download "$SLURM_TMPDIR/env"
    source "$SLURM_TMPDIR/env/bin/activate"
    pip install "python-sat[pblib,aiger]"
  fi
fi

while :; do
run_id="$(date +%F_%H-%M-%S)"
if ((z==0)) 
then
  res_name="j${j}/res_k${k}_n${n}_x${x}_y${y}_s${s}_c${c}_v${v}_a${a}_l${l}_b${b}_f${f}_r${r}_e${e:-none}_${run_id}"
else
  mkdir -p "$PWD/output/ex" 
  res_name="ex/res_k${k}_n${n}_x${x}_y${y}_s${s}_c${c}_v${v}_a${a}_l${l}_b${b}_f${f}_r${r}_e${e:-none}_${run_id}"
fi

  log="$PWD/output/$res_name/logOutput.log"

  python3 -u encode.py -k "$k" -n "$n" -l "$l" -a "$a" -v "$v" -c "$c" -s "$s" -x "$x" -y "$y" -b "$b" -t "$t" -f "$f" -r "$r" -p "$res_name" ${e:+-e "$e"} -j "$j"
  python3 -u solve.py  -k "$k" -n "$n" -x "$x" -y "$y" -t "$t" -f "$f" -r "$r" -p "$res_name" ${e:+-e "$e"} -z "$z"

  # make sure log has time to write
    #for _ in {1..50}; do
    #[ -s "$log" ] && break
    #sleep 0.1
    #done
    sleep 1

  if grep -q "Failure" "$log"; then
      j=$(( j >= 2 ? j - 2 : 0 ))
  else
    break
  fi
done
