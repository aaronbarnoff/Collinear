run ./compile-tools.sh to build the required repositories

Repos Used:
  Cadical: https://github.com/arminbiere/cadical
  Cardinality Cadical: https://github.com/jreeves3/Cardinality-CDCL
  Cadical Exhaust: https://github.com/curtisbright/cadical-exhaust

The script expects the directories:
  solvers/Cardinality-CDCL/Tools/knf2cnf (and pysat_encode.py)
  solvers/Cardinality-CDCL/cardinality-cadical/build/cadical
  solvers/cadical/build/cadical
  solvers/cadical-exhaust/build/cadical-exhaust

run.sh usage:
  Usage: ./run.sh -k <k> -n <n> [options]
  e.g. ./run.sh -k 7 -n 122 -x 33 -y 88 -f 1

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
    -e   (optional) CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer; (default: omitted, uses knf2cnf (seq counter))
    -z   0=regular solve (cadical), 1=exhaustive search (cadical-exhaust) (default 0)
    -j   line heuristic threshold value (default 0)
    -w   (KNF) 0=use pure CCDCL, 1=use hybrid mode (default 0)
    -q   flip direction (subsequence orientation: 0=subsequence off (default), 1=regular orientation, 2=flipped about y=x)
    -g   trim amount (remove x points from both ends (default 0))
    -m   read in FAs from file Collinear/fixed_assignments/fixed_assignments_n<n>_x<x>_y<y>_f<f>_j<j>.txt (default:1, on)
    -h   help
    -p   p=1: create encoding only, don't solve (default 0)
  
run.sh workflow:
1. run.sh executes encode.py and solve.py with the given arguments
2. encode.py generates the KNF encoding, and converts it to CNF if required (using knf2cnf or pysat_encode.py)
3. solve.py runs the desired SAT solver (cadical, cardinality-cadical, cadical-exhaust)
4. solve.py then verifies the solution is correct (except for cadical-exhaust).
5. can optionally use print_solution.py with the satOutput.log to verify individual solutions and plot them. 


