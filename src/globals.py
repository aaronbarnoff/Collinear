import time
import os
import subprocess
from datetime import datetime
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="e.g. for k=7, n=122, point (33, 88): python main.py -k 7 -n 122 -x 33 -y 88 -s 1 -c 0 -v 1 -a 0 -l -0 -b 0 -f 0 -t 0 -r 0")
    parser.add_argument("-k", default=5, help="number of collinear points to avoid")
    parser.add_argument("-n", default=28, help="n points; n-1 steps")
    
    parser.add_argument("-x", default=0, help="point x")
    parser.add_argument("-y", default=0, help="point y")

    parser.add_argument("-s", default=1, help="symmetry break [0=off, 1=on]")
    parser.add_argument("-c", default=0, help="v/h cardinality constraints [0=off, 1=on]")
    parser.add_argument("-v", default=1, help="v/h line binary clauses [0=off, 1=on]")
    parser.add_argument("-a", default=0, help="antidiagonal constraints [0=off, 1=on]")

    parser.add_argument("-l", default=0, help="cutoff for v/h line and antidiagonal. 0=1 point, 5=6 points")

    parser.add_argument("-b", default=0, help="boundary constraints [0=off, 1=unit clauses, 2=unit+binary clauses]") # at one point this was used as float value, haven't changed
    parser.add_argument("-f", default=0, help="0=CNF (cadical), 1=KNF (card. cadical)")
    parser.add_argument("-t", default=0, help="sat solver wall-clock timeout (s)")

    parser.add_argument("-e", default=None, help="CNF cardinality encoding type: seqcounter, totalizer, sortnetwrk, cardnetwrk, mtotalizer, kmtotalizer")

    parser.add_argument("-r", default=0, help="SAT solver seed")
    
    return vars(parser.parse_args())

class Globals:
    def __init__(self):
        args = parse_arguments()
        self.k=int(args["k"])
        self.n=int(args["n"])

        self.cutoff=int(args["l"])
        self.vh_card=int(args["c"])
        self.vh_line=int(args["v"])
        self.antidiag=int(args["a"])

        self.px=int(args["x"])
        self.py=int(args["y"])
        self.sym_break=int(args["s"])
        self.boundary_type=float(args["b"])
        self.use_KNF=int(args["f"])

        self.cnf_encoding=(args["e"])

        self.solver_timeout=int(args["t"])
        self.solver_seed=int(args["r"])
        
        #if self.cnfEncodingType is not None and self.useKNF:
        #    print("Must use CNF solver with encoding type.")
        #    exit(-1)

        self.solve_point = False
        if self.px >0 and self.py > 0:
            if self.px + self.py >= self.n:
                print("Invalid final point to solve for.")
                exit(-1)
            else:
                self.solve_point = True    

        if self.vh_line == 0 and self.vh_card == 0:
            print("Vertical/horizontal constraints required.")
            exit(-1)

        self.run_ID = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.cwd=os.getcwd()

        self.v = [[0 for _ in range(self.n)] for _ in range(self.n)]
        self.point_list = []
        self.collinear_list = []
        self.dimacs_buffer = []
        self.num_solutions = 0
        self.num_vars = 0
        self.var_cnt = 0
        self.num_clauses = 0
        self.debug = 0
        self.num_card_clauses = 0

        self.sat_time_wc = 0
        self.start_time = 0
        self.end_time = 0

        self.cwd_path = os.path.dirname(os.getcwd())
        self.output_path = os.path.join(self.cwd_path, 'output')
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        self.result_path = os.path.join(self.output_path, f'res_k{self.k}_n{self.n}_x{self.px}_y{self.py}_s{self.sym_break}_c{self.vh_card}_v{self.vh_line}_a{self.antidiag}_l{self.cutoff}_b{self.boundary_type}_f{self.use_KNF}_r{self.solver_seed}_e{self.cnf_encoding}_{self.run_ID}')
        
        #print(self.outputPath)
        if not os.path.exists(self.result_path):
            os.makedirs(self.result_path)

        self.knf_dimacs_filename = f'dimacsFile.knf'
        self.knf_dimacs_filepath = f'{self.result_path}/{self.knf_dimacs_filename}'

        self.cnf_dimacs_filename = f'dimacsFile.cnf'
        self.cnf_dimacs_filepath = f'{self.result_path}/{self.cnf_dimacs_filename}'

        self.sat_log_filename = f'satOutput.log'
        self.sat_log_filepath = f'{self.result_path}/{self.sat_log_filename}'
        self.sat_logfile = None

        self.out_log_filename = f'logOutput.log'
        self.out_log_filepath = f'{self.result_path}/{self.out_log_filename}'
        #self.logFile2 = None
        self.out_log_file = open(f'{self.out_log_filepath}', 'w+', buffering=1)

        self.pysat_encode_path= f'{self.cwd_path}/solvers/Cardinality-CDCL-main/Tools/pysat_encode.py'
        self.knf2cnf_path = f'{self.cwd_path}/solvers/Cardinality-CDCL-main/Tools/knf2cnf'
        self.CCDCL_path = f'{self.cwd_path}/solvers/Cardinality-CDCL-main/cardinality-cadical/build/cadical'
        self.CDCL_path = f'{self.cwd_path}/solvers/cadical-master/build/cadical'

