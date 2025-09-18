#!/usr/bin/env bash
#SBATCH --account=
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4G
set -euo pipefail

# CNF requires 8-12GB+ past k=7, n=220
# KNF can stay with 4GB for k=7 until very high n

usage() {
cat << EOF
Usage: $0 -k <k> -n <n> [options]

e.g. ./run.sh -k 7 -n 122 -x 33 -y 88 -s 1 -c 0 -v 1 -a 0 -l -0 -b 0 -f 0 -t 0 -r 0

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
  -h   help
EOF
}

options=$(getopt "hk:n:l:s:v:a:c:x:y:b:f:t:r:" "$@")
eval set -- "$options"

k= n= l= s= v= a= c= x= y= b= f= t= r=

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
    --) shift; break ;;
    *)  echo "Bad option"; usage; exit 2 ;;
  esac
done

cwd="$(pwd)"
dir_src="$cwd/src"
cd "$dir_src"

python3 -u main.py \
  -k "${k}" \
  -n "${n}" \
  -l "${l:-}" \
  -a "${a:-}" \
  -v "${v:-}" \
  -c "${c:-}" \
  -s "${s:-}" \
  -x "${x:-}" \
  -y "${y:-}" \
  -b "${b:-}" \
  -t "${t:-}" \
  -f "${f:-}" \
  -r "${r:-}"

echo "Done."
