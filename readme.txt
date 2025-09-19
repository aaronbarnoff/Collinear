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
  -e   CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer
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
  -e E        CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer
  