g = Globals()

def verify_solution(point_list):
    print("Confirming Results:", time.time() - g.start_time, "seconds")
    for (x1, y1) in point_list:
        for (x2, y2) in point_list:
            if (x1, y1) == (x2, y2):
                continue
            if (x2 < x1) or (y2 < y1):
                continue
            m_p = x2-x1
            m_q = y2-y1
            tmp_point_list = []
            count = 2
            tmp_point_list.append((x1,y1))
            tmp_point_list.append((x2,y2))

            #print(f'({x1},{y1}), ({x2}, {y2}); slope: {m_p}/{m_q} = {m_p/m_q}')
            x = x2
            y = y2
            while (x < g.n) and (y < g.n - x):
                x += m_p
                y += m_q
                if (x, y) in point_list:
                    count += 1
                    tmp_point_list.append((x, y))
            if count >= g.k:
                # print(tmpPointsList)
                g.collinear_list.append(tmp_point_list)    

    if g.collinear_list:
        print(f"Failure: {g.k} or more points found on the same line.")
        for line in g.collinear_list:
            (x1, y1)= line[0]
            (x2, y2)= line[1]
            if (x2 - x1) == 0:
                print('vline. points: ', end="")
            elif (y2 - y1) == 0:
                print('hline. points: ', end="")
            else:
                print(f'slope: {((y2 - y1) / (x2 - x1)):.2g}; m_p: {(y2-y1)}, m_q: {(x2-x1)}; points: ',end="")
            for points in line:
                (x, y)=points
                print(f'({x},{y}) ', end="")
            print("")

def knf2cnf():
    print("Converting to CNF file:", time.time() - g.start_time, "seconds")

    cnf_output_file = open(g.cnf_dimacs_filepath, 'w+')

    if g.cnf_encoding is None:
        command = f'\'{g.knf2cnf_path}\' \'{g.knf_dimacs_filepath}\''
        result = subprocess.Popen(command, shell=True, stdout=cnf_output_file, stderr=subprocess.PIPE, text=True)
        result.wait()
    else:
        command = ["python3", g.pysat_encode_path, "-k", g.knf_dimacs_filepath, "-c", g.cnf_dimacs_filepath, "-e", g.cnf_encoding] # requires python-sat module
        #print(command)
        result = subprocess.Popen(command, stdout=g.out_log_file, stderr=subprocess.STDOUT)
        result.wait()


    cnf_output_file.close()
    time.sleep(1) # Seems to cause problems without