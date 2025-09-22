Requires
Cadical: https://github.com/arminbiere/cadical
Cardinality Cadical: https://github.com/jreeves3/Cardinality-CDCL

The script expects the directories:
solvers/Cardinality-CDCL-main/Tools/knf2cnf
solvers/Cardinality-CDCL-main/cardinality-cadical/build/cadical
solvers/cadical-master/build/cadical

run.sh usage:
e.g. for k=7, n=122, point (33, 88): "./run.sh -k 7 -n 122 -x 33 -y 88 -s 1 -c 0 -v 1 -a 0 -l -0 -b 0 -f 0 -t 0 -r 0 -e seqcounter"
Options:
  -k   k value
  -n   n value
  -x   point x
  -y   point y
  -s   (0,1) symmetry break (0=off, 1=on)
  -v   Vertical/horizontal binary clauses (0=off, 1=on)
  -a   antidiagonal constraints (0=off, 1=on)
  -l   line length for antidiagonal and v/h binary(0= one point, 5= six points)
  -c   Vertical/horizontal Cardinality constraints (0=off, 1=on)
  -b   boundary constraints (0=off, 1=unit, 2=unit+binary)
  -f   1=KNF (cardinality cadical), 0=CNF (cadical)
  -t   wall-clock timeout for SAT solver (s)
  -r   SAT solver seed
  -e   (Optional) CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer; omitted: use knf2cnf
  -h   help
  
main.py usage:
e.g. for k=7, n=122, point (33, 88): "python main.py -k 7 -n 122 -x 33 -y 88 -s 1 -c 0 -v 1 -a 0 -l -0 -b 0 -f 0 -t 0 -r 0 -e totalizer"
options:
  -h, --help  show this help message and exit
  -k K        number of collinear points to avoid
  -n N        n points; n-1 steps
  -x X        point x
  -y Y        point y
  -s S        symmetry break [0=off, 1=on]
  -c C        v/h cardinality constraints [0=off, 1=on]
  -v V        v/h line binary clauses [0=off, 1=on]
  -a A        antidiagonal cardinality constraints [0=off, 1=on]
  -l L        line length for vhline and antidiagonal. 0=1 point, 5=6 points
  -b B        boundary constraints [0=off, 1=unit clauses, 2=unit+binary clauses]
  -f F        0=CNF (cadical), 1=KNF (card. cadical)
  -t T        sat solver wall-clock timeout (s)
  -r R        SAT solver seed
  -e E        (Optional) CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer; omitted: use knf2cnf
  
Workflow Information:
1. run.sh executes main.py with the above arguments.

2. main.py applies optional (0,1) symmetry break, and calls
+ constraints_main.py:
  - defineVars():                      define point variables
  - stepConstraint():                  create step constraints            
  - cardinalityConstraint():           create KNF cardinality constraints, including vertical/horizontal constraints (optional)
+ constraints_reachability.py
  - BUP_EachPoint_VHLine():            vertical/horizontal binary constraints (optional)
  - BUP_EachPoint_NegDiagonalLine():   antidiagonal line constraints (optional)
+ constraints_symmetry.py (unused)
  - createLexEncoding                  create lexicographic constraints for breaking reflection and rotation+reflection symmetry

3. main.py then calls solveNormal() in solve_normal.py:
  - solveCNF():                        call knf2cnf() in globals.py, which uses knf2cnf or pysat_encode.py to encode the KNF cardinality constraints into CNF; then calls the SAT solver and grab SAT/UNSAT result.
  - solveKNF():                        call the SAT solver and grab SAT/UNSAT result.
  - extractModel():                    read SAT solver log, grab CPU time, reconstruct solution into point list
  - checkCollinearK() in globals.py:   check that no k-collinear lines exist in the solution.



