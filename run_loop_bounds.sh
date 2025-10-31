#!/usr/bin/env bash
set -uo pipefail

###### Points to run ######
# Upper bound points to verify (single-point solve):
# n=261(89,171) - (UNSAT): ./run_loop_bounds.sh -x 89 -y 171 -b 0

# Lower bound points to verify (single-point solve):
# n=259(169,89) - (UNSAT): ./run_loop_bounds.sh -x 169 -y 89 -b 1
# n=264(172,91) - (UNSAT): ./run_loop_bounds.sh -x 172 -y 91 -b 1
# n=267(174,92) - (UNSAT): ./run_loop_bounds.sh -x 174 -y 92 -b 1

# Next unsolved upper bound point to start at (loop to next point): 
# n=263(90,172): ./run_loop_bounds.sh -x 90 -y 172 -b 0 -r 1

# Next unsolved lower bound point to start at (loop to next point): 
# n=269(175,93): ./run_loop_bounds.sh -x 175 -y 93 -b 1 -r 1

# Midline points to start at (loop on SAT, exit on UNSAT): 
# n=270(134,135): ./run_loop_bounds.sh -x 134 -y 135 -b 2 -r 1


usage() {
cat << EOF
Usage: $0 [options]

Example: ./run_loop_bounds.sh -x 0 -y 0 -b 0
Hardcoded: (-s) symBreak=1, (-v) V/HBinaryClauses=1, (-j) line-filter (k+j) heuristic j=0 off, (-r) seed=0, (-b) unit+binary clauses=2, (-c) V/HCard.=0, (-a) antidiagonal=0
Options:
  -x   point x (default 0)
  -y   point y (default 0)
  -f   0=CNF (cadical), 1=KNF (cardinality cadical) (default 0)
  -b   0=Upper bounds, 1=Lower bounds, 2=Midline (default 0)
  -r   0= no loop, 1= solve next point
  -m   read in FAs from 'fixed_assignments.txt' in main folder as unit clauses
  -h   help
EOF
}

if ! options=$(getopt -o hx:y:f:b:r:m: -- "$@"); then
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

while true; do
  case "$1" in
    -h) usage; exit 0 ;;
    -x) x="$2"; shift 2 ;;
    -y) y="$2"; shift 2 ;;
    -f) f="$2"; shift 2 ;;
    -b) b="$2"; shift 2 ;;
    -r) r="$2"; shift 2 ;;    
    -m) m="$2"; shift 2 ;;  
    --) shift; break ;;
    *)  echo "Bad option"; usage; exit 2 ;;
  esac
done

case "$x" in -|*[^0-9]*|"") echo "x must be a non-negative integer"; exit 2 ;; esac
case "$y" in -|*[^0-9]*|"") echo "y must be a non-negative integer"; exit 2 ;; esac
case "$f" in 0|1) ;; *) echo "f (CNF/KNF) must be 0 or 1"; exit 2 ;; esac
case "$b" in 0|1|2) ;; *) echo "b (upper/lower/midline) must be 0, 1, or 2"; exit 2 ;; esac
case "$r" in 0|1) ;; *) echo "r (no loop/loop) must be 0 or 1"; exit 2 ;; esac
case "$m" in 0|1) ;; *) echo "m must be 0 or 1"; exit 2 ;; esac

if (( f == 0 )); then
  solve_type="CNF"
else
  solve_type="KNF"
fi
 
if (( b == 0 )); then
  bounds="upper"
elif (( b == 1 )); then
  bounds="lower"
else
  bounds="midline"
fi

if (( r == 0)); then
loop="no loop"
else
loop="looping"
fi 

run_id="$(date +%F_%H-%M-%S)"
log_file="log_${run_id}.txt" 
exec > >(tee -a "$log_file") 2>&1

echo "Logging to $log_file"
echo "Started: $(date)"
echo "Initial parameters: x=$x y=$y f=$f b=$b ($bounds, $solve_type, $loop)"
echo

while :; do
  n=$(( x + y + 1 ))
    if ((x < 0 || y < 0)); then
    echo "out of bounds"
      break
    fi

    res_name="${bounds}_x${x}_y${y}_${solve_type}_${run_id}"
    echo "Solving for ${bounds} bounds, point n=${n}:(${x},${y})"

    python3 -u encode.py -k 7 -n "$n" -x "$x" -y "$y" -l 0 -a 0 -v 1 -c 0 -s 1 -b 2 -t 0 -f "$f" -r 0 -p "$res_name" -j 0 -w 0 --trim 0 --flip 0 --FA "$m"

    python3 -u solve.py  -k 7 -n "$n" -x "$x" -y "$y" -t 0 -f "$f" -r 0 -p "$res_name" -z 0 -w 0
    res=$?
    rm -f "output/$res_name/dimacsFile.knf" "output/$res_name/dimacsFile.cnf"
    
    if (( b == 0 )); then
        # Upper bounds loop
        if (( res == 20 )); then
            echo "UNSAT: ${bounds} n=${n}:(${x},${y}) ${solve_type}"
            (( x+=1 ))
            (( y-=1 ))
        elif (( res == 10 )); then
            echo "SAT:   ${bounds} n=${n}:(${x},${y}) ${solve_type}"
            (( y+=1 ))
        else
            echo "UNKNOWN: ${bounds} n=${n}:(${x},${y}) ${solve_type}"
            break
        fi
    elif (( b == 1 )); then
        # Lower bounds loop
        if (( res == 20 )); then
            echo "UNSAT: ${bounds} n=${n}:(${x},${y}) ${solve_type}"
            (( x-=1 ))
            (( y+=1 ))
        elif (( res == 10 )); then
            echo "SAT:   ${bounds} n=${n}:(${x},${y}) ${solve_type}"
            (( x+=1 ))
        else
            echo "UNKNOWN: ${bounds} n=${n}:(${x},${y}) ${solve_type}"
            break
        fi
    else
        # Midline loop
        if (( res == 20 )); then
            echo "UNSAT: ${bounds} n=${n}:(${x},${y}) ${solve_type}"
            break
        elif (( res == 10 )); then
            echo "SAT:   ${bounds} n=${n}:(${x},${y}) ${solve_type}"
            (( x+=1 ))
            (( y+=1 ))
        else
            echo "UNKNOWN: ${bounds} n=${n}:(${x},${y}) ${solve_type}"
            break
        fi
    fi
    if (( r == 0)); then
    break
    fi
  echo
done

echo
echo "Done at $(date)"
echo "Full log saved to: $log_file"
