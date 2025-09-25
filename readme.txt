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
    -f   0=CNF (cadical), 1=KNF (cardinality cadical)
    -t   wall-clock timeout for SAT solver (s)
    -r   SAT solver seed
    -e   (Optional) CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer
    -z   0=regular solve (cadical), 1=exhaustive search (cadical-exhaust)
    -h   help
  
encode.py usage:
  usage: encode.py [-h] [-k K] [-n N] [-x X] [-y Y] [-s S] [-c C] [-v V] [-a A] [-l L] [-b B] [-f F] [-t T] [-e E]
                  [-r R] [-o O] [-p P]
  e. for k=7, n=122, point (33, 88): python3 encode.py -k 7 -n 122 -x 33 -y 88 -s 1 -c 0 -v 1 -a 0 -l -0 -b 0 -f 0 -t 0 -r 0

  options:
    -h, --help  show this help message and exit
    -k K        number of collinear points to avoid
    -n N        n points; n-1 steps
    -x X        point x
    -y Y        point y
    -s S        symmetry break [0=off, 1=on]
    -c C        v/h cardinality constraints [0=off, 1=on]
    -v V        v/h line binary clauses [0=off, 1=on]
    -a A        antidiagonal constraints [0=off, 1=on]
    -l L        cutoff length for v/h line and antidiagonal. 0=1 point, 5=6 points
    -b B        boundary constraints [0=off, 1=unit clauses, 2=unit+binary clauses]
    -f F        0=CNF (cadical), 1=KNF (card. cadical)
    -t T        sat solver wall-clock timeout (s)
    -e E        CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer
    -r R        SAT solver seed
    -o O        Use lexicographic symmetry breaking constraints
    -p P        results folder name (used by run.sh)

solve.py usage:
  usage: solve.py [-h] [-k K] [-n N] [-x X] [-y Y] [-f F] [-e E] [-t T] [-r R] [-p P] [-z Z]

  options:
    -h, --help  show this help message and exit
    -k K        number of collinear points to avoid
    -n N        n points; n-1 steps
    -x X        point x
    -y Y        point y
    -f F        0=CNF (cadical), 1=KNF (card. cadical)
    -e E        CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer
    -t T        sat solver wall-clock timeout (s)
    -r R        SAT solver seed
    -p P        results folder name
    -z Z        0=regular solve, 1=exhaustive (cadical-exhaust)

run.sh workflow:
1. run.sh executes encode.py and solve.py with the given arguments
2. encode.py generates the KNF encoding, and converts it to CNF if required (using knf2cnf or pysat_encode.py)
3. solve.py runs the desired SAT solver (cadical, cardinality-cadical, cadical-exhaust)
4. solve.py then verifies the solution is correct (except for cadical-exhaust).
5. can optionally use print_solution.py with the satOutput.log to verify individual solutions and plot them. 

run_bounds.sh workflow:
1. run_bounds.sh executes the same workflow as run.sh, except over all boundary points (currently configured for up to n=180), and without cadical-exhaust.

run_exhaust.sh workflow:
1. run_exhaust.sh uses cadical-exhaust to solve all points on the grid given by minN=m and maxN=n; can specify number of cores to use with -j.
2. solutions are not verified due to the overhead.
3. cadical-exhaust is configured to only block point variables when searching for new solutions.