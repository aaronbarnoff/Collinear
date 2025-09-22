#!/usr/bin/env bash
#SBATCH --account=def-cbright
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4G
set -euo pipefail

# required for pysat
if [[ $(hostname) == *".fir.alliancecan.ca" || -n "${CC_CLUSTER:-}" ]]; then
    module load python/3.11
    virtualenv --no-download "$SLURM_TMPDIR/env"
    source "$SLURM_TMPDIR/env/bin/activate"
    #pip install --upgrade pip
    pip install "python-sat[pblib,aiger]"
fi

# CNF requires 8-12GB+ past k=7, n=220
# KNF can stay with 4GB for k=7 until very high n

usage() {
cat << EOF
Usage: $0 -k <k> -n <n> [options]

e.g. ./run.sh -k 7 -n 122 -x 33 -y 88 -s 1 -c 0 -v 1 -a 0 -l -0 -b 0 -f 0 -t 0 -r 0 -e seqcounter

Options:
  -k   k value
  -n   n value
  -x   point x
  -y   point y
  -s   (0,1) symmetry break (0=off, 1=on)
  -v   Vertical/horizontal binary clauses (0=off, 1=on)
  -a   antidiagonal constraints (0=off, 1=on)
  -l   line length for antidiagonal and v/h binary constraints (0= one point, 5= six points)
  -c   Vertical/horizontal Cardinality constraints (0=off, 1=on)
  -b   boundary constraints (0=off, 1=unit, 2=unit+binary)
  -f   1=KNF (cardinality cadical), 0=CNF (cadical)
  -t   wall-clock timeout for SAT solver (s)
  -r   SAT solver seed
  -e   (Optional) CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer
  -h   help
EOF
}

options=$(getopt "hk:n:l:s:v:a:c:x:y:b:f:t:r:e:" "$@")
eval set -- "$options"

k= n= l= s= v= a= c= x= y= b= f= t= r= e=

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
    --) shift; break ;;
    *)  echo "Bad option"; usage; exit 2 ;;
  esac
done

run_id="$(date +%F_%H-%M-%S)"
: "${x:=0}" "${y:=0}" "${s:=1}" "${c:=0}" "${v:=1}" "${a:=0}" "${l:=0}" "${b:=0}" "${f:=0}" "${t:=0}" "${r:=0}"
res_name="res_k${k}_n${n}_x${x}_y${y}_s${s}_c${c}_v${v}_a${a}_l${l}_b${b}_f${f}_r${r}_e${e:-none}_${run_id}"

#cwd="$(pwd)"
#dir_src="$cwd/src"
#cd "$dir_src"

python3 -u encode.py -k "$k" -n "$n" -l "$l" -a "$a" -v "$v" -c "$c" -s "$s" -x "$x" -y "$y" -b "$b" -t "$t" -f "$f" -r "$r" -p "$res_name" ${e:+-e "$e"}
python3 -u solve.py  -k "$k" -n "$n" -x "$x" -y "$y" -t "$t" -f "$f" -r "$r" -p "$res_name" ${e:+-e "$e"}

echo "Done."
#build the solvers, then
#find . -type f -print0 | while IFS= read -r -d '' f; do if file -b "$f" | grep -qE 'executable|script text'; then chmod +x "$f"; fi; done